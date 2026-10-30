import logging
import threading
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.schemas.source import SourceCreate, SourceResponse, SourceUpdate
from app.repositories.source_repository import SourceRepository
from app.services.ingestion import IngestionService

logger = logging.getLogger("app")
router = APIRouter(prefix="/sources", tags=["Sources"])

# In-memory lock to prevent overlapping ingestion runs within the process
_INGESTION_LOCK = threading.Lock()


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
def trigger_ingestion(
    background: bool = Query(False, description="Run ingestion in the background and return immediately"),
    source_id: Optional[int] = Query(None, description="Optional ID of a single source to ingest"),
    db: Session = Depends(get_db)
):
    """
    Trigger news ingestion for all enabled sources (or a specific source if source_id is provided).

    - background=False (default): Synchronous execution. Waits for the ingestion run to complete,
      persists all events and source status updates to PostgreSQL, and returns an accurate summary
      including counts and per-source errors.
    - background=True: Runs in a dedicated background worker thread with its own isolated database session.
      Returns immediately with status 'started'.
    - Prevents overlapping ingestion runs by returning HTTP 409 Conflict if another run is currently active.
    """
    if source_id is not None:
        repo = SourceRepository(db)
        if not repo.get_by_id(source_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source with ID {source_id} not found"
            )

    if not _INGESTION_LOCK.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An ingestion run is already in progress. Please wait for the active run to complete."
        )

    if background:
        def _run_in_background():
            bg_db = SessionLocal()
            try:
                logger.info("BACKGROUND_INGESTION_THREAD_STARTED (source_id=%s)", source_id)
                service = IngestionService(bg_db)
                result = service.ingest_all_enabled_sources(source_id=source_id)
                logger.info(
                    "BACKGROUND_INGESTION_THREAD_COMPLETED: status=%s attempted=%s created=%s errors=%s",
                    result.get("status"),
                    result.get("sources_attempted"),
                    result.get("events_created"),
                    result.get("error_count")
                )
            except Exception as e:
                logger.critical("BACKGROUND_INGESTION_THREAD_FAILED: %s", e, exc_info=True)
            finally:
                bg_db.close()
                _INGESTION_LOCK.release()

        thread = threading.Thread(
            target=_run_in_background,
            name="BackgroundIngestionThread",
            daemon=True
        )
        thread.start()
        return {
            "status": "started",
            "message": "Ingestion initiated in background thread. Check GET /api/v1/sources or GET /api/v1/events for updates."
        }

    try:
        service = IngestionService(db)
        summary = service.ingest_all_enabled_sources(source_id=source_id)
        return summary
    except Exception as e:
        logger.error("SYNCHRONOUS_INGESTION_FAILED: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion run failed: {str(e)}"
        )
    finally:
        _INGESTION_LOCK.release()


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    repo = SourceRepository(db)
    source = repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source
