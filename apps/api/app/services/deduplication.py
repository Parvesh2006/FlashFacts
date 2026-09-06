from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate
from app.utils.hashing import compute_event_dedup_hash, normalize_text


class DeduplicationService:
    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    def prepare_event_candidate(self, candidate_data: dict) -> Tuple[EventCreate, str]:
        title = candidate_data["title"]
        event_date = candidate_data["event_date"]
        date_str = event_date.isoformat() if hasattr(event_date, "isoformat") else str(event_date)

        dedup_hash = compute_event_dedup_hash(title, date_str)
        event_in = EventCreate(**candidate_data, dedup_hash=dedup_hash)
        return event_in, dedup_hash

    def check_duplicate(self, candidate_data: dict) -> Optional[Event]:
        """
        Check if an event matching title/date dedup hash already exists.
        """
        event_in, dedup_hash = self.prepare_event_candidate(candidate_data)

        # Check by dedup_hash
        existing_event = self.event_repo.get_by_dedup_hash(dedup_hash)
        if existing_event:
            return existing_event

        return None
