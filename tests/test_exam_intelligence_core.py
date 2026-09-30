import pytest
from datetime import date, datetime, timezone
from app.models.source import Source
from app.models.event import Event
from app.models.exam_intelligence import EventExamMetadata, EventExamRelevance
from app.services.exam_classification_service import ExamClassificationService
from app.repositories.event_repository import EventRepository


@pytest.fixture
def test_source(db_session):
    source = Source(name="Test Exam Source", url="https://testsource.com", feed_url="https://testsource.com/rss")
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source


def test_exam_intelligence_models_schema(db_session, test_source):
    """Test creation and relationships of EventExamMetadata and EventExamRelevance."""
    event = Event(
        title="Cabinet approves National Green Hydrogen Mission",
        summary="Union Cabinet approves outlay of Rs 19,744 crore for National Green Hydrogen Mission.",
        domain="Environment",
        event_date=date(2026, 3, 15),
        published_at=datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc),
        source_id=test_source.id,
        source_url="https://testsource.com/e1",
        confidence_score=0.95,
        dedup_hash="test_schema_hash_001",
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    metadata = EventExamMetadata(
        event_id=event.id,
        primary_state=None,
        geographic_level="NATIONAL",
        exam_importance="MUST_KNOW",
        why_it_matters="Crucial national policy initiative for renewable energy targets.",
        exam_facts=[
            {"fact_statement": "Outlay is Rs 19,744 crore.", "fact_type": "NUMBER", "memorization_tip": "Remember 19k+ cr"},
            {"fact_statement": "Nodal ministry is Ministry of New and Renewable Energy.", "fact_type": "ORGANIZATION"},
        ],
        question_angles=["Which ministry leads Green Hydrogen Mission?", "What is total financial outlay?"]
    )
    db_session.add(metadata)

    rel_tnpsc = EventExamRelevance(
        event_id=event.id,
        exam_type="TNPSC",
        relevance_score=75,
        relevance_level="HIGH",
        why_relevant="Important for General Science and Environment paper.",
        explanation="Important for General Science and Environment paper."
    )
    rel_upsc = EventExamRelevance(
        event_id=event.id,
        exam_type="UPSC",
        relevance_score=95,
        relevance_level="VERY_HIGH",
        why_relevant="Direct GS Paper 3 Environment topic.",
        explanation="Direct GS Paper 3 Environment topic."
    )
    db_session.add_all([rel_tnpsc, rel_upsc])
    db_session.commit()

    db_session.refresh(event)
    assert event.exam_metadata is not None
    assert event.exam_metadata.geographic_level == "NATIONAL"
    assert event.exam_metadata.exam_importance == "MUST_KNOW"
    assert len(event.exam_metadata.exam_facts) == 2
    assert len(event.exam_relevances) == 2


