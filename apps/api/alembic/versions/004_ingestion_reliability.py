"""Add ingestion reliability metadata and feed item identity."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_ingestion_reliability"
down_revision: Union[str, None] = "003_ingestion_tracking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("sources") as batch_op:
        batch_op.add_column(sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("last_error", sa.String(length=1024), nullable=True))
    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(sa.Column("source_guid", sa.String(length=1024), nullable=True))
        batch_op.create_index("ix_documents_source_guid", ["source_guid"], unique=False)
        batch_op.alter_column("published_at", existing_type=sa.DateTime(timezone=True), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column("published_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.drop_index("ix_documents_source_guid")
        batch_op.drop_column("source_guid")
    with op.batch_alter_table("sources") as batch_op:
        batch_op.drop_column("last_error")
        batch_op.drop_column("last_attempted_at")
