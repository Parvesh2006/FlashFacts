from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from app.models.source import Source
from app.models.ingestion_run import IngestionRun
from app.services.ingestion import IngestionService
from app.services.ai_provider import FallbackAIProvider
from app.repositories.event_repository import EventRepository


def test_identical_document_ingestion_twice(db_session):
    source = Source(
        name="Mock Feed Source",
        url="https://mockfeed.com",
        feed_url="https://mockfeed.com/rss",
        source_type="rss",
        domain="AI",
        reliability_score=0.95,
        enabled=True
    )
    db_session.add(source)
    db_session.commit()

    # Create ingestion runs
    ingestion_run1 = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
    ingestion_run2 = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
    db_session.add_all([ingestion_run1, ingestion_run2])
    db_session.commit()

    mock_entries = [
        {
            "title": "Breakthrough in LLM Reasoning Models",
            "summary": "New AI architecture improves multi-step logic problem solving.",
            "link": "https://mockfeed.com/article-1",
            "published": "Tue, 18 Aug 2026 12:00:00 GMT"
        }
    ]
    mock_feed = MagicMock()
    mock_feed.entries = mock_entries

    service = IngestionService(db_session)

    def mock_fetch(url):
        return mock_feed, 200, None

    with patch.object(service, "fetch_feed", side_effect=mock_fetch):
        metric1 = service.ingest_source(source, ingestion_run1)

        assert metric1.documents_discovered == 1
        assert metric1.documents_accepted == 1
        assert metric1.events_created == 1

        # Run ingestion a SECOND time with identical data -> document duplicate skipped
        metric2 = service.ingest_source(source, ingestion_run2)
        assert metric2.documents_discovered == 1
        assert metric2.documents_accepted == 0
        assert metric2.documents_duplicate == 1
        assert metric2.events_created == 0


def test_same_event_from_multiple_sources_merges_and_preserves_attribution(db_session):
    # Create two sources
    s1 = Source(
        name="Source One",
        url="https://one.example",
        feed_url="https://one.example/rss",
        source_type="rss",
        domain="Politics",
        reliability_score=0.95,
        enabled=True
    )
    s2 = Source(
        name="Source Two",
        url="https://two.example",
        feed_url="https://two.example/rss",
        source_type="rss",
        domain="Politics",
        reliability_score=0.9,
        enabled=True
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    # Create ingestion runs
    ingestion_run1 = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
    ingestion_run2 = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
    db_session.add_all([ingestion_run1, ingestion_run2])
    db_session.commit()

    mock_entries = [
        {
            "title": "Parliament Passes New Infrastructure Bill",
            "summary": "Lawmakers approved a major infrastructure package.",
            "link": "https://one.example/article-1",
            "published": "Tue, 18 Aug 2026 08:00:00 GMT"
        }
    ]
    mock_feed = MagicMock()
    mock_feed.entries = mock_entries

    # Ingest with Source One
    service1 = IngestionService(db_session)

    def mock_fetch1(url):
        return mock_feed, 200, None

    with patch.object(service1, "fetch_feed", side_effect=mock_fetch1):
        res1 = service1.ingest_source(s1, ingestion_run1)
        assert res1.events_created == 1

    # Now simulate the same article appearing on Source Two (same title/content but different URL)
    mock_entries_2 = [
        {
            "title": "Parliament Passes New Infrastructure Bill",
            "summary": "Lawmakers approved a major infrastructure package.",
            "link": "https://two.example/article-dup",
            "published": "Tue, 18 Aug 2026 08:00:00 GMT"
        }
    ]
    mock_feed_2 = MagicMock()
    mock_feed_2.entries = mock_entries_2

    service2 = IngestionService(db_session)

    def mock_fetch2(url):
        return mock_feed_2, 200, None

    with patch.object(service2, "fetch_feed", side_effect=mock_fetch2):
        res2 = service2.ingest_source(s2, ingestion_run2)
        # Should detect same event and link document to existing event
        assert res2.events_deduplicated == 1

    # Verify event has two event_sources linked
    repo = EventRepository(db_session)
    events, total = repo.list_events()
    assert total == 1
    ev = events[0]
    # event_sources relationship should show two sources linked
    assert hasattr(ev, "event_sources")
    assert len(ev.event_sources) >= 2


def test_entity_persistence_and_attachment(db_session):
    s = Source(
        name="Entity Source",
        url="https://entity.example",
        feed_url="https://entity.example/rss",
        source_type="rss",
        domain="Science",
        reliability_score=0.98,
        enabled=True
    )
    db_session.add(s)
    db_session.commit()

    # Create ingestion run
    ingestion_run = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
    db_session.add(ingestion_run)
    db_session.commit()

    mock_entries = [
        {
            "title": "NASA Announces Artemis Mission Milestone",
            "summary": "Artemis program reaches key milestone with successful test.",
            "link": "https://entity.example/article-1",
            "published": "Tue, 18 Aug 2026 10:00:00 GMT"
        }
    ]
    mock_feed = MagicMock()
    mock_feed.entries = mock_entries

    # Provide a mock AI provider that returns entities
    class MockAI:
        def enrich_event(self, title, content, domain, reliability_score=1.0):
            return {
                "summary": title,
                "why_it_matters": "Important.",
                "importance_score": 80,
                "classification": domain,
                "classification_confidence": 0.95,
                "entities": [{"name": "Artemis", "entity_type": "PROGRAM"}]
            }

    service = IngestionService(db_session)

    def mock_fetch(url):
        return mock_feed, 200, None

    with patch.object(service, "fetch_feed", side_effect=mock_fetch):
        # inject mock AI provider
        service.ai_provider = MockAI()
        res = service.ingest_source(s, ingestion_run)
        assert res.events_created == 1

    # Verify entity exists in DB
    repo = EventRepository(db_session)
    events, total = repo.list_events()
    assert total == 1
    ev = events[0]
    # ensure attached entities are present via repository response
    resp = repo.to_event_response(ev)
    assert len(resp.entities) >= 1
    assert any(e.name == "Artemis" for e in resp.entities)


def test_feed_failure_is_handled_and_reported(db_session):
    s = Source(
        name="Bad Feed",
        url="https://bad.example",
        feed_url="https://bad.example/rss",
        source_type="rss",
        domain="Science",
        reliability_score=0.5,
        enabled=True
    )
    db_session.add(s)
    db_session.commit()

    # Create ingestion run
    ingestion_run = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
    db_session.add(ingestion_run)
    db_session.commit()

    service = IngestionService(db_session)

    def mock_fetch_error(url):
        return None, None, "Connection failed"

    with patch.object(service, "fetch_feed", side_effect=mock_fetch_error):
        res = service.ingest_source(s, ingestion_run)
        # Should not crash and should handle the error
        assert res.status == "failed"
        assert res.documents_discovered == 0
