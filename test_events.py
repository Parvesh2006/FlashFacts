from app.core.database import SessionLocal
from app.repositories.event_repository import EventRepository

db = SessionLocal()
repo = EventRepository(db)
events, _ = repo.list_events(geography='India', domain='Science')
for e in events:
    print(e.domain, e.title)
