from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.source import SourceResponse
from app.schemas.domain import validate_exam_domain


class EntityResponse(BaseModel):
    id: int
    name: str
    entity_type: str

    model_config = ConfigDict(from_attributes=True)


class ExamRelevanceItemResponse(BaseModel):
    exam_type: str
    relevance_level: str
    relevance_score: int
    explanation: Optional[str] = None


class ExamFactItemResponse(BaseModel):
    label: str
    value: str


class EventExamIntelligenceResponse(BaseModel):
    exam_importance: Optional[str] = "USEFUL"
    geographic_level: Optional[str] = "INDIA"
    primary_state: Optional[str] = None
    why_it_matters: Optional[str] = None
    exam_facts: List[ExamFactItemResponse] = Field(default_factory=list)
    question_angles: List[str] = Field(default_factory=list)
    relevances: List[ExamRelevanceItemResponse] = Field(default_factory=list)


class EventBase(BaseModel):
    title: str
    summary: str
    domain: str
    event_type: Optional[str] = None
    event_date: date
    published_at: datetime
    source_id: int
    source_url: str
    confidence_score: float = 1.0

    # Phase 3A AI Intelligence Enrichment
    why_it_matters: Optional[str] = None
    importance_score: int = 50
    classification_confidence: float = 1.0
    ai_processed_at: Optional[datetime] = None
    processing_status: str = "completed"

    # News Relevance & Syllabus Quality Fields
    is_exam_eligible: bool = True
    rejection_reason: Optional[str] = None
    inclusion_reason: Optional[str] = None
    syllabus_topic: Optional[str] = None


class EventCreate(EventBase):
    dedup_hash: str

    @field_validator("domain")
    @classmethod
    def domain_must_be_exam_oriented(cls, value: str) -> str:
        return validate_exam_domain(value)


class EventResponse(EventBase):
    id: int
    source: str
    url: str
    dedup_hash: str
    entities: List[EntityResponse] = Field(default_factory=list)
    source_count: int = 1
    sources: List[SourceResponse] = Field(default_factory=list)
    exam_intelligence: Optional[EventExamIntelligenceResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    events: List[EventResponse]


class DomainStatResponse(BaseModel):
    domain: str
    count: int
