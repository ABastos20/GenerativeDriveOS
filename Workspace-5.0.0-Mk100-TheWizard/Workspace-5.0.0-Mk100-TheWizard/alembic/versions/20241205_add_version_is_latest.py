"""Add version and is_latest to documents table (Story 4.5.3b)

Revision ID: 20241205_add_version_is_latest
Revises: 934b0af4119f
Create Date: 2025-12-05

Story 4.5.3b: Qdrant is_latest Payload Filter
- version: incremented on re-ingest to track document versions
- is_latest: boolean for filtering stale versions at Qdrant query time
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20241205_add_version_is_latest"
down_revision = "934b0af4119f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add version and is_latest columns to documents table."""
    # Add version column with default 1 (existing docs get version 1)
    op.add_column(
        "documents",
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="Document version number (incremented on re-ingest)",
        ),
    )
    
    # Add is_latest column with default TRUE (existing docs are latest)
    op.add_column(
        "documents",
        sa.Column(
            "is_latest",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="True if this is the latest version of the doc_key",
        ),
    )
    
    # Add index on is_latest for efficient filtering
    op.create_index(
        "ix_documents_is_latest",
        "documents",
        ["is_latest"],
        unique=False,
    )
    
    # Add composite index for common query pattern: doc_key + is_latest
    op.create_index(
        "ix_documents_doc_key_is_latest",
        "documents",
        ["doc_key", "is_latest"],
        unique=False,
    )


def downgrade() -> None:
    """Remove version and is_latest columns."""
    op.drop_index("ix_documents_doc_key_is_latest", table_name="documents")
    op.drop_index("ix_documents_is_latest", table_name="documents")
    op.drop_column("documents", "is_latest")
    op.drop_column("documents", "version")
