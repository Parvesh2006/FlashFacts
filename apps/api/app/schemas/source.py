from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SourceBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "TechCrunch"})
    url: str = Field(..., json_schema_extra={"example": "https://techcrunch.com"})
    feed_url: str = Field(..., json_schema_extra={"example": "https://techcrunch.com/feed/"})
    source_type: str = Field("rss", json_schema_extra={"example": "rss"})
    domain: str = Field("General", json_schema_extra={"example": "Technology"})
    reliability_score: float = Field(1.0, ge=0.0, le=1.0)
    enabled: bool = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    feed_url: Optional[str] = None
    source_type: Optional[str] = None
    domain: Optional[str] = None
    reliability_score: Optional[float] = None
    enabled: Optional[bool] = None
    last_ingested_at: Optional[datetime] = None


class SourceResponse(SourceBase):
    id: int
    last_ingested_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
