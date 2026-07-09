"""Add temporal_chunks table for versioned chunk metadata."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20241205_add_temporal_chunks"
down_revision = "20241205_add_research_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "temporal_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("collection", sa.String(length=100), nullable=False, server_default="knowledge"),
        sa.Column("domain", sa.String(length=100), nullable=True),
        sa.Column("source_file", sa.String(length=500), nullable=True),
        sa.Column("section", sa.String(length=200), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="web_research"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0.5"),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.PrimaryKeyConstraint("id"),
        comment="Versioned chunk metadata for temporal memory updates",
    )
    op.create_index("ix_temporal_chunks_content_hash", "temporal_chunks", ["content_hash"])
    op.create_index("ix_temporal_chunks_supersedes", "temporal_chunks", ["supersedes"])
    op.create_index("ix_temporal_chunks_created_at", "temporal_chunks", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_temporal_chunks_created_at", table_name="temporal_chunks")
    op.drop_index("ix_temporal_chunks_supersedes", table_name="temporal_chunks")
    op.drop_index("ix_temporal_chunks_content_hash", table_name="temporal_chunks")
    op.drop_table("temporal_chunks")