def test_classification_service_tnpsc(db_session, test_source):
    """Test classification for Tamil Nadu state-specific event."""
    event = Event(
        title="TN Chief Minister launches Pudhumai Penn scheme phase 2 in Chennai Tamil Nadu",
        summary="Tamil Nadu government expands financial assistance scheme of Rs 1,000 per month for female students in Govt schools.",
        domain="Governance",
        event_date=date(2026, 3, 20),
        published_at=datetime(2026, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
        source_id=test_source.id,
        source_url="https://testsource.com/e2",
        confidence_score=0.98,
        dedup_hash="test_tn_scheme_hash",
    )
    db_session.add(event)
    db_session.commit()

    service = ExamClassificationService(db_session)
    metadata, relevances = service.classify_event(event)

    assert metadata.geographic_level in ["TN_STATE", "STATE"]
    assert metadata.primary_state == "TN"
    assert metadata.exam_importance in ["MUST_KNOW", "IMPORTANT"]
    assert len(metadata.exam_facts) > 0
    assert len(metadata.question_angles) > 0

    tnpsc_rel = next((r for r in relevances if r.exam_type == "TNPSC"), None)
    assert tnpsc_rel is not None
    assert tnpsc_rel.relevance_level in ["VERY_HIGH", "HIGH"]
    assert tnpsc_rel.relevance_score >= 75


def test_classification_service_upsc_and_national(db_session, test_source):
    """Test classification for national financial & banking policy event."""
    event = Event(
        title="RBI keeps repo rate unchanged at 6.5 percent in Monetary Policy Committee meeting",
        summary="Reserve Bank of India governor announces status quo on benchmark lending rates.",
        domain="Economy",
        event_date=date(2026, 3, 21),
        published_at=datetime(2026, 3, 21, 10, 0, 0, tzinfo=timezone.utc),
        source_id=test_source.id,
        source_url="https://testsource.com/e3",
        confidence_score=0.92,
        dedup_hash="test_rbi_repo_hash",
    )
    db_session.add(event)
    db_session.commit()

    service = ExamClassificationService(db_session)
    metadata, relevances = service.classify_event(event)

    assert metadata.geographic_level == "NATIONAL"
    assert metadata.exam_importance in ["MUST_KNOW", "IMPORTANT"]

    banking_rel = next((r for r in relevances if r.exam_type == "BANKING"), None)
    assert banking_rel is not None
    assert banking_rel.relevance_level in ["VERY_HIGH", "HIGH"]

    upsc_rel = next((r for r in relevances if r.exam_type == "UPSC"), None)
    assert upsc_rel is not None
    assert upsc_rel.relevance_level in ["VERY_HIGH", "HIGH"]


def test_api_filtering_by_exam_geography_importance(client, db_session, test_source):
    """Test listing and searching events filtered by exam, geography, and importance."""
    event1 = Event(
        title="Tamil Nadu Government launches Chief Minister Breakfast Scheme expansion",
        summary="TN Chief Minister inaugurates primary school breakfast scheme across all districts in Tamil Nadu.",
        domain="Governance",
        event_date=date(2026, 3, 22),
        published_at=datetime(2026, 3, 22, 10, 0, 0, tzinfo=timezone.utc),
        source_id=test_source.id,
        source_url="https://testsource.com/e4",
        confidence_score=0.95,
        dedup_hash="test_api_filter_tn",
    )
    event2 = Event(
        title="ISRO launches Gaganyaan test vehicle payload successfully from Sriharikota",
        summary="Indian Space Research Organisation conducts key crew escape module test flight.",
        domain="Science & Technology",
        event_date=date(2026, 3, 23),
        published_at=datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc),
        source_id=test_source.id,
        source_url="https://testsource.com/e5",
        confidence_score=0.96,
        dedup_hash="test_api_filter_isro",
    )
    db_session.add_all([event1, event2])
    db_session.commit()

    # Pre-classify events
    service = ExamClassificationService(db_session)
    service.classify_event(event1)
    service.classify_event(event2)

    # Test GET /api/v1/events with exam=TNPSC filter
    res = client.get("/api/v1/events?exam=TNPSC")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    titles = [e["title"] for e in data["events"]]
    assert any("Tamil Nadu" in t for t in titles)

    # Test GET /api/v1/events with geography filter
    res_geo = client.get("/api/v1/events?geography=TN_STATE")
    assert res_geo.status_code == 200
    geo_data = res_geo.json()
    assert geo_data["total"] >= 1
    assert any("Breakfast Scheme" in e["title"] for e in geo_data["events"])

    # Test GET /api/v1/search with q=Gaganyaan and exam=UPSC
    res_search = client.get("/api/v1/search?q=Gaganyaan&exam=UPSC")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total"] >= 1
    assert "ISRO" in search_data["events"][0]["title"]


def test_event_response_auto_classification(db_session, test_source):
    """Test that EventRepository.to_event_response automatically classifies event if missing."""
    event = Event(
        title="Supreme Court of India upholds electoral transparency norms",
        summary="Bench ruled on disclosure requirements for political funding and electoral integrity.",
        domain="Polity",
        event_date=date(2026, 3, 24),
        published_at=datetime(2026, 3, 24, 10, 0, 0, tzinfo=timezone.utc),
        source_id=test_source.id,
        source_url="https://testsource.com/e6",
        confidence_score=0.90,
        dedup_hash="test_auto_classify_hash",
    )
    db_session.add(event)
    db_session.commit()

    repo = EventRepository(db_session)
    res = repo.to_event_response(event)

    assert res.exam_intelligence is not None
    assert res.exam_intelligence.geographic_level == "NATIONAL"
    assert res.exam_intelligence.exam_importance in ["MUST_KNOW", "IMPORTANT"]
    assert len(res.exam_intelligence.relevances) == 6  # TNPSC, UPSC, SSC, BANKING, RAILWAY, GENERAL_GOVT


def test_unicode_and_utf8_safety(db_session, test_source):
    """Test classification with Tamil characters and special Unicode formatting."""
    event = Event(
        title="தமிழ்நாடு (Tamil Nadu) launches New Startup Policy 2026 for youth Entrepreneurs",
        summary="TN state policy aims to support 10,000 tech startups in Chennai, Coimbatore and Madurai with ₹500 crore fund.",
        domain="Economy",
        event_date=date(2026, 3, 25),
        published_at=datetime(2026, 3, 25, 10, 0, 0, tzinfo=timezone.utc),
        source_id=test_source.id,
        source_url="https://testsource.com/e7",
        confidence_score=0.94,
        dedup_hash="test_unicode_tn_hash",
    )
    db_session.add(event)
    db_session.commit()

    service = ExamClassificationService(db_session)
    metadata, relevances = service.classify_event(event)

    assert metadata.primary_state == "TN"
    assert metadata.geographic_level in ["TN_STATE", "STATE"]
    assert len(metadata.exam_facts) > 0

