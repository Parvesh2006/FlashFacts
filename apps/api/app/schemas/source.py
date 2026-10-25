from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.domain import validate_exam_domain


class SourceBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "TechCrunch"})
    url: str = Field(..., json_schema_extra={"example": "https://techcrunch.com"})
    feed_url: str = Field(..., json_schema_extra={"example": "https://techcrunch.com/feed/"})
    source_type: str = Field("rss", json_schema_extra={"example": "rss"})
    domain: str = Field("Technology", json_schema_extra={"example": "Technology"})
    reliability_score: float = Field(1.0, ge=0.0, le=1.0)
    enabled: bool = True


class SourceCreate(SourceBase):
    @field_validator("domain")
    @classmethod
    def domain_must_be_exam_oriented(cls, value: str) -> str:
        return validate_exam_domain(value)


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    feed_url: Optional[str] = None
    source_type: Optional[str] = None
    domain: Optional[str] = None
    reliability_score: Optional[float] = None
    enabled: Optional[bool] = None
    last_ingested_at: Optional[datetime] = None

    @field_validator("domain")
    @classmethod
    def domain_must_be_exam_oriented(cls, value: Optional[str]) -> Optional[str]:
        return validate_exam_domain(value) if value is not None else value


class SourceResponse(SourceBase):
    id: int
    last_ingested_at: Optional[datetime] = None
    last_attempted_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
