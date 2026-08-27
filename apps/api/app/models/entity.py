from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # PERSON, ORGANIZATION, COUNTRY, TECHNOLOGY, PROGRAM, CONCEPT
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    event_entities = relationship("EventEntity", back_populates="entity", cascade="all, delete-orphan")


class EventEntity(Base):
    __tablename__ = "event_entities"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    event = relationship("Event", back_populates="event_entities")
    entity = relationship("Entity", back_populates="event_entities")
