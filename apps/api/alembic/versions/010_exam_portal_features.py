"""Add Exam Portal features: users, bookmarks, revisions, syllabus, test settings

Revision ID: 010_exam_portal_features
Revises: 009_mock_tests
Create Date: 2026-10-20 11:41:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010_exam_portal_features'
down_revision: Union[str, None] = '009_mock_tests'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('is_guest', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('target_exam', sa.String(length=100), nullable=False, server_default='TNPSC Group 4'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Add columns to pyqs
    op.add_column('pyqs', sa.Column('topic', sa.String(length=100), nullable=True))
    op.add_column('pyqs', sa.Column('source', sa.String(length=255), nullable=True))
    op.add_column('pyqs', sa.Column('language', sa.String(length=10), nullable=False, server_default='en'))
    op.add_column('pyqs', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.create_index(op.f('ix_pyqs_topic'), 'pyqs', ['topic'], unique=False)

    # 3. Add columns to mock_tests
    op.add_column('mock_tests', sa.Column('time_limit_minutes', sa.Integer(), nullable=False, server_default='30'))
    op.add_column('mock_tests', sa.Column('negative_marking', sa.Float(), nullable=False, server_default='0.0'))

    # 4. Add columns to mock_test_attempts
    op.add_column('mock_test_attempts', sa.Column('user_id', sa.String(length=36), nullable=True))
    op.add_column('mock_test_attempts', sa.Column('draft_answers', sa.JSON(), nullable=True))
    op.add_column('mock_test_attempts', sa.Column('review_marked', sa.JSON(), nullable=True))
    op.add_column('mock_test_attempts', sa.Column('incorrect_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('mock_test_attempts', sa.Column('unanswered_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('mock_test_attempts', sa.Column('time_taken_seconds', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('mock_test_attempts', sa.Column('is_submitted', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    with op.batch_alter_table("mock_test_attempts") as batch_op:
        batch_op.alter_column("score", existing_type=sa.Integer(), type_=sa.Float())
        batch_op.create_foreign_key(
            "fk_mock_test_attempts_user_id", "users",
            ["user_id"], ["id"], ondelete="SET NULL"
        )
    op.create_index(op.f('ix_mock_test_attempts_user_id'), 'mock_test_attempts', ['user_id'], unique=False)

    # 5. pyq_bookmarks table
    op.create_table(
        'pyq_bookmarks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('pyq_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pyq_id'], ['pyqs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'pyq_id', name='uq_user_pyq_bookmark')
    )
    op.create_index(op.f('ix_pyq_bookmarks_id'), 'pyq_bookmarks', ['id'], unique=False)
    op.create_index(op.f('ix_pyq_bookmarks_user_id'), 'pyq_bookmarks', ['user_id'], unique=False)
    op.create_index(op.f('ix_pyq_bookmarks_pyq_id'), 'pyq_bookmarks', ['pyq_id'], unique=False)

    # 6. revision_items table
    op.create_table(
        'revision_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('question_source', sa.String(length=30), nullable=False, server_default='mock_test'),
        sa.Column('question_id', sa.Integer(), nullable=True),
        sa.Column('mock_test_id', sa.String(length=36), nullable=True),
        sa.Column('exam_name', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=True),
        sa.Column('topic', sa.String(length=100), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('selected_answer', sa.String(length=255), nullable=True),
        sa.Column('correct_answer', sa.String(length=255), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('outcome', sa.String(length=30), nullable=False, server_default='incorrect'),
        sa.Column('mistake_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_revised', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('next_review_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'question_text', name='uq_user_revision_question')
    )
    op.create_index(op.f('ix_revision_items_id'), 'revision_items', ['id'], unique=False)
    op.create_index(op.f('ix_revision_items_user_id'), 'revision_items', ['user_id'], unique=False)
    op.create_index(op.f('ix_revision_items_exam_name'), 'revision_items', ['exam_name'], unique=False)
    op.create_index(op.f('ix_revision_items_subject'), 'revision_items', ['subject'], unique=False)
    op.create_index(op.f('ix_revision_items_topic'), 'revision_items', ['topic'], unique=False)
    op.create_index(op.f('ix_revision_items_is_revised'), 'revision_items', ['is_revised'], unique=False)

    # 7. syllabus_topics table
    op.create_table(
        'syllabus_topics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_name', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=False),
        sa.Column('unit_number', sa.Integer(), nullable=True),
        sa.Column('unit_name', sa.String(length=255), nullable=False),
        sa.Column('topic_name', sa.String(length=255), nullable=False),
        sa.Column('subtopics', sa.JSON(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_syllabus_topics_id'), 'syllabus_topics', ['id'], unique=False)
    op.create_index(op.f('ix_syllabus_topics_exam_name'), 'syllabus_topics', ['exam_name'], unique=False)
    op.create_index(op.f('ix_syllabus_topics_subject'), 'syllabus_topics', ['subject'], unique=False)

    # 8. user_syllabus_progress table
    op.create_table(
        'user_syllabus_progress',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='not_started'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_studied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['syllabus_topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'topic_id', name='uq_user_topic_progress')
    )
    op.create_index(op.f('ix_user_syllabus_progress_id'), 'user_syllabus_progress', ['id'], unique=False)
    op.create_index(op.f('ix_user_syllabus_progress_user_id'), 'user_syllabus_progress', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_syllabus_progress_topic_id'), 'user_syllabus_progress', ['topic_id'], unique=False)


def downgrade() -> None:
    op.drop_table('user_syllabus_progress')
    op.drop_table('syllabus_topics')
    op.drop_table('revision_items')
    op.drop_table('pyq_bookmarks')
    op.drop_constraint('fk_mock_test_attempts_user_id', 'mock_test_attempts', type_='foreignkey')
    op.drop_column('mock_test_attempts', 'is_submitted')
    op.drop_column('mock_test_attempts', 'time_taken_seconds')
    op.drop_column('mock_test_attempts', 'unanswered_count')
    op.drop_column('mock_test_attempts', 'incorrect_count')
    op.drop_column('mock_test_attempts', 'review_marked')
    op.drop_column('mock_test_attempts', 'draft_answers')
    op.drop_column('mock_test_attempts', 'user_id')
    op.drop_column('mock_tests', 'negative_marking')
    op.drop_column('mock_tests', 'time_limit_minutes')
    op.drop_column('pyqs', 'is_verified')
    op.drop_column('pyqs', 'language')
    op.drop_column('pyqs', 'source')
    op.drop_column('pyqs', 'topic')
    op.drop_table('users')
