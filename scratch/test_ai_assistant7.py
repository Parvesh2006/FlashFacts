import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.services.ai_assistant import FlashFactsAIAssistant
db = SessionLocal()
assistant = FlashFactsAIAssistant(db)
filters = assistant.parse_query("Create 5 MCQs from recent Indian science and technology current affairs.")
print("Filters:", filters)
events, _ = assistant.event_repo.list_events(
    domain=filters.get('domain'),
    start_date=filters.get('start_date'),
    end_date=filters.get('end_date'),
    exam=filters.get('exam_id'),
    geography=filters.get('location_name'),
    sort='important',
    limit=50
)
print("list_events returned:", len(events))
