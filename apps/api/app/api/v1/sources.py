from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.source import SourceCreate, SourceResponse, SourceUpdate
from app.repositories.source_repository import SourceRepository
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("", response_model=List[SourceResponse])
def list_sources(
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: Session = Depends(get_db)
):
    repo = SourceRepository(db)
    return repo.list_sources(enabled_only=bool(enabled) if enabled is not None else False)


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(
    source_in: SourceCreate,
    db: Session = Depends(get_db)
):
    repo = SourceRepository(db)
    existing = repo.get_by_feed_url(source_in.feed_url)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source with feed URL '{source_in.feed_url}' already exists."
        )
    return repo.create(source_in)


@router.post("/ingest")
def trigger_ingestion(db: Session = Depends(get_db)):
    service = IngestionService(db)
    return service.ingest_all_enabled_sources()


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    repo = SourceRepository(db)
    source = repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source
