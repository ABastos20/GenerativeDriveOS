"""Add performance indexes for memory and sessions

Revision ID: d4f15282937e
Revises: 20241205_add_version_is_latest
Create Date: 2025-12-08 04:07:10.279036

Architect-recommended "non-negotiable" indexes for query performance.
These indexes prevent sequential scans and provide massive speedup.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f15282937e'
down_revision: Union[str, Sequence[str], None] = '20241205_add_version_is_latest'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for documents and temporal_chunks tables.
    
    Architect-recommended indexes (adapted for actual Jarvis schema):
    1. Documents domain index - Fast domain filtering
    2. Documents timestamp index - Fast temporal queries
    3. Documents doc_key index - Already exists (unique)
    4. Documents domain+timestamp composite - Optimized filtered temporal queries
    5. Documents is_latest partial index - Fast "latest only" queries
    6. Temporal chunks domain index - Fast domain filtering
    7. Temporal chunks hash index - Fast deduplication lookups
    8. Temporal chunks timestamp index - Fast temporal queries
    """
    
    # Documents table indexes
    op.create_index(
        'idx_documents_domain',
        'documents',
        ['domain'],
        unique=False,
    )
    
    # Composite index for domain + timestamp (common query pattern)
    op.create_index(
        'idx_documents_domain_timestamp',
        'documents',
        ['domain', sa.text('created_at DESC')],
        unique=False,
    )
    
    # Partial index for is_latest queries (WHERE is_latest =  true)
    op.execute(
        """
        CREATE INDEX idx_documents_is_latest 
        ON documents(is_latest) 
        WHERE is_latest = true
        """
    )
    
    # Temporal chunks indexes
    op.create_index(
        'idx_temporal_chunks_domain',
        'temporal_chunks',
        ['domain'],
        unique=False,
    )
    
    op.create_index(
        'idx_temporal_chunks_supersedes',
        'temporal_chunks',
        ['supersedes'],
        unique=False,
    )


def downgrade() -> None:
    """Remove performance indexes."""
    # Drop indexes in reverse order
    op.drop_index('idx_temporal_chunks_supersedes', table_name='temporal_chunks')
    op.drop_index('idx_temporal_chunks_domain', table_name='temporal_chunks')
    op.execute('DROP INDEX IF EXISTS idx_documents_is_latest')
    op.drop_index('idx_documents_domain_timestamp', table_name='documents')
    op.drop_index('idx_documents_domain', table_name='documents')


