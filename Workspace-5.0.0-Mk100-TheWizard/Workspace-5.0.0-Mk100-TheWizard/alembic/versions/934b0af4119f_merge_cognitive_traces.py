"""merge cognitive_traces

Revision ID: 934b0af4119f
Revises: 20241204_add_cognitive_traces, 20241204_add_memory_attribution
Create Date: 2025-12-04 22:29:12.860689

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '934b0af4119f'
down_revision: Union[str, Sequence[str], None] = ('20241204_add_cognitive_traces', '20241204_add_memory_attribution')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
