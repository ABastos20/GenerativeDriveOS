"""Add memory_attribution JSONB column to messages table (Story 4.5.2).

Revision ID: 20241204_add_memory_attribution
Revises: 20241205_add_voting_metadata
Create Date: 2024-12-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20241204_add_memory_attribution"
down_revision = "20241205_add_voting_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add memory_attribution JSONB column to messages table."""
    op.add_column(
        "messages",
        sa.Column(
            "memory_attribution",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Per-agent memory chunk/domain/source attribution (Story 4.5.2)",
        ),
    )
    
    # Create GIN index for efficient JSONB queries
    op.create_index(
        "ix_messages_memory_attribution",
        "messages",
        ["memory_attribution"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Remove memory_attribution column."""
    op.drop_index("ix_messages_memory_attribution", table_name="messages")
    op.drop_column("messages", "memory_attribution")
