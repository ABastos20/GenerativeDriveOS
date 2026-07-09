"""Add research_logs table for research mode analytics."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20241205_add_research_logs"
down_revision = "7b9e2d4c1f0a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gap_types", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("planned_queries", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("executed_queries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sources_collected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("confidence_before", sa.Numeric(4, 3), nullable=True),
        sa.Column("confidence_after", sa.Numeric(4, 3), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.PrimaryKeyConstraint("id"),
        comment="Research sessions executed via research mode",
    )
    op.create_index("ix_research_logs_conversation_id", "research_logs", ["conversation_id"])
    op.create_index("ix_research_logs_message_id", "research_logs", ["message_id"])
    op.create_index("ix_research_logs_created_at", "research_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_research_logs_created_at", table_name="research_logs")
    op.drop_index("ix_research_logs_message_id", table_name="research_logs")
    op.drop_index("ix_research_logs_conversation_id", table_name="research_logs")
    op.drop_table("research_logs")
