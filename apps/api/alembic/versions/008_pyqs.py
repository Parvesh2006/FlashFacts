"""Add PYQ model

Revision ID: 008_pyqs
Revises: 007_exam_intelligence_core
Create Date: 2026-10-09 21:24:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008_pyqs'
down_revision = '007_exam_intelligence_core'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('pyqs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_name', sa.String(length=100), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('paper_name', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=100), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('correct_answer', sa.String(length=255), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pyqs_exam_name'), 'pyqs', ['exam_name'], unique=False)
    op.create_index(op.f('ix_pyqs_id'), 'pyqs', ['id'], unique=False)
    op.create_index(op.f('ix_pyqs_subject'), 'pyqs', ['subject'], unique=False)
    op.create_index(op.f('ix_pyqs_year'), 'pyqs', ['year'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_pyqs_year'), table_name='pyqs')
    op.drop_index(op.f('ix_pyqs_subject'), table_name='pyqs')
    op.drop_index(op.f('ix_pyqs_id'), table_name='pyqs')
    op.drop_index(op.f('ix_pyqs_exam_name'), table_name='pyqs')
    op.drop_table('pyqs')
