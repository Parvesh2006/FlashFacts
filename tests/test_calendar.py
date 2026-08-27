from datetime import date, datetime, timezone
from app.models.source import Source
from app.models.event import Event


def test_calendar_aggregation_api(client, db_session):
    source = Source(name="Calendar Source", url="https://cal.com", feed_url="https://cal.com/rss")
    db_session.add(source)
    db_session.commit()

    ev1 = Event(
        title="Event 1", summary="s1", domain="AI",
        event_date=date(2026, 8, 18), published_at=datetime.now(timezone.utc),
        source_id=source.id, source_url="https://cal.com/1", dedup_hash="h1"
    )
    ev2 = Event(
        title="Event 2", summary="s2", domain="AI",
        event_date=date(2026, 8, 18), published_at=datetime.now(timezone.utc),
        source_id=source.id, source_url="https://cal.com/2", dedup_hash="h2"
    )
    ev3 = Event(
        title="Event 3", summary="s3", domain="Sports",
        event_date=date(2026, 8, 18), published_at=datetime.now(timezone.utc),
        source_id=source.id, source_url="https://cal.com/3", dedup_hash="h3"
    )
    db_session.add_all([ev1, ev2, ev3])
    db_session.commit()

    resp = client.get("/api/v1/calendar?month=2026-08")
    assert resp.status_code == 200
    data = resp.json()
    assert data["month"] == "2026-08"
    assert len(data["days"]) == 1

    day_info = data["days"][0]
    assert day_info["date"] == "2026-08-18"
    assert day_info["total"] == 3
    assert day_info["domains"]["AI"] == 2
    assert day_info["domains"]["Sports"] == 1
