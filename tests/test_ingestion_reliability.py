from unittest.mock import MagicMock, patch

import httpx

from app.models.ingestion_run import IngestionRun
from app.models.source import Source
from app.services.ingestion import IngestionService


def _source(db_session, name, feed_url):
    source = Source(
        name=name,
        url=feed_url,
        feed_url=feed_url,
        source_type="rss",
        domain="Science",
        enabled=True,
    )
    db_session.add(source)
    db_session.commit()
    return source


def _run(db_session):
    run = IngestionRun()
    db_session.add(run)
    db_session.commit()
    return run


def _client_for(responses):
    client = MagicMock()
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    client.get.side_effect = responses
    return client


def test_fetch_retries_timeout_then_recovers(monkeypatch):
    service = IngestionService(MagicMock())
    response = MagicMock(status_code=200, content=b"<rss><channel></channel></rss>")
    client = _client_for([httpx.ReadTimeout("timed out"), response])
    monkeypatch.setattr("app.services.ingestion.httpx.Client", MagicMock(return_value=client))
    monkeypatch.setattr("app.services.ingestion.time.sleep", lambda _: None)

    feed, status, error = service.fetch_feed("https://example.test/feed")

    assert feed is not None
    assert status == 200
    assert error is None
    assert client.get.call_count == 2


def test_fetch_does_not_retry_permanent_error(monkeypatch):
    service = IngestionService(MagicMock())
    response = MagicMock(status_code=404, content=b"")
    client = _client_for([response])
    monkeypatch.setattr("app.services.ingestion.httpx.Client", MagicMock(return_value=client))
    monkeypatch.setattr("app.services.ingestion.time.sleep", lambda _: None)

    feed, status, error = service.fetch_feed("https://example.test/missing")

    assert feed is None
    assert status == 404
    assert "HTTP 404" in error
    assert client.get.call_count == 1


def test_malformed_feed_is_reported_without_crashing(monkeypatch):
    service = IngestionService(MagicMock())
    response = MagicMock(status_code=200, content=b"not a feed")
    client = _client_for([response])
    monkeypatch.setattr("app.services.ingestion.httpx.Client", MagicMock(return_value=client))

    feed, status, error = service.fetch_feed("https://example.test/broken")

    assert feed is None
    assert status == 200
    assert error == "Malformed or empty feed"


def test_source_failure_does_not_stop_other_sources(db_session):
    failed = _source(db_session, "Failed", "https://failed.test/feed")
    healthy = _source(db_session, "Healthy", "https://healthy.test/feed")
    feed = MagicMock()
    feed.entries = [{
        "title": "A science discovery",
        "summary": "A useful research result.",
        "link": "https://healthy.test/item",
        "guid": "healthy-1",
        "published": "Tue, 18 Aug 2026 12:00:00 GMT",
    }]
    service = IngestionService(db_session)

    def fetch(url):
        if url == failed.feed_url:
            return None, 503, "HTTP 503 fetching feed"
        return feed, 200, None

    with patch.object(service, "fetch_feed", side_effect=fetch):
        result = service.ingest_all_enabled_sources()

    assert result["sources_attempted"] == 2
    assert result["sources_succeeded"] == 1
    assert result["sources_failed"] == 1
    assert result["documents_ingested"] == 1
    assert healthy.last_error is None
