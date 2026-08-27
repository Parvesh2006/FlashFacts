from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    domain = Column(String(100), nullable=False, index=True)
    event_date = Column(Date, nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    source_url = Column(String(1024), nullable=False)
    confidence_score = Column(Float, nullable=False, default=1.0)
    dedup_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Phase 3A AI Intelligence Enrichment Fields
    why_it_matters = Column(Text, nullable=True)
    importance_score = Column(Integer, nullable=False, default=50, index=True)
    classification_confidence = Column(Float, nullable=False, default=1.0)
    ai_processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_status = Column(String(50), nullable=False, default="completed", index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    source = relationship("Source", back_populates="events")
    event_sources = relationship("EventSource", back_populates="event", cascade="all, delete-orphan")
    event_entities = relationship("EventEntity", back_populates="event", cascade="all, delete-orphan")


class EventSource(Base):
    __tablename__ = "event_sources"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    event = relationship("Event", back_populates="event_sources")
    document = relationship("Document", back_populates="event_sources")
