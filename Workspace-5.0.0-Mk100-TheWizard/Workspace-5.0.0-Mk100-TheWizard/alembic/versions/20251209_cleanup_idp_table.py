"""cleanup_idp_table

Revision ID: b22002200220
Revises: a11001100110
Create Date: 2025-12-09 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b22002200220'
down_revision: Union[str, Sequence[str], None] = 'a11001100110'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the local idp_users table as we are using Keycloak
    op.drop_index(op.f('ix_idp_users_email'), table_name='idp_users')
    op.drop_index(op.f('ix_idp_users_subject_id'), table_name='idp_users')
    op.drop_table('idp_users')


def downgrade() -> None:
    # Recreate idp_users (Restoring previous state)
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
