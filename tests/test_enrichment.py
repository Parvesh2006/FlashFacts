from datetime import date, datetime, timezone

from app.models.entity import Entity
from app.models.event import Event
from app.models.source import Source
from app.services.enrichment import EventEnrichmentService


class ValidProvider:
    def enrich_event(self, title, content, domain, reliability_score=1.0):
        assert len(content) <= 6000
        return {
            "summary": "NASA launched a lunar mission.",
            "why_it_matters": "The mission advances lunar science.",
            "importance_score": 88,
            "classification": "Science",
            "classification_confidence": 0.92,
            "event_type": "Launch",
            "entities": [
                {"name": "NASA", "entity_type": "ORGANIZATION"},
                {"name": "Invented Entity", "entity_type": "ORGANIZATION"},
            ],
        }


class InvalidProvider:
    def enrich_event(self, *args, **kwargs):
        return {"importance_score": 400, "classification_confidence": 2.0}


class RaisingProvider:
    def enrich_event(self, *args, **kwargs):
        raise TimeoutError("provider timeout")


def make_event(db_session, title="NASA launches lunar mission", status="pending"):
    source = db_session.query(Source).filter(Source.feed_url == "https://science.test/rss").first()
    if not source:
        source = Source(
            name="Science Source", url="https://science.test", feed_url="https://science.test/rss",
            source_type="rss", domain="Science", reliability_score=0.9,
        )
        db_session.add(source)
        db_session.flush()
    event = Event(
        title=title,
        summary="NASA reported a lunar mission launch.",
        domain="Science",
        event_date=date(2026, 9, 4),
        published_at=datetime.now(timezone.utc),
        source_id=source.id,
        source_url="https://science.test/item",
        dedup_hash=title.lower().replace(" ", "-") + status,
        processing_status=status,
    )
    db_session.add(event)
    db_session.commit()
    return event


def test_successful_enrichment_validates_and_grounds_entities(db_session):
    event = make_event(db_session)
    result = EventEnrichmentService(db_session, ValidProvider()).enrich_event(event)

    assert result.importance_score == 88
    assert result.classification_confidence == 0.92
    assert event.event_type == "Launch"
    assert [link.entity.name for link in event.event_entities] == ["NASA"]


def test_invalid_provider_output_falls_back_and_bounds_values(db_session):
    event = make_event(db_session)
    result = EventEnrichmentService(db_session, InvalidProvider()).enrich_event(event)

    assert result.used_fallback is True
    assert 0 <= result.importance_score <= 100
    assert 0 <= result.classification_confidence <= 1
    assert event.processing_status == "failed"


def test_provider_failure_does_not_break_event(db_session):
    event = make_event(db_session)
    result = EventEnrichmentService(db_session, RaisingProvider()).enrich_event(event)

    assert result.used_fallback is True
    assert event.summary
    assert event.processing_status == "failed"


def test_batch_skips_completed_and_continues_after_failure(db_session):
    completed = make_event(db_session, "Completed event", "completed")
    pending = make_event(db_session, "Pending event", "pending")
    service = EventEnrichmentService(db_session, RaisingProvider())
    result = service.enrich_batch(limit=20)

    assert result["requested"] == 1
    assert result["failed"] == 1
    assert completed.processing_status == "completed"
    assert pending.processing_status == "failed"


def test_duplicate_entities_are_not_created(db_session):
    event = make_event(db_session)
    service = EventEnrichmentService(db_session, ValidProvider())
    service.enrich_event(event)
    service.enrich_event(event, force=True)

    assert db_session.query(Entity).filter(Entity.name == "NASA").count() == 1


def test_long_input_is_bounded(db_session):
    event = make_event(db_session, "Long event")
    event.summary = "x" * 20000
    db_session.commit()
    EventEnrichmentService(db_session, ValidProvider()).enrich_event(event)


def test_batch_enrichment_endpoint(client):
    response = client.post("/api/v1/events/enrich?limit=5")

    assert response.status_code == 200
    assert "processed" in response.json()
    assert "duration_ms" in response.json()