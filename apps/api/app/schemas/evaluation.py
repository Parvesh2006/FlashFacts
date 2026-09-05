from pydantic import BaseModel, ConfigDict


class DatasetSummary(BaseModel):
    name: str
    version: str
    size: int


class ClassificationMetrics(BaseModel):
    accuracy: float = 0.0


class EventTypeMetrics(BaseModel):
    accuracy: float = 0.0


class EntityMetrics(BaseModel):
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0


class ImportanceMetrics(BaseModel):
    mae: float = 0.0
    rmse: float = 0.0


class EnrichmentMetrics(BaseModel):
    success_rate: float = 0.0
    fallback_rate: float = 0.0
    failure_rate: float = 0.0


class LatencyMetrics(BaseModel):
    average_ms: float = 0.0
    median_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0


class EvaluationSummaryResponse(BaseModel):
    dataset: DatasetSummary
    classification: ClassificationMetrics
    event_type: EventTypeMetrics
    entities: EntityMetrics
    importance: ImportanceMetrics
    enrichment: EnrichmentMetrics
    latency: LatencyMetrics

    model_config = ConfigDict(extra="ignore")
