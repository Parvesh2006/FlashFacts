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
    exam: Optional[str] = Query(None, description="Filter by exam category (e.g. TNPSC, UPSC, SSC, BANKING, RAILWAY, GENERAL_GOVT)"),
    geography: Optional[str] = Query(None, description="Filter by geographic scope (e.g. TN, INDIA, INTERNATIONAL)"),
    importance: Optional[str] = Query(None, description="Filter by exam importance (e.g. MUST_KNOW, IMPORTANT, USEFUL, BACKGROUND)"),
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
        exam=exam,
        geography=geography,
        importance=importance,
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


@router.get("/{event_id}/exam-relevance")
def get_event_exam_relevance(event_id: int, db: Session = Depends(get_db)):
    from app.services.exam_intelligence import ExamIntelligenceService
    service = ExamIntelligenceService(db)
    result = service.get_event_exam_relevance(event_id)
    if not result.get("relevant_exams") and not result.get("key_points"):
        # Still return the structure, not a 404
        pass
    return result


@router.get("/{event_id}/mcq")
def get_event_mcq(
    event_id: int,
    exam_id: Optional[str] = Query(None),
    count: int = Query(3, ge=1, le=5),
    db: Session = Depends(get_db),
):
    from app.services.exam_intelligence import ExamIntelligenceService
    service = ExamIntelligenceService(db)
    result = service.generate_mcqs(event_id, exam_id=exam_id, count=count)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


@router.get("/{event_id}/timeline")
def get_event_timeline(event_id: int, db: Session = Depends(get_db)):
    from app.services.event_relation_service import EventRelationService
    service = EventRelationService(db)
    return service.get_event_timeline(event_id)


@router.get("/{event_id}/location")
def get_event_location(event_id: int, db: Session = Depends(get_db)):
    from app.models.location import EventLocation
    from app.services.location_service import LocationService
    repo = EventRepository(db)
    event = repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    service = LocationService(db)
    service.attach_locations_to_event(event)
    locs = db.query(EventLocation).filter(EventLocation.event_id == event.id).all()
    return {
        "event_id": event.id,
        "locations": [
            {
                "id": el.location.id,
                "name": el.location.name,
                "location_type": el.location.location_type,
                "relation_type": el.relation_type,
                "confidence": el.confidence,
            }
            for el in locs if el.location
        ],
    }


