from datetime import date, datetime, timezone
from app.models.source import Source
from app.models.event import Event


def test_list_events_and_filters(client, db_session):
    source = Source(name="Source 1", url="https://s1.com", feed_url="https://s1.com/rss")
    db_session.add(source)
    db_session.commit()

    event1 = Event(
        title="AI Research Conference Announced",
        summary="Top researchers gather to discuss AI ethics and scalability.",
        domain="AI",
        event_date=date(2026, 8, 18),
        published_at=datetime.now(timezone.utc),
        source_id=source.id,
        source_url="https://s1.com/e1",
        confidence_score=1.0,
        dedup_hash="hash_1"
    )
    event2 = Event(
        title="Central Bank Modifies Interest Rates",
        summary="Global markets react to monetary policy shifts.",
        domain="Economy",
        event_date=date(2026, 8, 19),
        published_at=datetime.now(timezone.utc),
        source_id=source.id,
        source_url="https://s1.com/e2",
        confidence_score=1.0,
        dedup_hash="hash_2"
    )
    db_session.add_all([event1, event2])
    db_session.commit()

    # Query all
    resp_all = client.get("/api/v1/events")
    assert resp_all.status_code == 200
    assert resp_all.json()["total"] == 2

    # Filter by domain
    resp_domain = client.get("/api/v1/events?domain=AI")
    assert resp_domain.status_code == 200
    assert resp_domain.json()["total"] == 1
    assert resp_domain.json()["events"][0]["title"] == "AI Research Conference Announced"

    # Filter by exact date
    resp_date = client.get("/api/v1/events?date=2026-08-19")
    assert resp_date.status_code == 200
    assert resp_date.json()["total"] == 1
    assert resp_date.json()["events"][0]["domain"] == "Economy"
