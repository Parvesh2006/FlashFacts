from datetime import date, datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from app.models.event import Event, EventSource
from app.models.document import Document
from app.models.entity import Entity, EventEntity
from app.schemas.event import EventCreate, DomainStatResponse, EventResponse, EntityResponse
from app.models.source import Source
from app.schemas.source import SourceResponse
from app.utils.hashing import normalize_text
from datetime import timezone

class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, event_id: int) -> Optional[Event]:
        return (
            self.db.query(Event)
            .options(
                joinedload(Event.event_entities).joinedload(EventEntity.entity),
                joinedload(Event.event_sources)
            )
            .filter(Event.id == event_id)
            .first()
        )

    def get_by_dedup_hash(self, dedup_hash: str) -> Optional[Event]:
        return self.db.query(Event).filter(Event.dedup_hash == dedup_hash).first()

    def create(self, event_in: EventCreate, document_id: Optional[int] = None) -> Event:
        event = Event(**event_in.model_dump())
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        if document_id:
            event_source = EventSource(
                event_id=event.id,
                document_id=document_id,
                source_id=event.source_id
            )
            self.db.add(event_source)
            self.db.commit()

        return event

    def add_event_source(self, event_id: int, document_id: int, source_id: int) -> EventSource:
        event_source = EventSource(
            event_id=event_id,
            document_id=document_id,
            source_id=source_id
        )
        self.db.add(event_source)
        self.db.commit()
        self.db.refresh(event_source)
        return event_source

    def attach_entities(self, event_id: int, entities_data: List[Dict[str, str]]) -> List[Entity]:
        attached_entities = []
        for ent_data in entities_data:
            name = ent_data.get("name", "").strip()
            ent_type = ent_data.get("entity_type", "CONCEPT").strip()
            if not name:
                continue

            normalized_name = normalize_text(name)
            entity = next(
                (
                    candidate for candidate in self.db.query(Entity).all()
                    if normalize_text(candidate.name) == normalized_name
                ),
                None,
            )
            if not entity:
                entity = Entity(name=name, entity_type=ent_type)
                self.db.add(entity)
                self.db.commit()
                self.db.refresh(entity)

            existing_link = (
                self.db.query(EventEntity)
                .filter(EventEntity.event_id == event_id, EventEntity.entity_id == entity.id)
                .first()
            )
            if not existing_link:
                link = EventEntity(event_id=event_id, entity_id=entity.id)
                self.db.add(link)
                self.db.commit()

            attached_entities.append(entity)
        return attached_entities

    def list_events(
        self,
        domain: Optional[str] = None,
        event_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Event], int]:
        query = (
            self.db.query(Event)
            .options(
                joinedload(Event.event_entities).joinedload(EventEntity.entity),
                joinedload(Event.event_sources)
            )
        )

        if domain:
            query = query.filter(Event.domain.ilike(domain))
        if event_date:
            query = query.filter(Event.event_date == event_date)
        if start_date:
            query = query.filter(Event.event_date >= start_date)
        if end_date:
            query = query.filter(Event.event_date <= end_date)

        total = query.count()

        if sort == "important":
            query = query.order_by(Event.importance_score.desc(), Event.published_at.desc())
        else:
            query = query.order_by(Event.published_at.desc(), Event.event_date.desc())

        events = query.offset(offset).limit(limit).all()
        return events, total

    def search_events(
        self,
        query_text: str,
        domain: Optional[str] = None,
        event_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Event], int]:
        query = (
            self.db.query(Event)
            .options(
                joinedload(Event.event_entities).joinedload(EventEntity.entity),
                joinedload(Event.event_sources),
            )
        )
        pattern = f"%{query_text.strip()}%"
        query = query.filter(
            or_(
                Event.title.ilike(pattern),
                Event.summary.ilike(pattern),
                Event.domain.ilike(pattern),
                Event.source_url.ilike(pattern),
                Event.event_sources.any(
                    EventSource.document.has(Document.content.ilike(pattern))
                ),
            )
        )

        if domain:
            query = query.filter(Event.domain.ilike(domain))
        if event_date:
            query = query.filter(Event.event_date == event_date)
        if start_date:
            query = query.filter(Event.event_date >= start_date)
        if end_date:
            query = query.filter(Event.event_date <= end_date)

        total = query.count()
        if sort == "important":
            query = query.order_by(Event.importance_score.desc(), Event.published_at.desc())
        else:
            query = query.order_by(Event.published_at.desc(), Event.event_date.desc())

        return query.offset(offset).limit(limit).all(), total

    def to_event_response(self, event: Event) -> EventResponse:
        published_at = event.published_at
        if published_at is not None and published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        entities_list = []
        if hasattr(event, "event_entities") and event.event_entities:
            for ee in event.event_entities:
                if ee.entity:
                    entities_list.append(
                        EntityResponse(
                            id=ee.entity.id,
                            name=ee.entity.name,
                            entity_type=ee.entity.entity_type
                        )
                    )

        source_count = 1
        if hasattr(event, "event_sources") and event.event_sources:
            source_count = max(1, len(event.event_sources))

        # Collect unique sources attributed to this event via event_sources
        source_objs = []
        try:
            source_ids = set()
            if hasattr(event, "event_sources") and event.event_sources:
                for es in event.event_sources:
                    if getattr(es, "source_id", None):
                        source_ids.add(es.source_id)
            # ensure primary event.source_id is included
            if getattr(event, "source_id", None):
                source_ids.add(event.source_id)
            if source_ids:
                source_objs = self.db.query(Source).filter(Source.id.in_(list(source_ids))).all()
        except Exception:
            source_objs = []

        primary_source = next(
            (source for source in source_objs if source.id == event.source_id),
            None,
        )

        resp_dict = {
            "id": event.id,
            "title": event.title,
            "summary": event.summary,
            "domain": event.domain,
            "event_type": event.event_type,
            "event_date": event.event_date,
            "published_at": published_at,
            "source_id": event.source_id,
            "source_url": event.source_url,
            "source": primary_source.name if primary_source else "",
            "url": event.source_url,
            "confidence_score": event.confidence_score,
            "dedup_hash": event.dedup_hash,
            "why_it_matters": event.why_it_matters,
            "importance_score": event.importance_score,
            "classification_confidence": event.classification_confidence,
            "ai_processed_at": event.ai_processed_at,
            "processing_status": event.processing_status,
            "entities": entities_list,
            "source_count": source_count,
            "sources": source_objs,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }
        return EventResponse(**resp_dict)

    def get_domain_counts(self) -> List[DomainStatResponse]:
        results = self.db.query(
            Event.domain, func.count(Event.id)
        ).group_by(Event.domain).all()
        return [DomainStatResponse(domain=r[0], count=r[1]) for r in results]

    def get_events_for_month(self, year: int, month: int) -> List[Event]:
        start_dt = date(year, month, 1)
        if month == 12:
            end_dt = date(year + 1, 1, 1)
        else:
            end_dt = date(year, month + 1, 1)
        return self.db.query(Event).filter(
            Event.event_date >= start_dt,
            Event.event_date < end_dt
        ).all()
