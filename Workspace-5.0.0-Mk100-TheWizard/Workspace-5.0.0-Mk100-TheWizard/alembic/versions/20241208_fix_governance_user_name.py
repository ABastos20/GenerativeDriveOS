"""Fix governance user schema add name

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-12-08 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing name column to governance_users."""
    op.add_column('governance_users', sa.Column('name', sa.String(length=255), nullable=True))
    
    # Populate existing rows (if any)
    op.execute("UPDATE governance_users SET name = 'Unknown User'")
    
    # Enforce not null
    op.alter_column('governance_users', 'name', nullable=False)


def downgrade() -> None:
    """Revert changes."""
    op.drop_column('governance_users', 'name')
