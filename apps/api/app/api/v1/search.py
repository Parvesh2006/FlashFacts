from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventListResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=EventListResponse)
def search_events(
    q: str = Query(..., min_length=1),
    domain: Optional[str] = Query(None),
    date: Optional[date] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    exam: Optional[str] = Query(None),
    geography: Optional[str] = Query(None),
    importance: Optional[str] = Query(None),
    sort: Optional[str] = Query("latest"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    repo = EventRepository(db)
    events, total = repo.search_events(
        query_text=q,
        domain=domain,
        event_date=date,
        start_date=start_date,
        end_date=end_date,
        exam=exam,
        geography=geography,
        importance=importance,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return EventListResponse(
        total=total,
        limit=limit,
        offset=offset,
        events=[repo.to_event_response(event) for event in events],
    )