"""add voting_metadata to messages

Revision ID: 20241205_add_voting_metadata
Revises: 20241205_add_temporal_chunks
Create Date: 2024-12-05 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241205_add_voting_metadata'
down_revision = '20241205_add_temporal_chunks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if column already exists before adding (idempotent)
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='messages' AND column_name='voting_metadata'
    """))
    if result.fetchone() is None:
        op.add_column('messages', sa.Column('voting_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Council of Ricks voting results and override metadata (Story 4.5)'))


def downgrade() -> None:
    op.drop_column('messages', 'voting_metadata')
