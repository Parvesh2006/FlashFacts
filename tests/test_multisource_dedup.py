from unittest.mock import patch, MagicMock
from app.models.source import Source
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
    with patch.object(service, "fetch_feed", return_value=mock_feed):
        stats = service.ingest_source(source)

        assert stats["discovered"] == 1
        assert stats["documents_stored"] == 1
        assert stats["events_created"] == 1

        # Run ingestion a SECOND time with identical data -> document duplicate skipped
        stats_repeat = service.ingest_source(source)
        assert stats_repeat["discovered"] == 1
        assert stats_repeat["documents_stored"] == 0
        assert stats_repeat["skipped"] == 1
        assert stats_repeat["events_created"] == 0


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
    with patch.object(service1, "fetch_feed", return_value=mock_feed):
        res1 = service1.ingest_source(s1)
        assert res1["events_created"] == 1

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
    with patch.object(service2, "fetch_feed", return_value=mock_feed_2):
        res2 = service2.ingest_source(s2)
        # Should detect same event and link document to existing event
        assert res2["events_deduplicated"] == 1

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
    with patch.object(service, "fetch_feed", return_value=mock_feed):
        # inject mock AI provider
        service.ai_provider = MockAI()
        res = service.ingest_source(s)
        assert res["events_created"] == 1

    # Verify entity exists in DB
    from app.repositories.event_repository import EventRepository
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

    service = IngestionService(db_session)
    with patch.object(service, "fetch_feed", return_value=None):
        res = service.ingest_source(s)
        # Should not crash and should set last_ingested_at
        assert res["discovered"] == 0