from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class EventRelation(Base):
    __tablename__ = "event_relations"

    id = Column(Integer, primary_key=True, index=True)
    source_event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    target_event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    relation_type = Column(String(50), nullable=False, default="RELATED_TO", index=True)
    # RELATED_TO, PRECEDES, FOLLOWS, CAUSES, CAUSED_BY, UPDATE_OF, SAME_STORY, PART_OF
    confidence_score = Column(Float, nullable=False, default=1.0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    source_event = relationship("Event", foreign_keys=[source_event_id])
    target_event = relationship("Event", foreign_keys=[target_event_id])


Index("ix_event_relations_pair", EventRelation.source_event_id, EventRelation.target_event_id, unique=True)

