from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.source import SourceResponse


class EntityResponse(BaseModel):
    id: int
    name: str
    entity_type: str

    model_config = ConfigDict(from_attributes=True)


class EventBase(BaseModel):
    title: str
    summary: str
    domain: str
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


class EventCreate(EventBase):
    dedup_hash: str


class EventResponse(EventBase):
    id: int
    dedup_hash: str
    entities: List[EntityResponse] = Field(default_factory=list)
    source_count: int = 1
    sources: List[SourceResponse] = Field(default_factory=list)
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
