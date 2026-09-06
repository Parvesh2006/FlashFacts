from collections import defaultdict
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.repositories.event_repository import EventRepository
from app.schemas.calendar import CalendarResponse, CalendarDayStat


class CalendarService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)

    def get_monthly_calendar(self, month_str: str) -> CalendarResponse:
        """
        month_str format: 'YYYY-MM' (e.g., '2026-08')
        """
        parts = month_str.split("-")
        if len(parts) != 2:
            raise ValueError("Invalid month format. Expected 'YYYY-MM'.")

        year = int(parts[0])
        month = int(parts[1])

        events = self.event_repo.get_events_for_month(year, month)

        # Group by date string: 'YYYY-MM-DD'
        day_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"total": 0, "domains": defaultdict(int)})

        for ev in events:
            date_key = ev.event_date.strftime("%Y-%m-%d")
            day_stats[date_key]["total"] += 1
            day_stats[date_key]["domains"][ev.domain] += 1

        # Format sorted days list
        sorted_days = []
        for date_key in sorted(day_stats.keys()):
            sorted_days.append(
                CalendarDayStat(
                    date=date_key,
                    total=day_stats[date_key]["total"],
                    domains=dict(day_stats[date_key]["domains"])
                )
            )

        return CalendarResponse(
            month=month_str,
            days=sorted_days
        )
