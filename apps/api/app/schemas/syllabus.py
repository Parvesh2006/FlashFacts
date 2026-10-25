from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class SyllabusTopicResponse(BaseModel):
    id: int
    exam_name: str
    subject: str
    unit_number: Optional[int] = None
    unit_name: str
    topic_name: str
    subtopics: Optional[List[str]] = None
    order_index: int
    status: str = "not_started"  # not_started, in_progress, completed, needs_revision
    notes: Optional[str] = None
    last_studied_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SyllabusUnitGroup(BaseModel):
    unit_number: Optional[int] = None
    unit_name: str
    subject: str
    topics: List[SyllabusTopicResponse]
    completed_count: int
    total_count: int
    completion_percentage: int


class SyllabusSubjectGroup(BaseModel):
    subject: str
    units: List[SyllabusUnitGroup]
    completed_count: int
    total_count: int
    completion_percentage: int


class ExamSyllabusResponse(BaseModel):
    exam_name: str
    overall_completion_percentage: int
    total_topics: int
    completed_topics: int
    in_progress_topics: int
    needs_revision_topics: int
    subjects: List[SyllabusSubjectGroup]


class UpdateTopicProgressRequest(BaseModel):
    topic_id: int
    status: str  # "not_started", "in_progress", "completed", "needs_revision"
    notes: Optional[str] = None


class TopicProgressResponse(BaseModel):
    topic_id: int
    status: str
    notes: Optional[str] = None
    last_studied_at: Optional[datetime] = None
    message: str
