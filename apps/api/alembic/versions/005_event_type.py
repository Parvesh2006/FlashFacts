"""Add structured event type for enrichment output."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005_event_type"
down_revision: Union[str, None] = "004_ingestion_reliability"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("events") as batch_op:
        batch_op.add_column(sa.Column("event_type", sa.String(length=100), nullable=True))
        batch_op.create_index("ix_events_event_type", ["event_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_index("ix_events_event_type")
        batch_op.drop_column("event_type")