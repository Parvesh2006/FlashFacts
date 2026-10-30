import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.source import Source
from app.models.document import Document
from app.models.event import Event
from app.models.ingestion_run import IngestionRun
from app.models.source_ingestion_metric import SourceIngestionMetric
from app.services.ingestion import IngestionService
from app.services.news_relevance_service import NewsRelevanceService
from app.services.location_service import LocationService
from app.services.extraction import EventExtractorService
from app.services.deduplication import DeduplicationService
from app.repositories.event_repository import EventRepository
from app.repositories.source_repository import SourceRepository
from app.repositories.document_repository import DocumentRepository
from app.utils.hashing import compute_content_hash, compute_event_dedup_hash


# =========================================================================
# 1. RSS Fetching, Parsing & Error Handling Tests
# =========================================================================

def test_fetch_feed_parses_valid_xml():
    """Verify fetch_feed parses valid RSS XML correctly."""
    service = IngestionService(MagicMock())
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Test Feed</title>
        <link>https://example.com</link>
        <item>
          <title>ISRO Launches Navigation Satellite</title>
          <link>https://example.com/isro-launch</link>
          <description>ISRO has successfully placed the satellite into GTO.</description>
          <pubDate>Mon, 30 Oct 2026 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>"""

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = xml_data.encode("utf-8")
    mock_resp.text = xml_data

    with patch("httpx.Client.get", return_value=mock_resp):
        feed, status, err = service.fetch_feed("https://example.com/rss.xml")
        assert status == 200
        assert err is None
        assert feed is not None
        assert len(feed.entries) == 1
        assert feed.entries[0].title == "ISRO Launches Navigation Satellite"


def test_fetch_feed_handles_http_errors_and_retries():
    """Verify fetch_feed returns appropriate error on non-retryable and retryable HTTP errors."""
    service = IngestionService(MagicMock())

    # 404 Not Found (non-retryable)
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    with patch("httpx.Client.get", return_value=mock_resp):
        feed, status, err = service.fetch_feed("https://example.com/missing.xml")
        assert feed is None
        assert status == 404
        assert "HTTP 404" in err


def test_fetch_feed_handles_timeouts_gracefully():
    """Verify fetch_feed handles timeout exceptions without crashing."""
    import httpx
    service = IngestionService(MagicMock())

    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("Connection timed out")):
        feed, status, err = service.fetch_feed("https://example.com/timeout.xml")
        assert feed is None
        assert "Timeout fetching feed" in err


# =========================================================================
# 2. Duplicate Prevention Tests (Level 1 & Level 2)
# =========================================================================

def test_duplicate_document_prevention(db_session: Session):
    """Verify identical article URLs and content are not re-inserted as duplicate documents."""
    service = IngestionService(db_session)
    source = Source(
        name="Test Feed",
        url="https://test.com",
        feed_url="https://test.com/rss",
        domain="Science",
        reliability_score=0.99,
        enabled=True,
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)

    run = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
    db_session.add(run)
    db_session.commit()

    fake_feed = MagicMock()
    fake_entry = {
        "title": "Quantum Computer Breakthrough",
        "link": "https://test.com/quantum-1",
        "summary": "Scientists demonstrate quantum advantage in supercomputing.",
        "published": "2026-10-30T10:00:00Z"
    }
    fake_feed.entries = [fake_entry]

    with patch.object(service, "fetch_feed", return_value=(fake_feed, 200, None)):
        # First ingestion
        metric1 = service.ingest_source(source, run)
        assert metric1.documents_accepted == 1
        assert metric1.documents_duplicate == 0

        # Second ingestion of the exact same entry
        metric2 = service.ingest_source(source, run)
        assert metric2.documents_accepted == 0
        assert metric2.documents_duplicate == 1


def test_event_deduplication_links_source_without_duplicate_row(db_session: Session):
    """Verify when two sources report the same event, the second is deduplicated and linked to the existing event."""
    service = IngestionService(db_session)
    source1 = Source(name="Src1", url="https://s1.com", feed_url="https://s1.com/rss", domain="Science", enabled=True)
    source2 = Source(name="Src2", url="https://s2.com", feed_url="https://s2.com/rss", domain="Science", enabled=True)
    db_session.add_all([source1, source2])
    db_session.commit()

    run = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
    db_session.add(run)
    db_session.commit()

    event_date = "2026-10-30"
    title = "ISRO Successfully Launches Earth Observation Satellite"

    entry1 = {
        "title": title,
        "link": "https://s1.com/isro-eos",
        "summary": "ISRO launched the satellite from Sriharikota.",
        "published": f"{event_date}T08:00:00Z"
    }
    feed1 = MagicMock(entries=[entry1])

    entry2 = {
        "title": title,
        "link": "https://s2.com/isro-eos-report",
        "summary": "Detailed coverage of ISRO satellite launch into orbit.",
        "published": f"{event_date}T09:00:00Z"
    }
    feed2 = MagicMock(entries=[entry2])

    with patch.object(service, "fetch_feed", return_value=(feed1, 200, None)):
        metric1 = service.ingest_source(source1, run)
        assert metric1.events_created == 1

    with patch.object(service, "fetch_feed", return_value=(feed2, 200, None)):
        metric2 = service.ingest_source(source2, run)
        assert metric2.events_created == 0
        assert metric2.events_deduplicated == 1


# =========================================================================
# 3. Partial Source Failure Resilience Tests
# =========================================================================

def test_partial_source_failure_does_not_abort_run(db_session: Session):
    """One failing source must NOT stop other sources from being ingested successfully."""
    service = IngestionService(db_session)
    src_failing = Source(name="Failing Feed", url="https://fail.com", feed_url="https://fail.com/rss", domain="Science", enabled=True)
    src_healthy = Source(name="Healthy Feed", url="https://ok.com", feed_url="https://ok.com/rss", domain="Science", enabled=True)
    db_session.add_all([src_failing, src_healthy])
    db_session.commit()

    feed_healthy = MagicMock(entries=[{
        "title": "Clean Energy Storage Breakthrough",
        "link": "https://ok.com/clean-energy",
        "summary": "New green hydrogen fuel cells achieve record efficiency.",
        "published": "2026-10-30T10:00:00Z"
    }])

    def mock_fetch(url):
        if "fail" in url:
            return None, 500, "Internal Server Error"
        return feed_healthy, 200, None

    with patch.object(service, "fetch_feed", side_effect=mock_fetch):
        summary = service.ingest_all_enabled_sources()
        assert summary["status"] == "completed"
        assert summary["sources_attempted"] >= 2
        assert summary["sources_failed"] >= 1
        assert summary["sources_succeeded"] >= 1
        assert summary["events_created"] >= 1

    # Verify source fields were updated
    db_session.refresh(src_failing)
    db_session.refresh(src_healthy)
    assert src_failing.last_error is not None
    assert src_healthy.last_ingested_at is not None
    assert src_healthy.last_error is None


# =========================================================================
# 4. Classification & Syllabus Relevance Filtering Tests
# =========================================================================

def test_landmark_legal_always_eligible():
    """Supreme Court and constitutional bench decisions must always be eligible with high scores."""
    res = NewsRelevanceService.evaluate(
        title="Supreme Court Constitution Bench rules on judicial appointments",
        content="A seven-judge bench delivered a landmark judgment interpreting Article 124.",
        domain="Polity"
    )
    assert res.is_eligible is True
    assert res.relevance_score >= 90
    assert "Polity" in res.syllabus_topic


def test_public_health_and_who_eligible():
    """Public health initiatives and WHO announcements must be recognized as eligible."""
    res = NewsRelevanceService.evaluate(
        title="World Health Organization certifies region malaria-free",
        content="The WHO confirmed successful elimination of malaria following nationwide vector control.",
        domain="Medical"
    )
    assert res.is_eligible is True
    assert res.relevance_score >= 50
    assert "Health" in res.syllabus_topic


def test_tamil_nadu_governance_eligible():
    """Tamil Nadu state welfare schemes and High Court rulings must be eligible."""
    res = NewsRelevanceService.evaluate(
        title="Madras High Court upholds government scheme for rural education",
        content="The High Court affirmed the state welfare initiative under public policy.",
        domain="Governance"
    )
    assert res.is_eligible is True
    assert res.relevance_score >= 60


def test_entertainment_gossip_rejected():
    """Celebrity gossip and movie reviews must be strictly rejected."""
    res = NewsRelevanceService.evaluate(
        title="Kollywood actor spotted at movie audio launch",
        content="The celebrity teaser release event saw many film stars in attendance.",
        domain="Entertainment"
    )
    assert res.is_eligible is False
    assert "Entertainment" in res.rejection_reason or "celebrity" in res.rejection_reason


def test_routine_crime_rejected():
    """Local thefts, chain snatchings, and prison escapes must be rejected."""
    res = NewsRelevanceService.evaluate(
        title="Inmate escaped from prison after stealing mobile phone",
        content="Local police arrested the escaped prisoner following a chase.",
        domain="Crime"
    )
    assert res.is_eligible is False
    assert res.rejection_reason is not None


def test_generic_sports_rejected_major_sports_accepted():
    """Routine match scores are rejected while Olympic/Championship events are accepted."""
    # Routine league score -> rejected
    res_routine = NewsRelevanceService.evaluate(
        title="Premier League: Team wins match 2-1",
        content="The striker scored in the final minutes to win the league game.",
        domain="Sports"
    )
    assert res_routine.is_eligible is False

    # Major National/International Sports -> accepted
    res_olympics = NewsRelevanceService.evaluate(
        title="India wins gold medal at the Asian Games",
        content="Indian athletes set a new record at the Asian Games world championship.",
        domain="Sports"
    )
    assert res_olympics.is_eligible is True


# =========================================================================
# 5. Geographic Mapping Tests
# =========================================================================

def test_geographic_mapping_for_tamil_nadu_and_india(db_session: Session):
    """Verify Tamil Nadu news is tagged with STATE and TN, and National news with INDIA."""
    loc_service = LocationService(db_session)
    source = Source(name="TN News", url="https://tn.gov.in", feed_url="https://tn.gov.in/rss", domain="Governance", enabled=True)
    db_session.add(source)
    db_session.commit()

    # Tamil Nadu Event
    event_tn = Event(
        title="Tamil Nadu Government introduces new mangrove conservation policy in Chennai",
        summary="Chief Minister announced the coastal conservation initiative across Tamil Nadu.",
        domain="Environment",
        event_date=datetime.now(timezone.utc).date(),
        published_at=datetime.now(timezone.utc),
        source_id=source.id,
        source_url="https://tn.gov.in/news/1",
        dedup_hash=compute_event_dedup_hash("Tamil Nadu Government introduces new mangrove policy in Chennai", "2026-10-30"),
        is_exam_eligible=True,
    )
    db_session.add(event_tn)
    db_session.commit()

    from app.services.exam_classification_service import ExamClassificationService
    classifier = ExamClassificationService(db_session)
    meta, relevances = classifier.classify_event(event_tn)

    assert meta.geographic_level in ("TN_STATE", "STATE")
    assert meta.primary_state == "TN"

    # Also verify LocationService extractor extracts Tamil Nadu / Chennai
    extracted = loc_service.extractor.extract_locations(f"{event_tn.title} {event_tn.summary}")
    loc_names = [loc.name for loc, conf, rel in extracted]
    assert "Tamil Nadu" in loc_names or "Chennai" in loc_names


# =========================================================================
# 6. API Endpoint & Response Tests
# =========================================================================

def test_trigger_ingestion_endpoint_sync_and_async(client: TestClient):
    """POST /api/v1/sources/ingest triggers ingestion synchronously or via background flag."""
    with patch("app.services.ingestion.IngestionService.ingest_all_enabled_sources") as mock_ingest:
        mock_ingest.return_value = {
            "status": "completed",
            "sources_attempted": 7,
            "sources_succeeded": 7,
            "sources_failed": 0,
            "documents_discovered": 150,
            "documents_ingested": 100,
            "documents_duplicate": 50,
            "events_created": 30,
            "events_deduplicated": 10,
            "processing_time_ms": 2500.0,
            "error_count": 0,
        }

        # Sync trigger
        res_sync = client.post("/api/v1/sources/ingest")
        assert res_sync.status_code == 200
        data_sync = res_sync.json()
        assert data_sync["status"] == "completed"
        assert data_sync["events_created"] == 30

        # Background trigger
        res_async = client.post("/api/v1/sources/ingest?background=true")
        assert res_async.status_code == 200
        data_async = res_async.json()
        assert data_async["status"] == "started"


def test_ingestion_lock_prevents_overlapping_runs(client: TestClient):
    """Calling /api/v1/sources/ingest while a run is active returns HTTP 409 Conflict."""
    from app.api.v1.sources import _INGESTION_LOCK
    assert _INGESTION_LOCK.acquire(blocking=False)
    try:
        res = client.post("/api/v1/sources/ingest")
        assert res.status_code == 409
        assert "already in progress" in res.json()["detail"]
    finally:
        _INGESTION_LOCK.release()


def test_ingest_single_source_by_id(client: TestClient, db_session: Session):
    """POST /api/v1/sources/ingest?source_id=X only targets that specific source."""
    source = Source(name="Target Feed", url="https://target.com", feed_url="https://target.com/rss", domain="Science", enabled=True)
    db_session.add(source)
    db_session.commit()

    with patch("app.services.ingestion.IngestionService.ingest_all_enabled_sources") as mock_ingest:
        mock_ingest.return_value = {
            "status": "completed",
            "sources_attempted": 1,
            "sources_succeeded": 1,
            "sources_failed": 0,
            "articles_fetched": 10,
            "articles_accepted": 8,
            "articles_stored": 5,
            "duplicates_skipped": 2,
            "events_created": 5,
            "events_deduplicated": 0,
            "documents_discovered": 10,
            "documents_ingested": 8,
            "documents_duplicate": 2,
            "processing_time_ms": 320.0,
            "error_count": 0,
            "errors": []
        }

        res = client.post(f"/api/v1/sources/ingest?source_id={source.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["sources_attempted"] == 1
        assert data["articles_stored"] == 5
        mock_ingest.assert_called_once_with(source_id=source.id)

    # If source ID does not exist, return 404
    res_404 = client.post("/api/v1/sources/ingest?source_id=999999")
    assert res_404.status_code == 404


def test_source_status_and_timestamps_persistence_on_failure(db_session: Session):
    """When a feed fetch fails, last_attempted_at and last_error are committed to DB."""
    source = Source(
        name="Broken Feed",
        url="https://broken.com",
        feed_url="https://broken.com/rss",
        domain="Science",
        enabled=True
    )
    db_session.add(source)
    db_session.commit()

    service = IngestionService(db_session)
    with patch.object(service, "fetch_feed", return_value=(None, 500, "HTTP 500 Internal Server Error")):
        run = IngestionRun(started_at=datetime.now(timezone.utc), status="running")
        db_session.add(run)
        db_session.commit()

        metric = service.ingest_source(source, run)
        assert metric.status == "http_error"
        assert metric.error_message == "HTTP 500 Internal Server Error"

        db_session.refresh(source)
        assert source.last_attempted_at is not None
        assert source.last_error == "HTTP 500 Internal Server Error"
        assert source.last_ingested_at is None


def test_truthful_ingestion_summary_response(db_session: Session):
    """IngestionService.ingest_all_enabled_sources returns accurate counts and per-source errors."""
    s1 = Source(name="Good Feed", url="https://good.com", feed_url="https://good.com/rss", domain="Science", enabled=True)
    s2 = Source(name="Bad Feed", url="https://bad.com", feed_url="https://bad.com/rss", domain="Economy", enabled=True)
    db_session.add_all([s1, s2])
    db_session.commit()

    mock_good_feed = MagicMock()
    mock_good_feed.entries = [
        {
            "title": "Clean Energy Breakthrough Announced by Ministry",
            "summary": "Government announces major grid upgrades.",
            "link": "https://good.com/art1",
            "published": "Fri, 30 Oct 2026 12:00:00 GMT"
        }
    ]

    service = IngestionService(db_session)

    def mock_fetch(url):
        if "good.com" in url:
            return mock_good_feed, 200, None
        return None, 404, "HTTP 404 Not Found"

    with patch.object(service, "fetch_feed", side_effect=mock_fetch):
        summary = service.ingest_all_enabled_sources()

        assert summary["status"] == "completed"
        assert summary["sources_attempted"] >= 2
        assert summary["sources_succeeded"] >= 1
        assert summary["sources_failed"] >= 1
        assert "articles_fetched" in summary
        assert "articles_accepted" in summary
        assert "articles_stored" in summary
        assert "duplicates_skipped" in summary
        assert "errors" in summary
        assert len(summary["errors"]) >= 1

        bad_err = next((e for e in summary["errors"] if e["source_name"] == "Bad Feed"), None)
        assert bad_err is not None
        assert "404" in bad_err["error"]


def test_events_api_filters_non_eligible_events(client: TestClient, db_session: Session):
    """GET /api/v1/events must only return events where is_exam_eligible is True."""
    source = Source(name="Src", url="https://s.com", feed_url="https://s.com/rss", domain="Science", enabled=True)
    db_session.add(source)
    db_session.commit()

    ev_eligible = Event(
        title="ISRO Launches Climate Observatory",
        summary="A major space observatory placed in orbit.",
        domain="Science",
        event_date=datetime.now(timezone.utc).date(),
        published_at=datetime.now(timezone.utc),
        source_id=source.id,
        source_url="https://s.com/ev1",
        dedup_hash=compute_event_dedup_hash("ISRO Launches Climate Observatory", "2026-10-30"),
        is_exam_eligible=True,
    )
    ev_ineligible = Event(
        title="Actor spotted at restaurant",
        summary="Movie celebrity was photographed by paparazzi.",
        domain="Entertainment",
        event_date=datetime.now(timezone.utc).date(),
        published_at=datetime.now(timezone.utc),
        source_id=source.id,
        source_url="https://s.com/ev2",
        dedup_hash=compute_event_dedup_hash("Actor spotted at restaurant", "2026-10-30"),
        is_exam_eligible=False,
    )
    db_session.add_all([ev_eligible, ev_ineligible])
    db_session.commit()

    res = client.get("/api/v1/events")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "events" in data
    titles = [e["title"] for e in data["events"]]
    assert "ISRO Launches Climate Observatory" in titles
    assert "Actor spotted at restaurant" not in titles
