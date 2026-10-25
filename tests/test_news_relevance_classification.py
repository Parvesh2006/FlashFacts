import pytest
from datetime import date
from app.services.classification import KeywordDomainClassifier
from app.services.exam_intelligence import ExamIntelligenceService
from app.models.event import Event
from app.models.source import Source
from app.repositories.event_repository import EventRepository


def test_vadavalli_local_crime_negative_case():
    """
    Negative test case:
    A Tamil local-news report about a person allegedly tricking a mobile-shop employee
    in Vadavalli, Coimbatore, and stealing four phones and ₹15,000.

    Expected:
    - Classified as Crime, not Environment, Polity, Economy, Science, or General News.
    """
    classifier = KeywordDomainClassifier()
    title = "வடவள்ளியில் செல்போன் கடை ஊழியரை ஏமாற்றி 4 போன்கள், ரூ.15,000 திருட்டு"
    content = (
        "கோவை வடவள்ளி பகுதியில் உள்ள செல்போன் கடையில் ஊழியரிடம் நூதன முறையில் பேசி "
        "4 செல்போன்கள் மற்றும் ரூ.15,000 ரொக்கத்தை மர்ம நபர் திருடிச் சென்றார். "
        "இதுகுறித்து போலீசார் வழக்குப்பதிவு செய்து விசாரணை நடத்தி வருகின்றனர்."
    )

    domain = classifier.classify(title, content)
    assert domain == "Crime"
    assert domain not in ("Environment", "Economy", "Politics", "Government", "Science", "General", "General News")


def test_landmark_legal_decision_not_excluded():
    """
    Positive test case:
    Major legal judgments and constitutional rulings must be classified as Government/Polity
    and preserved for competitive exam relevance.
    """
    classifier = KeywordDomainClassifier()
    title = "குற்றவியல் சட்டத் திருத்தம்: உச்ச நீதிமன்ற அரசியலமைப்பு அமர்வு வரலாற்று தீர்ப்பு"
    content = (
        "பாரதிய நியாய சன்ஹிதா சட்டப்பிரிவுகள் மற்றும் ஜாமீன் விதிகள் குறித்து "
        "உச்ச நீதிமன்றத்தின் 5 நீதிபதிகள் கொண்ட அரசியலமைப்பு அமர்வு வரலாற்று சிறப்புமிக்க தீர்ப்பளித்துள்ளது."
    )

    domain = classifier.classify(title, content)
    assert domain == "Government"


