"""Add geographic location and event relation tables."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "006_geographic_and_relations"
down_revision: Union[str, None] = "005_event_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "geographic_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("location_type", sa.String(length=50), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("geographic_locations.id"), nullable=True),
        sa.Column("country_code", sa.String(length=10), nullable=True),
        sa.Column("state_code", sa.String(length=10), nullable=True),
        sa.Column("district_code", sa.String(length=20), nullable=True),
        sa.Column("aliases_json", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_geographic_locations_id", "geographic_locations", ["id"], unique=False)
    op.create_index("ix_geographic_locations_name", "geographic_locations", ["name"], unique=False)
    op.create_index("ix_geographic_locations_norm_name", "geographic_locations", ["normalized_name"], unique=False)
    op.create_index("ix_geographic_locations_type", "geographic_locations", ["location_type"], unique=False)
    op.create_index("ix_geographic_locations_parent_id", "geographic_locations", ["parent_id"], unique=False)

    op.create_table(
        "event_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("geographic_locations.id"), nullable=False),
        sa.Column("relation_type", sa.String(length=50), nullable=False, server_default="PRIMARY"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_locations_id", "event_locations", ["id"], unique=False)
    op.create_index("ix_event_locations_event_id", "event_locations", ["event_id"], unique=False)
    op.create_index("ix_event_locations_location_id", "event_locations", ["location_id"], unique=False)
    op.create_index("ix_event_locations_event_loc", "event_locations", ["event_id", "location_id"], unique=True)

    op.create_table(
        "event_relations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("target_event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("relation_type", sa.String(length=50), nullable=False, server_default="RELATED_TO"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_relations_id", "event_relations", ["id"], unique=False)
    op.create_index("ix_event_relations_source_event_id", "event_relations", ["source_event_id"], unique=False)
    op.create_index("ix_event_relations_target_event_id", "event_relations", ["target_event_id"], unique=False)
    op.create_index("ix_event_relations_pair", "event_relations", ["source_event_id", "target_event_id"], unique=True)


def downgrade() -> None:
    op.drop_table("event_relations")
    op.drop_table("event_locations")
    op.drop_table("geographic_locations")

