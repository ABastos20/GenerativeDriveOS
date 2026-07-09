"""Add cognitive_traces table for ARCHES trace logging (Story 4.5.6).

Revision ID: 20241204_add_cognitive_traces
Revises: 20241205_add_voting_metadata
Create Date: 2024-12-04

Captures full cognitive trace of query lifecycle for debugging and replay.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision = "20241204_add_cognitive_traces"
down_revision = "20241205_add_voting_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create cognitive_traces table with indexes."""
    op.create_table(
        "cognitive_traces",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("trace_id", UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(50), nullable=False, server_default="qa"),
        sa.Column("severity", sa.String(50), nullable=False, server_default="normal"),
        sa.Column("sampled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("trace_schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("trace_data", JSONB(), nullable=False),
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trace_id"),
        comment="Cognitive traces for ARCHES query debugging and replay",
    )
    
    # Add indexes for efficient querying
    op.create_index("ix_cognitive_traces_trace_id", "cognitive_traces", ["trace_id"])
    op.create_index("ix_cognitive_traces_session_id", "cognitive_traces", ["session_id"])
    op.create_index("ix_cognitive_traces_severity", "cognitive_traces", ["severity"])
    op.create_index("ix_cognitive_traces_created_at", "cognitive_traces", ["created_at"])


def downgrade() -> None:
    """Drop cognitive_traces table."""
    op.drop_index("ix_cognitive_traces_created_at", table_name="cognitive_traces")
    op.drop_index("ix_cognitive_traces_severity", table_name="cognitive_traces")
    op.drop_index("ix_cognitive_traces_session_id", table_name="cognitive_traces")
    op.drop_index("ix_cognitive_traces_trace_id", table_name="cognitive_traces")
    op.drop_table("cognitive_traces")
