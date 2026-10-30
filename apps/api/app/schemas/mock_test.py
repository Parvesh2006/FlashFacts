from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class MockTestCreate(BaseModel):
    exam_name: str
    domain: Optional[str] = None
    language: str = "en"
    difficulty: str = "medium"
    total_questions: int = Field(10, ge=1, le=200)
    time_limit_minutes: int = Field(30, ge=5, le=180)
    negative_marking: Optional[float] = None
    include_pyqs: bool = True
    include_events: bool = True


class MockTestQuestionSchema(BaseModel):
    id: int
    question_order: int
    is_pyq: bool
    pyq_id: Optional[int] = None
    event_id: Optional[int] = None
    question_text: str
    options: List[str]


class MockTestSummary(BaseModel):
    id: str
    exam_name: str
    title: Optional[str] = None
    domain: Optional[str] = None
    subject: Optional[str] = None
    template_key: Optional[str] = None
    language: str
    difficulty: str
    total_questions: int
    time_limit_minutes: int
    negative_marking: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MockTestResponse(BaseModel):
    id: str
    exam_name: str
    title: Optional[str] = None
    domain: Optional[str] = None
    language: str
    difficulty: str
    total_questions: int
    time_limit_minutes: int
    negative_marking: float
    status: str
    created_at: datetime
    updated_at: datetime
    questions: Optional[List[MockTestQuestionSchema]] = None

    class Config:
        from_attributes = True


class MockTestAnswerReview(BaseModel):
    question_id: int
    question_order: int
    question_text: str
    options: List[str]
    selected_answer: Optional[str] = None
    correct_answer: str
    is_correct: bool
    explanation: Optional[str] = None


class MockTestAttemptCreate(BaseModel):
    answers: Dict[str, str]  # question_id (str) -> answer (str like "A", "B", "C", "D")
    time_taken_seconds: int = 0
    review_marked: Optional[List[int]] = None


class DraftAttemptRequest(BaseModel):
    draft_answers: Dict[str, str]
    review_marked: Optional[List[int]] = None
    time_taken_seconds: int = 0


class MockTestAttemptResponse(BaseModel):
    id: str
    test_id: str
    user_id: Optional[str] = None
    score: float
    accuracy: int
    total_answered: int
    incorrect_count: int
    unanswered_count: int
    time_taken_seconds: int
    is_submitted: bool
    submitted_at: datetime
    review: List[MockTestAnswerReview] = Field(default_factory=list)


class MockTestAttemptSummary(BaseModel):
    id: str
    test_id: str
    exam_name: str
    score: float
    accuracy: int
    total_answered: int
    total_questions: int
    time_taken_seconds: int
    submitted_at: datetime

    class Config:
        from_attributes = True
