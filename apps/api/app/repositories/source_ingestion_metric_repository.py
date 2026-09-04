from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.source_ingestion_metric import SourceIngestionMetric


class SourceIngestionMetricRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> SourceIngestionMetric:
        """Create a new source ingestion metric."""
        metric = SourceIngestionMetric(**kwargs)
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def get_by_id(self, metric_id: int) -> Optional[SourceIngestionMetric]:
        """Get a metric by ID."""
        return self.db.query(SourceIngestionMetric).filter(SourceIngestionMetric.id == metric_id).first()

    def list_by_ingestion_run(self, ingestion_run_id: int) -> List[SourceIngestionMetric]:
        """Get all metrics for a specific ingestion run."""
        return (
            self.db.query(SourceIngestionMetric)
            .filter(SourceIngestionMetric.ingestion_run_id == ingestion_run_id)
            .order_by(SourceIngestionMetric.started_at)
            .all()
        )

    def list_by_source(self, source_id: int, limit: int = 100) -> List[SourceIngestionMetric]:
        """Get recent metrics for a specific source."""
        return (
            self.db.query(SourceIngestionMetric)
            .filter(SourceIngestionMetric.source_id == source_id)
            .order_by(SourceIngestionMetric.started_at.desc())
            .limit(limit)
            .all()
        )

    def update(self, metric_id: int, **kwargs) -> Optional[SourceIngestionMetric]:
        """Update a metric."""
        metric = self.get_by_id(metric_id)
        if metric:
            for key, value in kwargs.items():
                setattr(metric, key, value)
            self.db.commit()
            self.db.refresh(metric)
        return metric
