"""add message citation_provenance

Revision ID: 4d2a3c1b9e0c
Revises: 0f3513bed9f3
Create Date: 2025-11-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "4d2a3c1b9e0c"
down_revision: Union[str, Sequence[str], None] = "0f3513bed9f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add citation_provenance column to messages table."""
    op.add_column(
        "messages",
        sa.Column(
            "citation_provenance",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Stored citation metadata for assistant messages (sources[], scores, hashes, etc.)",
        ),
    )


def downgrade() -> None:
    """Remove citation_provenance column from messages table."""
    op.drop_column("messages", "citation_provenance")

