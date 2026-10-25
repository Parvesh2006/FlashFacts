from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class RevisionItemResponse(BaseModel):
    id: str
    question_source: str
    question_id: Optional[int] = None
    mock_test_id: Optional[str] = None
    exam_name: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    question_text: str
    options: List[str]
    selected_answer: Optional[str] = None
    correct_answer: str
    explanation: Optional[str] = None
    outcome: str
    mistake_count: int
    is_revised: bool
    next_review_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SaveRevisionRequest(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    exam_name: str = "TNPSC Group 4"
    subject: Optional[str] = None
    topic: Optional[str] = None
    question_source: str = "manual"
    selected_answer: Optional[str] = None


class RetryRevisionRequest(BaseModel):
    selected_answer: str  # "A", "B", "C", "D" or full option text


class RetryRevisionResponse(BaseModel):
    id: str
    is_correct: bool
    selected_letter: Optional[str] = None
    correct_letter: str
    mistake_count: int
    is_revised: bool
    next_review_at: Optional[datetime] = None
    explanation: Optional[str] = None


class UpdateRevisionStatusRequest(BaseModel):
    is_revised: bool


class RevisionSummaryResponse(BaseModel):
    total_count: int
    pending_count: int
    revised_count: int
    exams: List[str]
    subjects: List[str]
