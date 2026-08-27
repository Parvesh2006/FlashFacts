"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-18 21:34:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=512), nullable=False),
        sa.Column('feed_url', sa.String(length=512), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='rss'),
        sa.Column('domain', sa.String(length=100), nullable=False, server_default='General'),
        sa.Column('reliability_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sources_id', 'sources', ['id'], unique=False)
    op.create_index('ix_sources_feed_url', 'sources', ['feed_url'], unique=True)
    op.create_index('ix_sources_domain', 'sources', ['domain'], unique=False)
    op.create_index('ix_sources_enabled', 'sources', ['enabled'], unique=False)

    # documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('crawled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_id', 'documents', ['id'], unique=False)
    op.create_index('ix_documents_source_id', 'documents', ['source_id'], unique=False)
    op.create_index('ix_documents_content_hash', 'documents', ['content_hash'], unique=True)
    op.create_index('ix_documents_published_at', 'documents', ['published_at'], unique=False)

    # events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(length=100), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('source_url', sa.String(length=1024), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('dedup_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_events_id', 'events', ['id'], unique=False)
    op.create_index('ix_events_title', 'events', ['title'], unique=False)
    op.create_index('ix_events_domain', 'events', ['domain'], unique=False)
    op.create_index('ix_events_event_date', 'events', ['event_date'], unique=False)
    op.create_index('ix_events_published_at', 'events', ['published_at'], unique=False)
    op.create_index('ix_events_source_id', 'events', ['source_id'], unique=False)
    op.create_index('ix_events_dedup_hash', 'events', ['dedup_hash'], unique=True)

    # event_sources table
    op.create_table(
        'event_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_event_sources_id', 'event_sources', ['id'], unique=False)
    op.create_index('ix_event_sources_event_id', 'event_sources', ['event_id'], unique=False)
    op.create_index('ix_event_sources_document_id', 'event_sources', ['document_id'], unique=False)

    # processing_jobs table
    op.create_table(
        'processing_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('items_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_processing_jobs_id', 'processing_jobs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_processing_jobs_id', table_name='processing_jobs')
    op.drop_table('processing_jobs')
    
    op.drop_index('ix_event_sources_document_id', table_name='event_sources')
    op.drop_index('ix_event_sources_event_id', table_name='event_sources')
    op.drop_index('ix_event_sources_id', table_name='event_sources')
    op.drop_table('event_sources')

    op.drop_index('ix_events_dedup_hash', table_name='events')
    op.drop_index('ix_events_source_id', table_name='events')
    op.drop_index('ix_events_published_at', table_name='events')
    op.drop_index('ix_events_event_date', table_name='events')
    op.drop_index('ix_events_domain', table_name='events')
    op.drop_index('ix_events_title', table_name='events')
    op.drop_index('ix_events_id', table_name='events')
    op.drop_table('events')

    op.drop_index('ix_documents_published_at', table_name='documents')
    op.drop_index('ix_documents_content_hash', table_name='documents')
    op.drop_index('ix_documents_source_id', table_name='documents')
    op.drop_index('ix_documents_id', table_name='documents')
    op.drop_table('documents')

    op.drop_index('ix_sources_enabled', table_name='sources')
    op.drop_index('ix_sources_domain', table_name='sources')
    op.drop_index('ix_sources_feed_url', table_name='sources')
    op.drop_index('ix_sources_id', table_name='sources')
    op.drop_table('sources')
