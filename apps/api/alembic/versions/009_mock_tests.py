"""Add Mock Test models

Revision ID: 009_mock_tests
Revises: 008_pyqs
Create Date: 2026-10-09 16:03:13.630799

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009_mock_tests'
down_revision: Union[str, None] = '008_pyqs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('mock_tests',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('exam_name', sa.String(length=100), nullable=False),
    sa.Column('domain', sa.String(length=100), nullable=True),
    sa.Column('language', sa.String(length=10), nullable=False),
    sa.Column('difficulty', sa.String(length=20), nullable=False),
    sa.Column('total_questions', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_tests_id'), 'mock_tests', ['id'], unique=False)

    op.create_table('mock_test_attempts',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('test_id', sa.String(length=36), nullable=False),
    sa.Column('answers', sa.JSON(), nullable=False),
    sa.Column('score', sa.Integer(), nullable=False),
    sa.Column('accuracy', sa.Integer(), nullable=False),
    sa.Column('total_answered', sa.Integer(), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['test_id'], ['mock_tests.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_test_attempts_id'), 'mock_test_attempts', ['id'], unique=False)

    op.create_table('mock_test_questions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('test_id', sa.String(length=36), nullable=False),
    sa.Column('question_order', sa.Integer(), nullable=False),
    sa.Column('is_pyq', sa.Boolean(), nullable=True),
    sa.Column('pyq_id', sa.Integer(), nullable=True),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('options', sa.JSON(), nullable=False),
    sa.Column('correct_answer', sa.String(length=255), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=True),
    sa.Column('reference_url', sa.String(length=512), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    sa.ForeignKeyConstraint(['pyq_id'], ['pyqs.id'], ),
    sa.ForeignKeyConstraint(['test_id'], ['mock_tests.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_test_questions_id'), 'mock_test_questions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_mock_test_questions_id'), table_name='mock_test_questions')
    op.drop_table('mock_test_questions')
    op.drop_index(op.f('ix_mock_test_attempts_id'), table_name='mock_test_attempts')
    op.drop_table('mock_test_attempts')
    op.drop_index(op.f('ix_mock_tests_id'), table_name='mock_tests')
    op.drop_table('mock_tests')
