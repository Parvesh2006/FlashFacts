"""Add pyq_papers table for genuine examination question paper PDFs

Revision ID: 011_pyq_papers
Revises: 010_exam_portal_features
Create Date: 2026-10-23 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '011_pyq_papers'
down_revision: Union[str, None] = '010_exam_portal_features'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pyq_papers',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('exam_name', sa.String(length=100), nullable=False),
        sa.Column('exam_category', sa.String(length=50), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('exam_date', sa.Date(), nullable=True),
        sa.Column('subject', sa.String(length=150), nullable=False),
        sa.Column('language', sa.String(length=20), server_default='en', nullable=False),
        sa.Column('shift_session', sa.String(length=50), nullable=True),
        sa.Column('paper_code', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('storage_path', sa.Text(), nullable=True),
        sa.Column('pdf_url', sa.Text(), nullable=True),
        sa.Column('authority', sa.String(length=200), nullable=False),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=True),
        sa.Column('verification_status', sa.String(length=30), server_default='verified_official', nullable=False),
        sa.Column('redistribution_status', sa.String(length=50), server_default='official_open_access', nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(length=50), server_default='application/pdf', nullable=False),
        sa.Column('availability_status', sa.String(length=30), server_default='available', nullable=False),
        sa.Column('download_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pyq_papers_id'), 'pyq_papers', ['id'], unique=False)
    op.create_index(op.f('ix_pyq_papers_exam_name'), 'pyq_papers', ['exam_name'], unique=False)
    op.create_index(op.f('ix_pyq_papers_exam_category'), 'pyq_papers', ['exam_category'], unique=False)
    op.create_index(op.f('ix_pyq_papers_year'), 'pyq_papers', ['year'], unique=False)
    op.create_index(op.f('ix_pyq_papers_subject'), 'pyq_papers', ['subject'], unique=False)
    op.create_index(op.f('ix_pyq_papers_language'), 'pyq_papers', ['language'], unique=False)
    op.create_index(op.f('ix_pyq_papers_paper_code'), 'pyq_papers', ['paper_code'], unique=False)
    op.create_index(op.f('ix_pyq_papers_checksum_sha256'), 'pyq_papers', ['checksum_sha256'], unique=False)
    op.create_index('ix_pyq_papers_exam_year', 'pyq_papers', ['exam_name', 'year'], unique=False)
    op.create_index('ix_pyq_papers_category_year', 'pyq_papers', ['exam_category', 'year'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_pyq_papers_category_year', table_name='pyq_papers')
    op.drop_index('ix_pyq_papers_exam_year', table_name='pyq_papers')
    op.drop_index(op.f('ix_pyq_papers_checksum_sha256'), table_name='pyq_papers')
    op.drop_index(op.f('ix_pyq_papers_paper_code'), table_name='pyq_papers')
    op.drop_index(op.f('ix_pyq_papers_language'), table_name='pyq_papers')
    op.drop_index(op.f('ix_pyq_papers_subject'), table_name='pyq_papers')
    op.drop_index(op.f('ix_pyq_papers_year'), table_name='pyq_papers')
    op.drop_index(op.f('ix_pyq_papers_exam_category'), table_name='pyq_papers')
    op.drop_index(op.f('ix_pyq_papers_exam_name'), table_name='pyq_papers')
    op.drop_index(op.f('ix_pyq_papers_id'), table_name='pyq_papers')
    op.drop_table('pyq_papers')
