"""identity_split

Revision ID: a11001100110
Revises: eb7f240665a0
Create Date: 2025-12-09 03:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a11001100110'
down_revision: Union[str, Sequence[str], None] = 'eb7f240665a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create idp_users table (Sovereign Identity Boundary)
    op.create_table(
        'idp_users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_idp_users_subject_id'), 'idp_users', ['subject_id'], unique=True)
    op.create_index(op.f('ix_idp_users_email'), 'idp_users', ['email'], unique=True)

    # 2. Add Identity Columns to governance_users
    op.add_column('governance_users', sa.Column('subject_id', sa.String(), nullable=True))
    op.add_column('governance_users', sa.Column('issuer', sa.String(), nullable=True))
    
    # 3. Data Migration (Best Effort)
    # We populate idp_users from existing governance_users
    # And link them up.
    connection = op.get_bind()
    
    # Check if we have users
    users = connection.execute(sa.text("SELECT id, name, email FROM governance_users")).fetchall()
    
    for u in users:
        uid = u.id
        name = u.name
        email = u.email
        # Generate stable subject_id
        # In real world, this comes from IdP. Here we are "Bootstrapping the IdP" from existing users.
        sub = f"sub_{uid}" 
        iss = "https://jarvis.sovereign.idp"
        
        # Insert into idp_users
        connection.execute(sa.text(
            "INSERT INTO idp_users (id, subject_id, email, name, created_at) "
            "VALUES (:id, :sub, :email, :name, NOW())"
        ), {"id": uid, "sub": sub, "email": email, "name": name})
        
        # Update governance_users
        connection.execute(sa.text(
            "UPDATE governance_users SET subject_id = :sub, issuer = :iss WHERE id = :id"
        ), {"sub": sub, "iss": iss, "id": uid})

    # 4. Enforce constraints
    # Now that data is populated, we can set nullable=False (if we had specific control, 
    # but alter_column is tricky with existing nulls if logic failed. We assume success).
    op.alter_column('governance_users', 'subject_id', nullable=False)
    # Issuer default
    op.alter_column('governance_users', 'issuer', server_default="https://jarvis.sovereign.idp", nullable=False)
    
    # 5. Drop PII from governance_users
    # op.drop_column('governance_users', 'email') 
    # COMMENTED OUT: We are keeping email temporarily for 9-1/Dashboard backward compatibility 
    # until the codebase is visibly updated to use the new join. 
    # Ideally we drop it NOW, but that breaks running code immediately.
    # User instruction 11-1 says "Schema Migration (Drop PII columns)".
    # But if I drop it now, I break the app before I fix the code.
    # I should drop it. The "Mock IdP" task is first.
    # The Task 2 is "Database Refactor".
    # I will DROP IT to force the refactor. "Break then Fix".
    op.drop_column('governance_users', 'email')
    
    # Create indexes for lookups
    op.create_index(op.f('ix_governance_users_subject_id'), 'governance_users', ['subject_id', 'issuer'], unique=True)


def downgrade() -> None:
    # Reverse order
    op.add_column('governance_users', sa.Column('email', sa.VARCHAR(), nullable=True))
    
    # Restore email (Lossy if modified in IdP, but we do best effort join)
    connection = op.get_bind()
    connection.execute(sa.text(
        "UPDATE governance_users SET email = idp_users.email "
        "FROM idp_users WHERE governance_users.id = idp_users.id"
    ))
    
    op.drop_index(op.f('ix_governance_users_subject_id'), table_name='governance_users')
    op.drop_column('governance_users', 'issuer')
    op.drop_column('governance_users', 'subject_id')
    op.drop_table('idp_users')
