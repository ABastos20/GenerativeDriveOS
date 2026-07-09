"""Add frozen trust snapshot to Proposal

Revision ID: eb7f240665a0
Revises: f7d70fed16d9
Create Date: 2025-12-08 21:16:18.622064

Story 9-5: Governance Locks
- frozen_trust_snapshot: JSON snapshot of all trust scores when proposal opens
- total_weight_at_open: Total system weight for legitimacy conservation check
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'eb7f240665a0'
down_revision: Union[str, Sequence[str], None] = 'f7d70fed16d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add governance lock columns to proposals table."""
    # Story 9-5: Governance Locks
    op.add_column('proposals', sa.Column('frozen_trust_snapshot', sa.JSON(), nullable=True))
    op.add_column('proposals', sa.Column('total_weight_at_open', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove governance lock columns from proposals table."""
    op.drop_column('proposals', 'total_weight_at_open')
    op.drop_column('proposals', 'frozen_trust_snapshot')
