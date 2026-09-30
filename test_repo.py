from app.core.database import SessionLocal
from app.repositories.event_repository import EventRepository
from app.models.event import Event

db = SessionLocal()
repo = EventRepository(db)
events, _ = repo.search_events(query_text='5 mcqs from indian science technology', domain='Science,Technology')
print('events length:', len(events))
for e in events:
    print(e.title)
