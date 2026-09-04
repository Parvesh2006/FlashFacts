from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="running", index=True)

    # Aggregate metrics
    sources_attempted = Column(Integer, nullable=False, default=0)
    sources_succeeded = Column(Integer, nullable=False, default=0)
    sources_failed = Column(Integer, nullable=False, default=0)

    documents_discovered = Column(Integer, nullable=False, default=0)
    documents_accepted = Column(Integer, nullable=False, default=0)
    documents_duplicate = Column(Integer, nullable=False, default=0)

    events_created = Column(Integer, nullable=False, default=0)
    events_deduplicated = Column(Integer, nullable=False, default=0)

    processing_time_ms = Column(Float, nullable=False, default=0.0)
    error_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    source_metrics = relationship("SourceIngestionMetric", back_populates="ingestion_run", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        # Ensure all integer fields have default values
        if 'sources_attempted' not in kwargs:
            kwargs['sources_attempted'] = 0
        if 'sources_succeeded' not in kwargs:
            kwargs['sources_succeeded'] = 0
        if 'sources_failed' not in kwargs:
            kwargs['sources_failed'] = 0
        if 'documents_discovered' not in kwargs:
            kwargs['documents_discovered'] = 0
        if 'documents_accepted' not in kwargs:
            kwargs['documents_accepted'] = 0
        if 'documents_duplicate' not in kwargs:
            kwargs['documents_duplicate'] = 0
        if 'events_created' not in kwargs:
            kwargs['events_created'] = 0
        if 'events_deduplicated' not in kwargs:
            kwargs['events_deduplicated'] = 0
        if 'processing_time_ms' not in kwargs:
            kwargs['processing_time_ms'] = 0.0
        if 'error_count' not in kwargs:
            kwargs['error_count'] = 0
        if 'status' not in kwargs:
            kwargs['status'] = 'running'
        if 'started_at' not in kwargs:
            kwargs['started_at'] = datetime.now(timezone.utc)
        super().__init__(**kwargs)
