from datetime import date, datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from app.models.event import Event, EventSource
from app.models.document import Document
from app.models.entity import Entity, EventEntity
from app.models.source import Source
from app.models.exam_intelligence import EventExamMetadata, EventExamRelevance
from app.schemas.event import (
    EventCreate,
    DomainStatResponse,
    EventResponse,
    EntityResponse,
    EventExamIntelligenceResponse,
    ExamFactItemResponse,
    ExamRelevanceItemResponse,
)
from app.schemas.source import SourceResponse
from app.utils.hashing import normalize_text, fix_mojibake


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, event_id: int) -> Optional[Event]:
        return (
            self.db.query(Event)
            .options(
                joinedload(Event.event_entities).joinedload(EventEntity.entity),
                joinedload(Event.event_sources),
                joinedload(Event.exam_metadata),
                joinedload(Event.exam_relevances),
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

        # Classify for Exam Intelligence Core on creation
        try:
            from app.services.exam_classification_service import ExamClassificationService
            ExamClassificationService(self.db).classify_event(event)
        except Exception:
            pass

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
        exam: Optional[str] = None,
        geography: Optional[str] = None,
        importance: Optional[str] = None,
        sort: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Event], int]:
        query = (
            self.db.query(Event)
            .options(
                joinedload(Event.event_entities).joinedload(EventEntity.entity),
                joinedload(Event.event_sources),
                joinedload(Event.exam_metadata),
                joinedload(Event.exam_relevances),
            )
        )

        if domain:
            query = query.filter(Event.domain.ilike(domain))
        else:
            # Exclude non-exam domains from default competitive-exam current-affairs feed
            non_exam_domains = ["Entertainment", "Crime", "Lifestyle", "Gossip", "Cinema"]
            query = query.filter(~Event.domain.in_(non_exam_domains))
        if event_date:
            query = query.filter(Event.event_date == event_date)
        if start_date:
            query = query.filter(Event.event_date >= start_date)
        if end_date:
            query = query.filter(Event.event_date <= end_date)

        if exam:
            exam_norm = exam.strip().upper()
            if "TNPSC" in exam_norm:
                exam_type_val = "TNPSC"
            elif "UPSC" in exam_norm:
                exam_type_val = "UPSC"
            elif "SSC" in exam_norm:
                exam_type_val = "SSC"
            elif "BANK" in exam_norm:
                exam_type_val = "BANKING"
            elif "RAILWAY" in exam_norm or "RRB" in exam_norm:
                exam_type_val = "RAILWAY"
            else:
                exam_type_val = "GENERAL_GOVT"

            query = query.join(Event.exam_relevances).filter(
                EventExamRelevance.exam_type == exam_type_val,
                EventExamRelevance.relevance_level.in_(["VERY_HIGH", "HIGH", "MEDIUM"])
            )
            non_exam_domains = ["Entertainment", "Crime", "Lifestyle", "Gossip", "Cinema"]
            query = query.filter(~Event.domain.in_(non_exam_domains))

        if geography:
            geo_norm = geography.strip().upper()
            query = query.join(Event.exam_metadata).filter(
                or_(
                    EventExamMetadata.geographic_level.ilike(geo_norm),
                    EventExamMetadata.primary_state.ilike(f"%{geography.strip()}%")
                )
            )

        if importance:
            imp_norm = importance.strip().upper()
            query = query.join(Event.exam_metadata).filter(
                EventExamMetadata.exam_importance.ilike(imp_norm)
            )

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
        exam: Optional[str] = None,
        geography: Optional[str] = None,
        importance: Optional[str] = None,
        sort: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Event], int]:
        query = (
            self.db.query(Event)
            .options(
                joinedload(Event.event_entities).joinedload(EventEntity.entity),
                joinedload(Event.event_sources),
                joinedload(Event.exam_metadata),
                joinedload(Event.exam_relevances),
            )
        )
        # Strict Unicode-aware keyword filtering.
        # Match every meaningful query term against event metadata.
        import re

        stop_words = {
            "a", "an", "the", "is", "are", "was", "were",
            "in", "on", "at", "of", "for", "to", "from",
            "and", "or", "with", "about", "what", "which",
            "who", "how", "me", "tell", "show", "find",
            "give", "latest", "news", "current", "affairs",
            "today", "event", "events",
        }
        terms = list(dict.fromkeys(
            term for term in re.findall(
                r"[^\W_]+", query_text.casefold(), flags=re.UNICODE
            )
            if term not in stop_words and len(term) > 1
        ))
        if not terms:
            terms = [query_text.strip()]

        for term in terms:
            variants = [term]
            tamil_plural_suffix = "\u0b99\u0bcd\u0b95\u0bb3\u0bcd"
            if term.endswith(tamil_plural_suffix) and len(term) > 5:
                variants.append(term[:-5])

            term_conditions = []
            for variant in variants:
                pattern = f"%{variant}%"
                term_conditions.extend([
                    Event.title.ilike(pattern),
                    Event.summary.ilike(pattern),
                    Event.domain.ilike(pattern),
                ])
            query = query.filter(or_(*term_conditions))

        if domain:
            query = query.filter(Event.domain.ilike(domain))
        if event_date:
            query = query.filter(Event.event_date == event_date)
        if start_date:
            query = query.filter(Event.event_date >= start_date)
        if end_date:
            query = query.filter(Event.event_date <= end_date)

        if exam:
            exam_norm = exam.strip().upper()
            exam_type_val = "TNPSC" if "TNPSC" in exam_norm else ("UPSC" if "UPSC" in exam_norm else ("SSC" if "SSC" in exam_norm else ("BANK" in exam_norm and "BANKING" or ("RAILWAY" if "RAILWAY" in exam_norm else "GENERAL_GOVT"))))
            query = query.join(Event.exam_relevances).filter(
                EventExamRelevance.exam_type == exam_type_val,
                EventExamRelevance.relevance_level.in_(["VERY_HIGH", "HIGH", "MEDIUM"])
            )
            non_exam_domains = ["Entertainment", "Crime", "Lifestyle", "Gossip", "Cinema"]
            query = query.filter(~Event.domain.in_(non_exam_domains))

        if geography:
            query = query.join(Event.exam_metadata).filter(
                or_(
                    EventExamMetadata.geographic_level.ilike(geography.strip()),
                    EventExamMetadata.primary_state.ilike(f"%{geography.strip()}%")
                )
            )

        if importance:
            query = query.join(Event.exam_metadata).filter(
                EventExamMetadata.exam_importance.ilike(importance.strip())
            )

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

        source_objs = []
        try:
            source_ids = set()
            if hasattr(event, "event_sources") and event.event_sources:
                for es in event.event_sources:
                    if getattr(es, "source_id", None):
                        source_ids.add(es.source_id)
            if getattr(event, "source_id", None):
                source_ids.add(event.source_id)
            if source_ids:
                source_objs = self.db.query(Source).filter(Source.id.in_(list(source_ids))).all()
        except Exception:
            source_objs = []

        primary_source = next(
            (s for s in source_objs if s.id == event.source_id),
            None,
        )

        source_name = ""
        if primary_source and primary_source.name:
            source_name = primary_source.name
        elif hasattr(event, "source") and event.source and getattr(event.source, "name", None):
            source_name = event.source.name
        elif source_objs and getattr(source_objs[0], "name", None):
            source_name = source_objs[0].name
        else:
            source_name = "FlashFacts Intelligence Network"

        # Exam Intelligence Resolution
        exam_intel_resp = None
        try:
            from app.services.exam_classification_service import ExamClassificationService
            meta = getattr(event, "exam_metadata", None)
            relevances = getattr(event, "exam_relevances", None)

            if not meta or not relevances:
                # Classify on demand for existing events
                meta, relevances = ExamClassificationService(self.db).classify_event(event)

            fact_items = [
                ExamFactItemResponse(
                    label=f.get("label", f.get("fact_type", "Fact")),
                    value=f.get("value", f.get("fact_statement", ""))
                )
                for f in (meta.exam_facts if meta else [])
            ]
            rel_items = [
                ExamRelevanceItemResponse(
                    exam_type=r.exam_type,
                    relevance_level=r.relevance_level,
                    relevance_score=r.relevance_score,
                    explanation=getattr(r, "why_relevant", getattr(r, "explanation", None)),
                )
                for r in (relevances or [])
            ]

            exam_intel_resp = EventExamIntelligenceResponse(
                exam_importance=meta.exam_importance if meta else "USEFUL",
                geographic_level=meta.geographic_level if meta else "INDIA",
                primary_state=meta.primary_state if meta else None,
                why_it_matters=meta.why_it_matters if meta else None,
                exam_facts=fact_items,
                question_angles=meta.question_angles if meta else [],
                relevances=rel_items,
            )
        except Exception as e:
            import logging
            logging.exception("Error building exam_intelligence response: %s", e)
            exam_intel_resp = None
        resp_dict = {
            "id": event.id,
            "title": event.title or "",
            "summary": event.summary or "",
            "domain": event.domain,
            "event_type": event.event_type,
            "event_date": event.event_date,
            "published_at": published_at,
            "source_id": event.source_id,
            "source_url": event.source_url,
            "source": source_name,
            "url": event.source_url,
            "confidence_score": event.confidence_score,
            "dedup_hash": event.dedup_hash,
            "why_it_matters": event.why_it_matters or "",
            "importance_score": event.importance_score,
            "classification_confidence": event.classification_confidence,
            "ai_processed_at": event.ai_processed_at,
            "processing_status": event.processing_status,
            "entities": entities_list,
            "source_count": source_count,
            "sources": source_objs,
            "exam_intelligence": exam_intel_resp,
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
