"""003_ingestion_tracking

Revision ID: 003_ingestion_tracking
Revises: 002_event_enrichment_and_entities
Create Date: 2026-09-01 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_ingestion_tracking'
down_revision: Union[str, None] = '002_event_enrichment_and_entities'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ingestion_runs table
    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='running'),
        sa.Column('sources_attempted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sources_succeeded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sources_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_discovered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_accepted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_duplicate', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('events_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('events_deduplicated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processing_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ingestion_runs_id', 'ingestion_runs', ['id'], unique=False)
    op.create_index('ix_ingestion_runs_status', 'ingestion_runs', ['status'], unique=False)

    # Create source_ingestion_metrics table
    op.create_table(
        'source_ingestion_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ingestion_run_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='running'),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('documents_discovered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_accepted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_duplicate', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('events_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('events_deduplicated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processing_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['ingestion_run_id'], ['ingestion_runs.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_source_ingestion_metrics_id', 'source_ingestion_metrics', ['id'], unique=False)
    op.create_index('ix_source_ingestion_metrics_ingestion_run_id', 'source_ingestion_metrics', ['ingestion_run_id'], unique=False)
    op.create_index('ix_source_ingestion_metrics_source_id', 'source_ingestion_metrics', ['source_id'], unique=False)
    op.create_index('ix_source_ingestion_metrics_status', 'source_ingestion_metrics', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_source_ingestion_metrics_status', table_name='source_ingestion_metrics')
    op.drop_index('ix_source_ingestion_metrics_source_id', table_name='source_ingestion_metrics')
    op.drop_index('ix_source_ingestion_metrics_ingestion_run_id', table_name='source_ingestion_metrics')
    op.drop_index('ix_source_ingestion_metrics_id', table_name='source_ingestion_metrics')
    op.drop_table('source_ingestion_metrics')
    op.drop_index('ix_ingestion_runs_status', table_name='ingestion_runs')
    op.drop_index('ix_ingestion_runs_id', table_name='ingestion_runs')
    op.drop_table('ingestion_runs')
