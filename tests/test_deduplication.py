from datetime import date, datetime, timezone
from app.repositories.event_repository import EventRepository
from app.services.deduplication import DeduplicationService
from app.models.source import Source


def test_event_deduplication(db_session):
    # Seed Source
    source = Source(name="Test Source", url="https://test.com", feed_url="https://test.com/rss")
    db_session.add(source)
    db_session.commit()

    repo = EventRepository(db_session)
    dedup = DeduplicationService(repo)

    candidate_1 = {
        "title": "Quantum Chip Achieves Milestone",
        "summary": "Scientists build a 1000-qubit processor.",
        "domain": "Technology",
        "event_date": date(2026, 8, 18),
        "published_at": datetime.now(timezone.utc),
        "source_id": source.id,
        "source_url": "https://test.com/article1",
        "confidence_score": 1.0
    }

    # First check: no duplicate
    existing = dedup.check_duplicate(candidate_1)
    assert existing is None

    # Create event
    event_in, _ = dedup.prepare_event_candidate(candidate_1)
    repo.create(event_in)

    # Second check with identical title and date: duplicate detected!
    candidate_dup = candidate_1.copy()
    candidate_dup["source_url"] = "https://test.com/article2_syndicated"
    existing_dup = dedup.check_duplicate(candidate_dup)

    assert existing_dup is not None
    assert existing_dup.title == "Quantum Chip Achieves Milestone"