def test_routine_crime_excluded_from_exam_feed_but_preserved_for_audit(db_session, client):
    """
    Verify that routine local-crime reports are:
    1. Excluded from default competitive exam current affairs feeds.
    2. Excluded from exam-specific feeds (e.g. TNPSC).
    3. Preserved with their original URL and record in the database for auditability.
    4. Accessible when specifically querying domain=Crime or by direct ID.
    """
    # 1. Create a test source
    src = Source(
        name="Coimbatore Daily",
        url="https://example.com/cbe",
        feed_url="https://example.com/cbe/rss",
        source_type="rss",
        domain="Tamil Nadu",
        reliability_score=1.0,
        enabled=True,
    )
    db_session.add(src)
    db_session.commit()

    from datetime import datetime, timezone

    # 2. Ingest the negative test case event
    crime_event = Event(
        title="வடவள்ளியில் செல்போன் கடை ஊழியரை ஏமாற்றி 4 போன்கள், ரூ.15,000 திருட்டு",
        summary=(
            "கோவை வடவள்ளி பகுதியில் உள்ள செல்போன் கடையில் ஊழியரிடம் நூதன முறையில் பேசி "
            "4 செல்போன்கள் மற்றும் ரூ.15,000 ரொக்கத்தை மர்ம நபர் திருடிச் சென்றார்."
        ),
        domain="Crime",
        source_id=src.id,
        source_url="https://example.com/cbe/vadavalli-theft-123",
        event_date=date(2026, 10, 20),
        published_at=datetime.now(timezone.utc),
        dedup_hash="test_crime_vadavalli_hash_1",
        confidence_score=0.95,
        importance_score=20,
    )
    db_session.add(crime_event)

    # Also add an exam-relevant event for contrast
    exam_event = Event(
        title="உச்ச நீதிமன்றம் வரலாற்று தீர்ப்பு: அரசியலமைப்பு சட்ட திருத்தம் உறுதி",
        summary="உச்ச நீதிமன்ற அரசியலமைப்பு அமர்வு முக்கிய வழக்கில் தீர்ப்பளித்துள்ளது.",
        domain="Government",
        source_id=src.id,
        source_url="https://example.com/cbe/sc-landmark-judgment-456",
        event_date=date(2026, 10, 20),
        published_at=datetime.now(timezone.utc),
        dedup_hash="test_exam_event_hash_2",
        confidence_score=1.0,
        importance_score=85,
    )
    db_session.add(exam_event)
    db_session.commit()

    # 3. Default competitive-exam current affairs feed: Crime must be excluded!
    resp = client.get("/api/v1/events")
    assert resp.status_code == 200
    data = resp.json()
    returned_ids = [e["id"] for e in data["events"]]
    assert crime_event.id not in returned_ids, "Routine local crime must be excluded from default exam feed"
    assert exam_event.id in returned_ids, "Exam-relevant event must be included"

    # 4. Exam-filtered feed: Crime must be excluded!
    resp_tnpsc = client.get("/api/v1/events?exam=TNPSC")
    assert resp_tnpsc.status_code == 200
    tnpsc_ids = [e["id"] for e in resp_tnpsc.json()["events"]]
    assert crime_event.id not in tnpsc_ids, "Routine local crime must be excluded from TNPSC exam feed"

    # 5. Auditability: Crime record is preserved and accessible when domain=Crime is queried
    resp_audit = client.get("/api/v1/events?domain=Crime")
    assert resp_audit.status_code == 200
    audit_data = resp_audit.json()
    audit_ids = [e["id"] for e in audit_data["events"]]
    assert crime_event.id in audit_ids, "Crime record must be preserved for auditability"
    found_item = next(e for e in audit_data["events"] if e["id"] == crime_event.id)
    assert found_item["source_url"] == "https://example.com/cbe/vadavalli-theft-123"

    # 6. Direct ID retrieval is preserved
    resp_single = client.get(f"/api/v1/events/{crime_event.id}")
    assert resp_single.status_code == 200
    assert resp_single.json()["domain"] == "Crime"
    assert resp_single.json()["source_url"] == "https://example.com/cbe/vadavalli-theft-123"


def test_exam_intelligence_scores_routine_crime_as_not_relevant(db_session):
    """
    Verify ExamIntelligenceService assigns routine crime a non-relevant score (<= 15)
    and does not grant an unearned Tamil Nadu geographic boost.
    """
    service = ExamIntelligenceService(db_session)
    mock_crime = Event(
        title="வடவள்ளியில் செல்போன் கடை ஊழியரை ஏமாற்றி 4 போன்கள், ரூ.15,000 திருட்டு",
        summary="கோவை வடவள்ளி பகுதியில் செல்போன் திருட்டு.",
        domain="Crime",
        importance_score=20,
    )

    tnpsc_def = service.get_exam("tnpsc-group-4")
    score_res = service.score_event_for_exam(mock_crime, tnpsc_def)
    assert score_res["relevance_score"] <= 15, "Routine local crime must score <= 15 for TNPSC"

    upsc_def = service.get_exam("upsc-prelims")
    if upsc_def:
        upsc_score = service.score_event_for_exam(mock_crime, upsc_def)
        assert upsc_score["relevance_score"] <= 15, "Routine local crime must score <= 15 for UPSC"
