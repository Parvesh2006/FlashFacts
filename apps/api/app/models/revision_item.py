import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint
from app.core.database import Base


class RevisionItem(Base):
    __tablename__ = "revision_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    question_source = Column(String(30), nullable=False, default="mock_test")  # "mock_test", "pyq", "manual"
    question_id = Column(Integer, nullable=True)
    mock_test_id = Column(String(36), nullable=True)

    exam_name = Column(String(100), nullable=False, index=True)
    subject = Column(String(100), nullable=True, index=True)
    topic = Column(String(100), nullable=True, index=True)

    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)
    selected_answer = Column(String(255), nullable=True)
    correct_answer = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=True)

    outcome = Column(String(30), nullable=False, default="incorrect")  # "incorrect", "skipped", "saved"
    mistake_count = Column(Integer, nullable=False, default=1)
    is_revised = Column(Boolean, nullable=False, default=False, index=True)

    next_review_at = Column(DateTime(timezone=True), nullable=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "question_text", name="uq_user_revision_question"),
    )
