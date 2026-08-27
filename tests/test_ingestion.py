from unittest.mock import patch, MagicMock
from app.models.source import Source
from app.services.ingestion import IngestionService


def test_ingestion_service_with_mock_feed(db_session):
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

        # Run ingestion a SECOND time with identical data -> document duplicate skipped!
        stats_repeat = service.ingest_source(source)
        assert stats_repeat["discovered"] == 1
        assert stats_repeat["documents_stored"] == 0
        assert stats_repeat["skipped"] == 1
        assert stats_repeat["events_created"] == 0
