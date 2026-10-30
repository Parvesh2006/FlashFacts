"""Add last_verified_at column to pyq_papers

Revision ID: 012_pyq_verification_fields
Revises: 011_pyq_papers
Create Date: 2026-10-26 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '012_pyq_verification_fields'
down_revision: Union[str, None] = '011_pyq_papers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_verified_at if not present
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('pyq_papers')]
    if 'last_verified_at' not in cols:
        op.add_column(
            'pyq_papers',
            sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('pyq_papers')]
    if 'last_verified_at' in cols:
        op.drop_column('pyq_papers', 'last_verified_at')
