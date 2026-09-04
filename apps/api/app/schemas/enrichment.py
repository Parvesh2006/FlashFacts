from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


ALLOWED_ENTITY_TYPES = {
    "PERSON", "ORGANIZATION", "COUNTRY", "LOCATION", "EVENT",
    "TECHNOLOGY", "PRODUCT", "PROGRAM", "CONCEPT",
}


class EnrichmentEntity(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    entity_type: str = Field(
        default="CONCEPT",
        max_length=50,
        validation_alias=AliasChoices("entity_type", "type"),
    )

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("entity_type")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        return normalized if normalized in ALLOWED_ENTITY_TYPES else "CONCEPT"


class EventEnrichment(BaseModel):
    summary: str = Field(default="", max_length=2000)
    why_it_matters: Optional[str] = Field(default=None, max_length=2000)
    importance_score: int = Field(default=50, ge=0, le=100)
    classification: str = Field(min_length=1, max_length=100)
    classification_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    event_type: Optional[str] = Field(default=None, max_length=100)
    entities: List[EnrichmentEntity] = Field(default_factory=list, max_length=30)
    provider: str = "fallback"
    used_fallback: bool = False

    model_config = ConfigDict(extra="ignore")