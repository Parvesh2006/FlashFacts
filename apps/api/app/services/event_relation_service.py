"""
Event Relation & Timeline Service.
"""
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.event import Event
from app.models.event_relation import EventRelation

logger = logging.getLogger("app")


class EventRelationService:
    """Service for managing relationships between events and event timelines."""

    def __init__(self, db: Session):
        self.db = db

    def create_relation(
        self,
        source_event_id: int,
        target_event_id: int,
        relation_type: str = "RELATED_TO",
        confidence_score: float = 1.0,
    ) -> Optional[EventRelation]:
        """Create a relationship between two events."""
        if source_event_id == target_event_id:
            return None

        existing = self.db.query(EventRelation).filter(
            EventRelation.source_event_id == source_event_id,
            EventRelation.target_event_id == target_event_id,
        ).first()

        if existing:
            return existing

        relation = EventRelation(
            source_event_id=source_event_id,
            target_event_id=target_event_id,
            relation_type=relation_type,
            confidence_score=confidence_score,
        )
        self.db.add(relation)
        self.db.commit()
        self.db.refresh(relation)
        return relation

    def get_related_events(self, event_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Return related events linked to a target event."""
        relations = self.db.query(EventRelation).filter(
            or_(
                EventRelation.source_event_id == event_id,
                EventRelation.target_event_id == event_id,
            )
        ).limit(limit).all()

        related_ids = []
        for rel in relations:
            other_id = rel.target_event_id if rel.source_event_id == event_id else rel.source_event_id
            related_ids.append((other_id, rel.relation_type, rel.confidence_score))

        if not related_ids:
            # Fallback: find events in same domain close in date
            target = self.db.query(Event).filter(Event.id == event_id).first()
            if target:
                domain_events = self.db.query(Event).filter(
                    Event.domain == target.domain,
                    Event.id != target.id,
                ).order_by(Event.event_date.desc()).limit(limit).all()

                return [
                    {
                        "event_id": e.id,
                        "title": e.title,
                        "domain": e.domain,
                        "event_date": e.event_date.isoformat(),
                        "relation_type": "RELATED_TO",
                        "confidence_score": 0.7,
                    }
                    for e in domain_events
                ]
            return []

        ids = [item[0] for item in related_ids]
        events_map = {e.id: e for e in self.db.query(Event).filter(Event.id.in_(ids)).all()}

        result = []
        for other_id, rel_type, conf in related_ids:
            ev = events_map.get(other_id)
            if ev:
                result.append({
                    "event_id": ev.id,
                    "title": ev.title,
                    "domain": ev.domain,
                    "event_date": ev.event_date.isoformat(),
                    "relation_type": rel_type,
                    "confidence_score": conf,
                })

        return result

    def get_event_timeline(self, event_id: int) -> Dict[str, Any]:
        """Return chronological timeline context around an event."""
        target_event = self.db.query(Event).filter(Event.id == event_id).first()
        if not target_event:
            return {"event_id": event_id, "timeline": []}

        # Query preceding and subsequent events in same domain
        preceding = self.db.query(Event).filter(
            Event.domain == target_event.domain,
            Event.event_date <= target_event.event_date,
            Event.id != target_event.id,
        ).order_by(Event.event_date.desc()).limit(3).all()

        subsequent = self.db.query(Event).filter(
            Event.domain == target_event.domain,
            Event.event_date >= target_event.event_date,
            Event.id != target_event.id,
        ).order_by(Event.event_date.asc()).limit(3).all()

        timeline = []
        for p in reversed(preceding):
            timeline.append({
                "event_id": p.id,
                "title": p.title,
                "event_date": p.event_date.isoformat(),
                "position": "PRECEDING",
                "relation_type": "PREVIOUS_DEVELOPMENT",
            })

        timeline.append({
            "event_id": target_event.id,
            "title": target_event.title,
            "event_date": target_event.event_date.isoformat(),
            "position": "CURRENT",
            "relation_type": "TARGET_EVENT",
        })

        for s in subsequent:
            timeline.append({
                "event_id": s.id,
                "title": s.title,
                "event_date": s.event_date.isoformat(),
                "position": "SUBSEQUENT",
                "relation_type": "SUBSEQUENT_DEVELOPMENT",
            })

        return {
            "event_id": event_id,
            "domain": target_event.domain,
            "timeline": timeline,
        }

