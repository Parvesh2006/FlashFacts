import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.repositories.event_repository import EventRepository
db = SessionLocal()
repo = EventRepository(db)
events, total = repo.list_events(domain='Technology', geography='India', start_date=None, end_date=None, limit=50)
print('Found list_events:', total)
events, total = repo.search_events(query_text="5 from recent indian science technology", domain='Technology', geography='India', start_date=None, end_date=None, limit=50)
print('Found search_events:', total)
