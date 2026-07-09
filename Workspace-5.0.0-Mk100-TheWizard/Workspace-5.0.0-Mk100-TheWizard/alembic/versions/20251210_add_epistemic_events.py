"""Add epistemic events table for audit persistence.

Story 11-5.4: PostgreSQL Persistence Sink

Revision ID: 20251210_add_epistemic_events
Revises: 20251209_identity_split
Create Date: 2025-12-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '20251210_add_epistemic_events'
down_revision = 'a11001100110'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create epistemic_events table for audit persistence."""
    op.create_table(
        'epistemic_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, comment='Event UUID'),
        sa.Column('event_type', sa.String(50), nullable=False, index=True,
                  comment='promotion | demotion | decay | freeze | contradiction | usage_violation'),
        sa.Column('knowledge_unit_id', UUID(as_uuid=True), nullable=False, index=True,
                  comment='ID of affected knowledge unit'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True,
                  comment='Event timestamp (UTC)'),
        sa.Column('payload', JSONB, nullable=False,
                  comment='Full event data as JSON'),
        comment='Epistemic audit events for compliance and forensic reconstruction'
    )
    
    # Composite index for common query pattern: event_type + timestamp
    op.create_index(
        'ix_epistemic_events_type_time',
        'epistemic_events',
        ['event_type', 'timestamp']
    )


def downgrade() -> None:
    """Remove epistemic_events table."""
    op.drop_index('ix_epistemic_events_type_time', table_name='epistemic_events')
    op.drop_table('epistemic_events')
