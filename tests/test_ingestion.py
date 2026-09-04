from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from app.models.source import Source
from app.models.ingestion_run import IngestionRun
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

    # Create an ingestion run
    ingestion_run = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
    db_session.add(ingestion_run)
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

    # Patch fetch_feed to return the parsed tuple format
    def mock_fetch(url):
        return mock_feed, 200, None

    with patch.object(service, "fetch_feed", side_effect=mock_fetch):
        metric = service.ingest_source(source, ingestion_run)

        assert metric.documents_discovered == 1
        assert metric.documents_accepted == 1
        assert metric.events_created == 1
        assert metric.status == "success"

        # Run ingestion a SECOND time with identical data -> document duplicate skipped!
        ingestion_run2 = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
        db_session.add(ingestion_run2)
        db_session.commit()

        metric_repeat = service.ingest_source(source, ingestion_run2)
        assert metric_repeat.documents_discovered == 1
        assert metric_repeat.documents_accepted == 0
        assert metric_repeat.documents_duplicate == 1
        assert metric_repeat.events_created == 0
        assert metric_repeat.status == "success"
