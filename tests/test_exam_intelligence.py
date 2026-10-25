"""
Tests for Exam Intelligence Service and MCQ Generation.
"""
import pytest
from datetime import datetime, date
from app.models.source import Source
from app.models.event import Event
from app.services.exam_intelligence import ExamIntelligenceService, EXAM_DEFINITIONS
from app.services.ai_provider import FallbackAIProvider


@pytest.fixture
def test_source(db_session):
    src = Source(
        name="Test Source",
        url="https://example.com",
        feed_url="https://example.com/rss",
        source_type="rss",
        domain="Government",
        reliability_score=1.0,
        enabled=True,
    )
    db_session.add(src)
    db_session.commit()
    return src


def test_exam_definitions_exist():
    """Verify all 7 required exams are defined with appropriate structure."""
    expected_ids = {
        "tnpsc-group-4", "tnpsc-group-2", "ssc-cgl",
        "ssc-chsl", "upsc-cse", "rrb-ntpc", "banking"
    }
    assert set(EXAM_DEFINITIONS.keys()) == expected_ids
    for exam_id, defn in EXAM_DEFINITIONS.items():
        assert "id" in defn
        assert "name" in defn
        assert "code" in defn
        assert "domains" in defn
        assert "keywords" in defn
        assert "section_label" in defn


def test_exams_endpoint_returns_required_exam_ids(client):
    response = client.get("/api/v1/exams")
    assert response.status_code == 200
    data = response.json()
    assert {exam["id"] for exam in data} == {
        "tnpsc-group-4", "tnpsc-group-2", "ssc-cgl",
        "ssc-chsl", "upsc-cse", "rrb-ntpc", "banking"
    }
    assert len(data) == 7


def test_score_event_for_exam(db_session, test_source):
    """Test deterministic scoring of events for exam relevance."""
    event = Event(
        title="Reserve Bank of India announces new monetary policy and interest rate benchmark",
        summary="The RBI introduced new liquidity measures and adjusted key repo rates for Indian banks.",
        domain="Economy",
        event_type="policy",
        event_date=date.today(),
        published_at=datetime.utcnow(),
        source_id=test_source.id,
        source_url="https://example.com/rbi-policy",
        importance_score=85,
        confidence_score=0.95,
        dedup_hash="test_hash_rbi_1",
    )
    db_session.add(event)
    db_session.commit()

    service = ExamIntelligenceService(db_session, provider=FallbackAIProvider())

    # Banking exam should score high
    banking_score = service.score_event_for_exam(event, EXAM_DEFINITIONS["banking"])
    assert banking_score["relevance_score"] >= 50
    assert "Economy" in str(banking_score["reasons"])

    # UPSC exam should also match on Economy domain and government policy
    upsc_score = service.score_event_for_exam(event, EXAM_DEFINITIONS["upsc-cse"])
    assert upsc_score["relevance_score"] >= 30


def test_generate_fallback_mcqs(db_session, test_source):
    """Test deterministic fallback MCQ generation for an event."""
    event = Event(
        title="ISRO launches new Earth Observation Satellite EOS-08",
        summary="The Indian Space Research Organisation successfully launched the EOS-08 satellite aboard SSLV-D3.",
        domain="Science",
        event_type="launch",
        event_date=date.today(),
        published_at=datetime.utcnow(),
        source_id=test_source.id,
        source_url="https://example.com/isro-launch",
        why_it_matters="Enhances disaster monitoring and environmental surveillance capabilities.",
        importance_score=75,
        confidence_score=0.9,
        dedup_hash="test_hash_isro_1",
    )
    db_session.add(event)
    db_session.commit()

    service = ExamIntelligenceService(db_session, provider=FallbackAIProvider())
    result = service.generate_mcqs(event.id, exam_id="upsc-cse", count=3)

    assert result["event_id"] == event.id
    assert result["provider"] == "fallback"
    assert len(result["mcqs"]) >= 1

    for mcq in result["mcqs"]:
        assert "question" in mcq
        assert len(mcq["options"]) == 4
        assert mcq["correct_answer"] in ("A", "B", "C", "D")
        assert "explanation" in mcq
        assert mcq["event_id"] == event.id


def test_event_exam_relevance_endpoint_data(db_session, test_source):
    """Test full event exam relevance resolution."""
    event = Event(
        title="Ministry of Finance presents annual union budget outline",
        summary="Union Finance Minister highlighted major infrastructure and taxation proposals.",
        domain="Government",
        event_type="announcement",
        event_date=date.today(),
        published_at=datetime.utcnow(),
        source_id=test_source.id,
        source_url="https://example.com/budget-2026",
        importance_score=90,
        confidence_score=0.98,
        dedup_hash="test_hash_budget_1",
    )
    db_session.add(event)
    db_session.commit()

    service = ExamIntelligenceService(db_session, provider=FallbackAIProvider())
    rel_data = service.get_event_exam_relevance(event.id)

    assert rel_data["event_id"] == event.id
    assert len(rel_data["relevant_exams"]) > 0
    assert len(rel_data["key_points"]) > 0
