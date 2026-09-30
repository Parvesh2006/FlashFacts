import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.services.ai_assistant import FlashFactsAIAssistant
db = SessionLocal()
assistant = FlashFactsAIAssistant(db)
filters = assistant.parse_query("Create 5 MCQs from recent Indian science and technology current affairs.")

location_name = filters.get("location_name")
query_text = filters.get("query_text")
domain = filters.get("domain")

print('loc:', location_name, 'domain:', domain)

events = []
if location_name:
    loc = assistant.location_service.find_by_name(location_name)
    if loc:
        loc_res = assistant.location_service.get_location_events(loc.id, limit=50)
        event_ids = [e["id"] for e in loc_res.get("events", [])]
        print('event_ids from loc:', event_ids)
        if event_ids:
            from app.models.event import Event
            events = db.query(Event).filter(Event.id.in_(event_ids)).all()
print('after loc:', len(events))
