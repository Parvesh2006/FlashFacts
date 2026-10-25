from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class PYQBase(BaseModel):
    exam_name: str
    year: int
    paper_name: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    source: Optional[str] = None
    language: str = "en"
    is_verified: bool = True
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None


class PYQCreate(PYQBase):
    pass


class PYQResponse(PYQBase):
    id: int
    is_bookmarked: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PYQFiltersResponse(BaseModel):
    exams: List[str]
    years: List[int]
    subjects: List[str]
    topics: List[str]
    total_count: int


class PYQBookmarkResponse(BaseModel):
    pyq_id: int
    bookmarked: bool
    message: str
