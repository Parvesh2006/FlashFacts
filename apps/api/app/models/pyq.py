from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.core.database import Base


class PYQ(Base):
    __tablename__ = "pyqs"

    id = Column(Integer, primary_key=True, index=True)
    exam_name = Column(String(100), nullable=False, index=True)  # e.g., "TNPSC Group 4"
    year = Column(Integer, nullable=False, index=True)
    paper_name = Column(String(255), nullable=True)
    subject = Column(String(100), nullable=True, index=True)
    topic = Column(String(100), nullable=True, index=True)
    source = Column(String(255), nullable=True)
    language = Column(String(10), nullable=False, default="en")
    is_verified = Column(Boolean, nullable=False, default=True)

    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # list of string options
    correct_answer = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
