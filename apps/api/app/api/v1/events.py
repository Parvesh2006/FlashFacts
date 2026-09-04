from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.event import EventResponse, EventListResponse
from app.repositories.event_repository import EventRepository
from app.services.enrichment import EventEnrichmentService

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/enrich")
def enrich_events(
    limit: int = Query(20, ge=1, le=200),
    force: bool = Query(False),
    db: Session = Depends(get_db),
):
    return EventEnrichmentService(db).enrich_batch(limit=limit, force=force)


@router.get("", response_model=EventListResponse)
def list_events(
    domain: Optional[str] = Query(None, description="Filter by domain category"),
    date: Optional[date] = Query(None, description="Filter by exact event date (YYYY-MM-DD)"),
    start_date: Optional[date] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date filter (YYYY-MM-DD)"),
    sort: Optional[str] = Query("latest", description="Sort order: 'latest' or 'important'"),
    limit: int = Query(50, ge=1, le=200, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    repo = EventRepository(db)
    events, total = repo.list_events(
        domain=domain,
        event_date=date,
        start_date=start_date,
        end_date=end_date,
        sort=sort,
        limit=limit,
        offset=offset
    )
    return EventListResponse(
        total=total,
        limit=limit,
        offset=offset,
        events=[repo.to_event_response(e) for e in events]
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    repo = EventRepository(db)
    event = repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return repo.to_event_response(event)
