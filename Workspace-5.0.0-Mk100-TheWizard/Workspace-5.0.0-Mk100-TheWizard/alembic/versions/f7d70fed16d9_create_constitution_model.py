"""create_constitution_model

Revision ID: f7d70fed16d9
Revises: 0ce7da1d2c6c
Create Date: 2025-12-08 20:39:38.677055

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f7d70fed16d9'
down_revision: Union[str, Sequence[str], None] = '0ce7da1d2c6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('constitutions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('weight_epistemic', sa.Float(), nullable=False),
    sa.Column('weight_consistency', sa.Float(), nullable=False),
    sa.Column('weight_integrity', sa.Float(), nullable=False),
    sa.Column('weight_reputation', sa.Float(), nullable=False),
    sa.Column('sybil_threshold', sa.Float(), nullable=False),
    sa.Column('minority_floor', sa.Float(), nullable=False),
    sa.Column('anti_elite_multiplier', sa.Float(), nullable=False),
    sa.Column('max_legitimacy_drift', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_constitutions_active'), 'constitutions', ['active'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_constitutions_active'), table_name='constitutions')
    op.drop_table('constitutions')
