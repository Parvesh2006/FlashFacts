"""
Tests for Geographic Locations, Event Relations, Timeline, and Coverage APIs.
"""
import pytest
from datetime import datetime, date
from app.models.source import Source
from app.models.event import Event
from app.models.location import GeographicLocation, EventLocation
from app.services.location_service import LocationService, seed_geographic_locations
from app.services.event_relation_service import EventRelationService


@pytest.fixture
def test_source(db_session):
    src = Source(
        name="The Hindu",
        url="https://thehindu.com",
        feed_url="https://thehindu.com/feeder",
        source_type="rss",
        domain="General",
        reliability_score=1.0,
        enabled=True,
    )
    db_session.add(src)
    db_session.commit()
    return src


def test_seed_and_hierarchy_locations(db_session):
    """Verify geographic location seeding and hierarchy relationships."""
    locs = seed_geographic_locations(db_session)
    assert len(locs) >= 10

    service = LocationService(db_session)
    tree = service.get_location_tree()
    assert len(tree) > 0

    tn = db_session.query(GeographicLocation).filter(GeographicLocation.name == "Tamil Nadu").first()
    assert tn is not None
    assert tn.country_code == "IN"


def test_location_extraction_and_event_linking(db_session, test_source):
    """Verify deterministic location extraction from event content."""
    event = Event(
        title="Coimbatore district administration launches green energy initiative in Tamil Nadu",
        summary="The district collector inaugurated solar micro-grids across industrial clusters in Coimbatore.",
        domain="Environment",
        event_type="launch",
        event_date=date.today(),
        published_at=datetime.utcnow(),
        source_id=test_source.id,
        source_url="https://example.com/coimbatore-green",
        importance_score=80,
        confidence_score=0.95,
        dedup_hash="test_hash_covai_1",
    )
    db_session.add(event)
    db_session.commit()

    service = LocationService(db_session)
    locs = service.attach_locations_to_event(event)

    assert len(locs) >= 1
    loc_names = [el.location.name for el in locs if el.location]
    assert "Coimbatore" in loc_names or "Tamil Nadu" in loc_names


def test_event_location_endpoint_is_repeat_safe(client, db_session, test_source):
    event = Event(
        title="Chennai launches a new flood monitoring system",
        summary="The Tamil Nadu city deployed sensors across Chennai.",
        domain="Environment",
        event_type="launch",
        event_date=date.today(),
        published_at=datetime.utcnow(),
        source_id=test_source.id,
        source_url="https://example.com/chennai-flood",
        importance_score=75,
        confidence_score=0.9,
        dedup_hash="test_hash_chennai_repeat",
    )
    db_session.add(event)
    db_session.commit()

    first = client.get(f"/api/v1/events/{event.id}/location")
    second = client.get(f"/api/v1/events/{event.id}/location")

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(first.json()["locations"]) >= 1
    assert len(second.json()["locations"]) == len(first.json()["locations"])


def test_location_events_include_deep_descendants(db_session, test_source):
    service = LocationService(db_session)
    service.get_location_tree()
    india = db_session.query(GeographicLocation).filter(GeographicLocation.name == "India").first()
    chennai = db_session.query(GeographicLocation).filter(GeographicLocation.name == "Chennai").first()
    event = Event(
        title="Chennai metro expansion approved",
        summary="The project affects commuters in Chennai.",
        domain="Government",
        event_type="policy",
        event_date=date.today(),
        published_at=datetime.utcnow(),
        source_id=test_source.id,
        source_url="https://example.com/chennai-metro",
        importance_score=70,
        confidence_score=0.9,
        dedup_hash="test_hash_chennai_descendant",
    )
    db_session.add(event)
    db_session.commit()
    db_session.add(EventLocation(event_id=event.id, location_id=chennai.id, relation_type="PRIMARY", confidence=0.95))
    db_session.commit()

    result = service.get_location_events(india.id)

    assert result["total"] == 1
    assert result["events"][0]["id"] == event.id


def test_event_timeline_and_relations(db_session, test_source):
    """Verify event relation creation and timeline retrieval."""
    e1 = Event(
        title="Ministry of Electronics announces semiconductor subsidy scheme",
        summary="Initial announcement of 50 billion INR incentive package.",
        domain="Technology",
        event_type="policy",
        event_date=date(2026, 9, 1),
        published_at=datetime.utcnow(),
        source_id=test_source.id,
        source_url="https://example.com/semi-1",
        importance_score=85,
        confidence_score=0.9,
        dedup_hash="test_hash_semi_1",
    )
    e2 = Event(
        title="First semiconductor fabrication plant breaks ground in Gujarat",
        summary="Construction begins on the chip manufacturing facility under national policy.",
        domain="Technology",
        event_type="launch",
        event_date=date(2026, 9, 15),
        published_at=datetime.utcnow(),
        source_id=test_source.id,
        source_url="https://example.com/semi-2",
        importance_score=90,
        confidence_score=0.95,
        dedup_hash="test_hash_semi_2",
    )
    db_session.add_all([e1, e2])
    db_session.commit()

    rel_service = EventRelationService(db_session)
    rel = rel_service.create_relation(e1.id, e2.id, relation_type="PRECEDES")
    assert rel is not None

    timeline = rel_service.get_event_timeline(e2.id)
    assert timeline["event_id"] == e2.id
    assert len(timeline["timeline"]) >= 2


def test_location_and_coverage_api_endpoints(client, db_session):
    """Test /api/v1/locations and /api/v1/coverage API endpoints."""
    seed_geographic_locations(db_session)

    resp = client.get("/api/v1/locations")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    resp_cov = client.get("/api/v1/coverage")
    assert resp_cov.status_code == 200
    data = resp_cov.json()
    assert "total_sources" in data
    assert "events_with_geographic_mapping" in data
    levels = {row["level"] for row in data["coverage_breakdown"]}
    assert {"WORLD", "COUNTRY", "STATE"}.issubset(levels)
