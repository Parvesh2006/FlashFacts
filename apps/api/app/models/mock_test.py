import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class MockTest(Base):
    __tablename__ = "mock_tests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    exam_name = Column(String(100), nullable=False)
    domain = Column(String(100), nullable=True)
    language = Column(String(10), nullable=False, default="en")
    difficulty = Column(String(20), nullable=False, default="medium")
    total_questions = Column(Integer, nullable=False, default=10)
    time_limit_minutes = Column(Integer, nullable=False, default=30)
    negative_marking = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="generating")  # generating, ready, completed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    questions = relationship("MockTestQuestion", back_populates="test", cascade="all, delete-orphan", order_by="MockTestQuestion.question_order")
    attempts = relationship("MockTestAttempt", back_populates="test", cascade="all, delete-orphan")


class MockTestQuestion(Base):
    __tablename__ = "mock_test_questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String(36), ForeignKey("mock_tests.id"), nullable=False)
    question_order = Column(Integer, nullable=False)

    is_pyq = Column(Boolean, default=False)
    pyq_id = Column(Integer, ForeignKey("pyqs.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)

    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)
    correct_answer = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=True)
    reference_url = Column(String(512), nullable=True)

    test = relationship("MockTest", back_populates="questions")


class MockTestAttempt(Base):
    __tablename__ = "mock_test_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    test_id = Column(String(36), ForeignKey("mock_tests.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    answers = Column(JSON, nullable=False)  # dict of question_id -> selected_answer
    draft_answers = Column(JSON, nullable=True)  # in-progress draft answers
    review_marked = Column(JSON, nullable=True)  # list of question IDs marked for review

    score = Column(Float, nullable=False, default=0.0)  # can be float due to negative marking
    accuracy = Column(Integer, nullable=False, default=0)
    total_answered = Column(Integer, nullable=False, default=0)
    incorrect_count = Column(Integer, nullable=False, default=0)
    unanswered_count = Column(Integer, nullable=False, default=0)
    time_taken_seconds = Column(Integer, nullable=False, default=0)
    is_submitted = Column(Boolean, nullable=False, default=True)

    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    test = relationship("MockTest", back_populates="attempts")
