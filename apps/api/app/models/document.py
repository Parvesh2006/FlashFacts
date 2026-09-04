from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(1024), nullable=False)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    source_guid = Column(String(1024), nullable=True, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    crawled_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    processed = Column(Boolean, nullable=False, default=False)

    source = relationship("Source", back_populates="documents")
    event_sources = relationship("EventSource", back_populates="document", cascade="all, delete-orphan")
