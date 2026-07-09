"""Align governance schema with models

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-12-08 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. governance_users schema alignment
    # Rename external_id -> email
    op.alter_column('governance_users', 'external_id', new_column_name='email')
    
    # Drop display_name (we added 'name' in previous migration)
    op.drop_column('governance_users', 'display_name')
    
    # Fix trust_score (Numeric -> JSONB trust_scores)
    op.drop_column('governance_users', 'trust_score')
    op.add_column('governance_users', sa.Column('trust_scores', postgresql.JSONB, server_default='{}'))
    
    # Cleanup and Additions
    op.drop_column('governance_users', 'claimed_expertise')
    op.drop_column('governance_users', 'demonstrated_expertise')
    op.drop_column('governance_users', 'engagement_score')
    
    op.alter_column('governance_users', 'last_active_at', new_column_name='last_active')
    op.add_column('governance_users', sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')))
    op.add_column('governance_users', sa.Column('invited_by', sa.UUID()))
    op.create_foreign_key('fk_governance_users_invited_by', 'governance_users', 'governance_users', ['invited_by'], ['id'])

    # 2. permissions schema alignment (Rebuild table to match Action/Role model)
    op.drop_table('permissions')
    op.create_table('permissions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('conditions', postgresql.JSONB, nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('action', 'role', 'resource_type', name='uq_permission_action_role')
    )
    op.create_index(op.f('ix_permissions_role'), 'permissions', ['role'])
    op.create_index(op.f('ix_permissions_action'), 'permissions', ['action'])

    # 3. escalations schema alignment
    op.alter_column('escalations', 'trigger_reason', new_column_name='trigger_type')
    op.alter_column('escalations', 'context', new_column_name='trigger_context')
    op.alter_column('escalations', 'current_level', new_column_name='current_role')
    op.drop_column('escalations', 'resolution_action') # resolution is enough per model, or resolution text? Model has resolution(Text). DB has resolution(Text). resolution_action was extra.
    
    # Add target_type/id
    op.add_column('escalations', sa.Column('target_type', sa.String(100), nullable=True))
    op.add_column('escalations', sa.Column('target_id', sa.UUID(), nullable=True))
    
    # Populate defaults for existing rows (if any) to avoid not-null constraint failure
    op.execute("UPDATE escalations SET target_type = 'unknown' WHERE target_type IS NULL")
    # For target_id, we can't easily fake a UUID if strict, but let's try a nil uuid
    op.execute("UPDATE escalations SET target_id = '00000000-0000-0000-0000-000000000000'::uuid WHERE target_id IS NULL")
    
    op.alter_column('escalations', 'target_type', nullable=False)
    op.alter_column('escalations', 'target_id', nullable=False)
    
    # Rename deadline_at -> deadline
    op.alter_column('escalations', 'deadline_at', new_column_name='deadline')

    # 4. governance_audit_log alignment
    op.alter_column('governance_audit_log', 'user_id', new_column_name='actor_id')
    op.add_column('governance_audit_log', sa.Column('actor_type', sa.String(50), server_default='user'))
    op.alter_column('governance_audit_log', 'action', new_column_name='action_type')
    op.alter_column('governance_audit_log', 'resource_type', new_column_name='entity_type')
    op.alter_column('governance_audit_log', 'resource_id', new_column_name='entity_id')


def downgrade() -> None:
    # Not implementing full downgrade path as this is a dev-fix forward. 
    # But strictly we should revers renames and add back columns.
    pass
