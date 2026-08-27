"""002_event_enrichment_and_entities

Revision ID: 002_event_enrichment_and_entities
Revises: 001_initial_schema
Create Date: 2026-08-19 04:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_event_enrichment_and_entities'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_ingested_at to sources
    op.add_column('sources', sa.Column('last_ingested_at', sa.DateTime(timezone=True), nullable=True))

    # Add AI enrichment fields to events
    op.add_column('events', sa.Column('why_it_matters', sa.Text(), nullable=True))
    op.add_column('events', sa.Column('importance_score', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('events', sa.Column('classification_confidence', sa.Float(), nullable=False, server_default='1.0'))
    op.add_column('events', sa.Column('ai_processed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('events', sa.Column('processing_status', sa.String(length=50), nullable=False, server_default='completed'))

    op.create_index('ix_events_importance_score', 'events', ['importance_score'], unique=False)
    op.create_index('ix_events_processing_status', 'events', ['processing_status'], unique=False)

    # Create entities table
    op.create_table(
        'entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_entities_id', 'entities', ['id'], unique=False)
    op.create_index('ix_entities_name', 'entities', ['name'], unique=True)
    op.create_index('ix_entities_entity_type', 'entities', ['entity_type'], unique=False)

    # Create event_entities table
    op.create_table(
        'event_entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_event_entities_id', 'event_entities', ['id'], unique=False)
    op.create_index('ix_event_entities_event_id', 'event_entities', ['event_id'], unique=False)
    op.create_index('ix_event_entities_entity_id', 'event_entities', ['entity_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_event_entities_entity_id', table_name='event_entities')
    op.drop_index('ix_event_entities_event_id', table_name='event_entities')
    op.drop_index('ix_event_entities_id', table_name='event_entities')
    op.drop_table('event_entities')

    op.drop_index('ix_entities_entity_type', table_name='entities')
    op.drop_index('ix_entities_name', table_name='entities')
    op.drop_index('ix_entities_id', table_name='entities')
    op.drop_table('entities')

    op.drop_index('ix_events_processing_status', table_name='events')
    op.drop_index('ix_events_importance_score', table_name='events')
    op.drop_column('events', 'processing_status')
    op.drop_column('events', 'ai_processed_at')
    op.drop_column('events', 'classification_confidence')
    op.drop_column('events', 'importance_score')
    op.drop_column('events', 'why_it_matters')

    op.drop_column('sources', 'last_ingested_at')
