import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

    id = Column(Integer, primary_key=True, index=True)
    exam_name = Column(String(100), nullable=False, index=True)
    subject = Column(String(100), nullable=False, index=True)
    unit_number = Column(Integer, nullable=True)
    unit_name = Column(String(255), nullable=False)
    topic_name = Column(String(255), nullable=False)
    subtopics = Column(JSON, nullable=True)  # list of subtopic strings
    order_index = Column(Integer, nullable=False, default=0)

    progress_entries = relationship("UserSyllabusProgress", back_populates="topic", cascade="all, delete-orphan")


class UserSyllabusProgress(Base):
    __tablename__ = "user_syllabus_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("syllabus_topics.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(30), nullable=False, default="not_started")  # not_started, in_progress, completed, needs_revision
    notes = Column(Text, nullable=True)
    last_studied_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    topic = relationship("SyllabusTopic", back_populates="progress_entries")

    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_topic_progress"),
    )
