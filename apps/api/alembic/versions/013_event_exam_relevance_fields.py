"""Add exam relevance fields to events

Revision ID: 013_event_exam_relevance_fields
Revises: 012_pyq_verification_fields
Create Date: 2026-10-27 10:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '013_event_exam_relevance_fields'
down_revision: Union[str, None] = '012_pyq_verification_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = {c['name'] for c in insp.get_columns('events')}
    indexes = {i['name'] for i in insp.get_indexes('events')}

    if 'is_exam_eligible' not in cols:
        op.add_column(
            'events',
            sa.Column('is_exam_eligible', sa.Boolean(), nullable=False, server_default='true')
        )

    # Independent index check: create missing index even if column already exists
    if 'ix_events_is_exam_eligible' not in indexes:
        op.create_index('ix_events_is_exam_eligible', 'events', ['is_exam_eligible'])

    if 'rejection_reason' not in cols:
        op.add_column(
            'events',
            sa.Column('rejection_reason', sa.String(255), nullable=True)
        )

    if 'inclusion_reason' not in cols:
        op.add_column(
            'events',
            sa.Column('inclusion_reason', sa.String(255), nullable=True)
        )

    if 'syllabus_topic' not in cols:
        op.add_column(
            'events',
            sa.Column('syllabus_topic', sa.String(150), nullable=True)
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = {c['name'] for c in insp.get_columns('events')}
    indexes = {i['name'] for i in insp.get_indexes('events')}

    if 'syllabus_topic' in cols:
        op.drop_column('events', 'syllabus_topic')
    if 'inclusion_reason' in cols:
        op.drop_column('events', 'inclusion_reason')
    if 'rejection_reason' in cols:
        op.drop_column('events', 'rejection_reason')

    # Independent index drop: drop only if index exists
    if 'ix_events_is_exam_eligible' in indexes:
        op.drop_index('ix_events_is_exam_eligible', table_name='events')

    if 'is_exam_eligible' in cols:
        op.drop_column('events', 'is_exam_eligible')
