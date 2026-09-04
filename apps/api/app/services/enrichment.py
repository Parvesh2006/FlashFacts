import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.entity import Entity, EventEntity
from app.repositories.event_repository import EventRepository
from app.schemas.enrichment import EventEnrichment
from app.services.ai_provider import AIProvider, FallbackAIProvider, get_ai_provider
from app.utils.hashing import normalize_text

logger = logging.getLogger("app")


class EventEnrichmentService:
    def __init__(self, db: Session, provider: Optional[AIProvider] = None):
        self.db = db
        self.provider = provider or get_ai_provider()
        self.event_repo = EventRepository(db)

    def enrich_event(self, event: Event, force: bool = False) -> EventEnrichment:
        if event.processing_status == "completed" and not force:
            return EventEnrichment(
                summary=event.summary or event.title,
                why_it_matters=event.why_it_matters,
                importance_score=event.importance_score,
                classification=event.domain,
                classification_confidence=event.classification_confidence,
                event_type=event.event_type,
                provider="existing",
            )

        event.processing_status = "processing"
        self.db.commit()
        content = self._bounded_content(event)
        try:
            raw = self.provider.enrich_event(
                title=event.title,
                content=content,
                domain=event.domain,
                reliability_score=event.source.reliability_score if event.source else 1.0,
            )
            enrichment = EventEnrichment.model_validate(raw)
            enrichment = self._ground_and_normalize(enrichment, event)
            self._persist(event, enrichment)
            return enrichment
        except Exception as exc:
            self.db.rollback()
            logger.warning("Event enrichment failed: event_id=%s error=%s", event.id, exc)
            fallback = FallbackAIProvider().enrich_event(
                event.title, content, event.domain,
                event.source.reliability_score if event.source else 1.0,
            )
            enrichment = EventEnrichment.model_validate({
                **fallback,
                "provider": "fallback",
                "used_fallback": True,
            })
            self._persist(event, enrichment, status="failed")
            return enrichment

    def enrich_batch(self, limit: int = 20, force: bool = False) -> Dict[str, Any]:
        started_at = time.perf_counter()
        query = self.db.query(Event).order_by(Event.id.asc())
        if not force:
            query = query.filter(Event.processing_status != "completed")
        events = query.limit(max(1, limit)).all()
        result = {
            "requested": len(events), "processed": 0, "succeeded": 0,
            "failed": 0, "fallback": 0, "skipped": 0,
        }
        for event in events:
            try:
                enrichment = self.enrich_event(event, force=force)
                result["processed"] += 1
                if enrichment.used_fallback:
                    result["fallback"] += 1
                    result["failed"] += 1
                else:
                    result["succeeded"] += 1
            except Exception:
                self.db.rollback()
                result["failed"] += 1
                logger.exception("Batch enrichment failed: event_id=%s", event.id)
        result["duration_ms"] = round((time.perf_counter() - started_at) * 1000, 2)
        return result

    def _bounded_content(self, event: Event) -> str:
        from app.core.config import settings
        document_content = " ".join(
            source.document.content
            for source in event.event_sources
            if source.document and source.document.content
        )
        source_text = " ".join(filter(None, [event.title, event.summary, document_content]))
        return source_text[:settings.AI_MAX_INPUT_CHARS]

    def _ground_and_normalize(self, enrichment: EventEnrichment, event: Event) -> EventEnrichment:
        source_text = normalize_text(f"{event.title} {self._bounded_content(event)}")
        grounded_entities = [
            entity for entity in enrichment.entities
            if normalize_text(entity.name) in source_text
        ]
        return enrichment.model_copy(update={
            "summary": enrichment.summary or event.title,
            "classification": enrichment.classification or event.domain,
            "entities": grounded_entities,
        })

    def _persist(self, event: Event, enrichment: EventEnrichment, status: str = "completed") -> None:
        event.summary = enrichment.summary[:2000]
        event.why_it_matters = enrichment.why_it_matters
        event.importance_score = enrichment.importance_score
        event.domain = enrichment.classification
        event.event_type = enrichment.event_type
        event.classification_confidence = enrichment.classification_confidence
        event.ai_processed_at = datetime.now(timezone.utc)
        event.processing_status = status
        self.db.commit()
        if enrichment.entities:
            self.event_repo.attach_entities(
                event.id,
                [entity.model_dump() for entity in enrichment.entities],
            )