import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.services.ai_assistant import FlashFactsAIAssistant, EXAM_DEFINITIONS
from app.models.event import Event
db = SessionLocal()
assistant = FlashFactsAIAssistant(db)
filters = assistant.parse_query("Create 5 MCQs from recent Indian science and technology current affairs.")

location_name = filters.get("location_name")
query_text = filters.get("query_text")
domain = filters.get("domain")
start_date = filters.get("start_date")
end_date = filters.get("end_date")
exam_id = filters.get("exam_id")
events = []
print("location_name:", location_name)
if location_name:
    loc = assistant.location_service.find_by_name(location_name)
    if loc:
        loc_res = assistant.location_service.get_location_events(loc.id, limit=50)
        event_ids = [e["id"] for e in loc_res.get("events", [])]
        if event_ids:
            events = db.query(Event).filter(Event.id.in_(event_ids)).all()
print("after location, events:", len(events))
if not events:
    if query_text and len(query_text) > 2:
        events, _ = assistant.event_repo.search_events(
            query_text=query_text,
            domain=domain,
            start_date=start_date,
            end_date=end_date,
            exam=exam_id,
            geography=location_name,
            limit=50,
        )
print("after search_events, events:", len(events))
if not events:
    if domain or exam_id or location_name or not query_text or len(query_text) <= 2:
        events, _ = assistant.event_repo.list_events(
            domain=domain,
            start_date=start_date,
            end_date=end_date,
            exam=exam_id,
            geography=location_name,
            sort="important",
            limit=50,
        )
print("after list_events, events:", len(events))
if domain:
    events = [e for e in events if e.domain and e.domain.lower() == domain.lower()]
print("after domain filter, events:", len(events))
