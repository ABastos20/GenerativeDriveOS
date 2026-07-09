"""add knowledge_domains table

Revision ID: 7b9e2d4c1f0a
Revises: 4d2a3c1b9e0c
Create Date: 2025-12-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b9e2d4c1f0a"
down_revision: Union[str, Sequence[str], None] = "4d2a3c1b9e0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create knowledge_domains table for domain taxonomy."""
    op.create_table(
        "knowledge_domains",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "key",
            sa.String(length=100),
            nullable=False,
            unique=True,
            comment="Stable domain key, e.g. 'architecture.core', 'history.modern'",
        ),
        sa.Column(
            "label",
            sa.String(length=200),
            nullable=False,
            comment="Human-readable label for the domain",
        ),
        sa.Column(
            "parent_key",
            sa.String(length=100),
            nullable=True,
            comment="Optional parent domain key for hierarchical taxonomy",
        ),
        sa.Column(
            "kind",
            sa.String(length=50),
            nullable=False,
            server_default="generic",
            comment="Category of domain: human_science | product_branch | infra | generic",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Drop knowledge_domains table."""
    op.drop_table("knowledge_domains")

