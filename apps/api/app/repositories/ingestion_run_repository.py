from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.ingestion_run import IngestionRun


class IngestionRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> IngestionRun:
        """Create a new ingestion run."""
        run = IngestionRun(**kwargs)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_by_id(self, run_id: int) -> Optional[IngestionRun]:
        """Get an ingestion run by ID."""
        return self.db.query(IngestionRun).filter(IngestionRun.id == run_id).first()

    def list_runs(self, limit: int = 100, offset: int = 0) -> List[IngestionRun]:
        """List recent ingestion runs."""
        return self.db.query(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(limit).offset(offset).all()

    def list_completed_runs(self, limit: int = 100, offset: int = 0) -> List[IngestionRun]:
        """List completed ingestion runs."""
        return (
            self.db.query(IngestionRun)
            .filter(IngestionRun.status == "completed")
            .order_by(IngestionRun.started_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_latest_run(self) -> Optional[IngestionRun]:
        """Get the most recent ingestion run."""
        return self.db.query(IngestionRun).order_by(IngestionRun.started_at.desc()).first()

    def update(self, run_id: int, **kwargs) -> Optional[IngestionRun]:
        """Update an ingestion run."""
        run = self.get_by_id(run_id)
        if run:
            for key, value in kwargs.items():
                setattr(run, key, value)
            self.db.commit()
            self.db.refresh(run)
        return run
