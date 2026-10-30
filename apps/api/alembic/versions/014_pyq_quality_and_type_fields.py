"""Add question_type, quality_status, and rejection_reason columns to pyqs

Revision ID: 014_pyq_quality_and_type_fields
Revises: 013_event_exam_relevance_fields
Create Date: 2026-10-27 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '014_pyq_quality_and_type_fields'
down_revision: Union[str, None] = '013_event_exam_relevance_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = {c['name'] for c in insp.get_columns('pyqs')}
    indexes = {i['name'] for i in insp.get_indexes('pyqs')}

    if 'question_type' not in cols:
        op.add_column(
            'pyqs',
            sa.Column('question_type', sa.String(50), nullable=False, server_default='syllabus_practice')
        )

    # Independent index check: create missing index even if column already exists
    if 'ix_pyqs_question_type' not in indexes:
        op.create_index('ix_pyqs_question_type', 'pyqs', ['question_type'])

    if 'quality_status' not in cols:
        op.add_column(
            'pyqs',
            sa.Column('quality_status', sa.String(50), nullable=False, server_default='valid')
        )

    # Independent index check: create missing index even if column already exists
    if 'ix_pyqs_quality_status' not in indexes:
        op.create_index('ix_pyqs_quality_status', 'pyqs', ['quality_status'])

    if 'rejection_reason' not in cols:
        op.add_column(
            'pyqs',
            sa.Column('rejection_reason', sa.String(255), nullable=True)
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = {c['name'] for c in insp.get_columns('pyqs')}
    indexes = {i['name'] for i in insp.get_indexes('pyqs')}

    if 'rejection_reason' in cols:
        op.drop_column('pyqs', 'rejection_reason')

    # Independent index drop: drop only if index exists
    if 'ix_pyqs_quality_status' in indexes:
        op.drop_index('ix_pyqs_quality_status', table_name='pyqs')

    if 'quality_status' in cols:
        op.drop_column('pyqs', 'quality_status')

    # Independent index drop: drop only if index exists
    if 'ix_pyqs_question_type' in indexes:
        op.drop_index('ix_pyqs_question_type', table_name='pyqs')

    if 'question_type' in cols:
        op.drop_column('pyqs', 'question_type')
