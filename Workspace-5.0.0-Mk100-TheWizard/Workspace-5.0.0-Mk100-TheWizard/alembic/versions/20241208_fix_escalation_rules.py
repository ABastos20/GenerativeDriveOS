"""Fix escalation rules schema

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-08 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix EscalationRule schema to match models.py."""
    
    # 1. Add missing columns
    op.add_column('escalation_rules', sa.Column('threshold_value', sa.Float(), nullable=True))
    op.add_column('escalation_rules', sa.Column('threshold_operator', sa.String(length=10), nullable=True))
    op.add_column('escalation_rules', sa.Column('auto_escalate_further', sa.Boolean(), server_default='true', nullable=False))
    
    # 2. Add escalate_to_role (enum or string)
    # Use generic string to simplify (enum handling in alembic can be tricky with existing types)
    op.add_column('escalation_rules', sa.Column('escalate_to_role', sa.String(length=50), nullable=True))
    
    # Populate new columns from old ones if possible (best effort migration)
    op.execute("UPDATE escalation_rules SET escalate_to_role = 'admin'") # Default
    
    # Make nullable false after population
    op.alter_column('escalation_rules', 'escalate_to_role', nullable=False)

    # 3. Drop incompatible columns
    op.drop_column('escalation_rules', 'trigger_condition')
    op.drop_column('escalation_rules', 'escalation_target')
    op.drop_column('escalation_rules', 'target_value')


def downgrade() -> None:
    """Revert changes."""
    op.add_column('escalation_rules', sa.Column('target_value', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column('escalation_rules', sa.Column('escalation_target', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('escalation_rules', sa.Column('trigger_condition', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
    
    # Populate dummy data for not null constraint
    op.execute("UPDATE escalation_rules SET trigger_condition = '{}', escalation_target = 'role', target_value = 'admin'")
    
    op.alter_column('escalation_rules', 'target_value', nullable=False)
    op.alter_column('escalation_rules', 'escalation_target', nullable=False)
    op.alter_column('escalation_rules', 'trigger_condition', nullable=False)
    
    op.drop_column('escalation_rules', 'escalate_to_role')
    op.drop_column('escalation_rules', 'auto_escalate_further')
    op.drop_column('escalation_rules', 'threshold_operator')
    op.drop_column('escalation_rules', 'threshold_value')
