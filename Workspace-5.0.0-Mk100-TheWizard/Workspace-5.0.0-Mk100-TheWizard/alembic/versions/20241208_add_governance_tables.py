"""Add governance tables for Story 9-1

Revision ID: a1b2c3d4e5f6
Revises: 569456b4b01a
Create Date: 2025-12-08 18:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '569456b4b01a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add governance tables for multi-human governance model."""
    
    # 1. GovernanceUser table - Stores governance participants
    op.create_table('governance_users',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False, comment='External identity (email, OAuth ID)'),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, comment='owner | admin | contributor | observer'),
        sa.Column('trust_score', sa.Numeric(precision=4, scale=3), nullable=False, server_default='0.500', comment='Trust weight (0-1)'),
        sa.Column('claimed_expertise', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Self-declared expertise domains'),
        sa.Column('demonstrated_expertise', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='System-inferred expertise'),
        sa.Column('engagement_score', sa.Numeric(precision=4, scale=3), nullable=False, server_default='0.000', comment='Activity engagement metric'),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Explicit permission overrides'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governance_users_external_id'), 'governance_users', ['external_id'], unique=True)
    op.create_index(op.f('ix_governance_users_role'), 'governance_users', ['role'], unique=False)
    op.create_index(op.f('ix_governance_users_is_active'), 'governance_users', ['is_active'], unique=False)
    
    # 2. Permission table - Named permission sets
    op.create_table('permissions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Permission name (e.g., "vote_on_conflicts")'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, comment='voting | escalation | override | admin'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)
    op.create_index(op.f('ix_permissions_category'), 'permissions', ['category'], unique=False)
    
    # 3. EscalationRule table - Defines escalation triggers and behavior
    op.create_table('escalation_rules',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger_type', sa.String(length=50), nullable=False, comment='tie_vote | quorum_failure | csi_threshold | constitutional_conflict | timeout'),
        sa.Column('trigger_condition', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='JSON condition spec'),
        sa.Column('escalation_target', sa.String(length=50), nullable=False, comment='role | user_id | external'),
        sa.Column('target_value', sa.String(length=255), nullable=False, comment='The specific target (e.g., "admin", specific user ID)'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100', comment='Lower = higher priority'),
        sa.Column('timeout_hours', sa.Integer(), nullable=True, comment='Hours before auto-escalation'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_escalation_rules_trigger_type'), 'escalation_rules', ['trigger_type'], unique=False)
    op.create_index(op.f('ix_escalation_rules_is_active'), 'escalation_rules', ['is_active'], unique=False)
    op.create_index(op.f('ix_escalation_rules_priority'), 'escalation_rules', ['priority'], unique=False)
    
    # 4. Escalation table - Active escalation instances
    op.create_table('escalations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('rule_id', sa.UUID(), nullable=True, comment='Link to trigger rule'),
        sa.Column('trigger_reason', sa.String(length=100), nullable=False),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Full context of what triggered escalation'),
        sa.Column('current_level', sa.String(length=50), nullable=False, comment='contributor | admin | owner'),
        sa.Column('assigned_to', sa.UUID(), nullable=True, comment='Currently assigned user'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default="'pending'", comment='pending | in_progress | resolved | expired'),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('resolution_action', sa.String(length=100), nullable=True, comment='approved | rejected | deferred | override'),
        sa.Column('resolved_by', sa.UUID(), nullable=True),
        sa.Column('escalation_chain', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='History of escalation path'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deadline_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['rule_id'], ['escalation_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['governance_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by'], ['governance_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_escalations_status'), 'escalations', ['status'], unique=False)
    op.create_index(op.f('ix_escalations_current_level'), 'escalations', ['current_level'], unique=False)
    op.create_index(op.f('ix_escalations_assigned_to'), 'escalations', ['assigned_to'], unique=False)
    op.create_index(op.f('ix_escalations_deadline_at'), 'escalations', ['deadline_at'], unique=False)
    
    # 5. GovernanceAuditLog table - Immutable audit trail
    op.create_table('governance_audit_log',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True, comment='Actor (null for system actions)'),
        sa.Column('action', sa.String(length=100), nullable=False, comment='Action performed'),
        sa.Column('resource_type', sa.String(length=100), nullable=False, comment='Type of resource affected'),
        sa.Column('resource_id', sa.UUID(), nullable=True, comment='ID of affected resource'),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Previous state'),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='New state'),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional context'),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['governance_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governance_audit_log_user_id'), 'governance_audit_log', ['user_id'], unique=False)
    op.create_index(op.f('ix_governance_audit_log_action'), 'governance_audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_governance_audit_log_resource_type'), 'governance_audit_log', ['resource_type'], unique=False)
    op.create_index(op.f('ix_governance_audit_log_created_at'), 'governance_audit_log', ['created_at'], unique=False)


def downgrade() -> None:
    """Remove governance tables."""
    # Drop in reverse order of creation (respecting foreign keys)
    op.drop_index(op.f('ix_governance_audit_log_created_at'), table_name='governance_audit_log')
    op.drop_index(op.f('ix_governance_audit_log_resource_type'), table_name='governance_audit_log')
    op.drop_index(op.f('ix_governance_audit_log_action'), table_name='governance_audit_log')
    op.drop_index(op.f('ix_governance_audit_log_user_id'), table_name='governance_audit_log')
    op.drop_table('governance_audit_log')
    
    op.drop_index(op.f('ix_escalations_deadline_at'), table_name='escalations')
    op.drop_index(op.f('ix_escalations_assigned_to'), table_name='escalations')
    op.drop_index(op.f('ix_escalations_current_level'), table_name='escalations')
    op.drop_index(op.f('ix_escalations_status'), table_name='escalations')
    op.drop_table('escalations')
    
    op.drop_index(op.f('ix_escalation_rules_priority'), table_name='escalation_rules')
    op.drop_index(op.f('ix_escalation_rules_is_active'), table_name='escalation_rules')
    op.drop_index(op.f('ix_escalation_rules_trigger_type'), table_name='escalation_rules')
    op.drop_table('escalation_rules')
    
    op.drop_index(op.f('ix_permissions_category'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
    op.drop_table('permissions')
    
    op.drop_index(op.f('ix_governance_users_is_active'), table_name='governance_users')
    op.drop_index(op.f('ix_governance_users_role'), table_name='governance_users')
    op.drop_index(op.f('ix_governance_users_external_id'), table_name='governance_users')
    op.drop_table('governance_users')
