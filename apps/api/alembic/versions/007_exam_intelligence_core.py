"""Add exam intelligence core metadata and exam relevance tables."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "007_exam_intelligence_core"
down_revision: Union[str, None] = "006_geographic_and_relations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_exam_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("exam_importance", sa.String(length=50), nullable=False, server_default="USEFUL"),
        sa.Column("geographic_level", sa.String(length=50), nullable=False, server_default="INDIA"),
        sa.Column("primary_state", sa.String(length=100), nullable=True),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("exam_facts_json", sa.Text(), nullable=True, server_default="[]"),
        sa.Column("question_angles_json", sa.Text(), nullable=True, server_default="[]"),
        sa.Column("relevance_factors_json", sa.Text(), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index("ix_event_exam_metadata_id", "event_exam_metadata", ["id"], unique=False)
    op.create_index("ix_event_exam_metadata_event_id", "event_exam_metadata", ["event_id"], unique=True)
    op.create_index("ix_event_exam_metadata_importance", "event_exam_metadata", ["exam_importance"], unique=False)
    op.create_index("ix_event_exam_metadata_geo_level", "event_exam_metadata", ["geographic_level"], unique=False)
    op.create_index("ix_event_exam_metadata_primary_state", "event_exam_metadata", ["primary_state"], unique=False)

    op.create_table(
        "event_exam_relevance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("exam_type", sa.String(length=50), nullable=False),
        sa.Column("relevance_level", sa.String(length=50), nullable=False, server_default="MEDIUM"),
        sa.Column("relevance_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_exam_relevance_id", "event_exam_relevance", ["id"], unique=False)
    op.create_index("ix_event_exam_relevance_event_id", "event_exam_relevance", ["event_id"], unique=False)
    op.create_index("ix_event_exam_relevance_exam_type", "event_exam_relevance", ["exam_type"], unique=False)
    op.create_index("ix_event_exam_relevance_rel_level", "event_exam_relevance", ["relevance_level"], unique=False)
    op.create_index("ix_event_exam_relevance_rel_score", "event_exam_relevance", ["relevance_score"], unique=False)
    op.create_index("ix_event_exam_relevance_event_exam", "event_exam_relevance", ["event_id", "exam_type"], unique=True)


def downgrade() -> None:
    op.drop_table("event_exam_relevance")
    op.drop_table("event_exam_metadata")

