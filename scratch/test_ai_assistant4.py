import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.services.ai_assistant import FlashFactsAIAssistant
db = SessionLocal()
assistant = FlashFactsAIAssistant(db)
filters = assistant.parse_query("Create 5 MCQs from recent Indian science and technology current affairs.")
print('Filters:', filters)
events = assistant._retrieve_candidate_events(filters)
print('Got', len(events), 'events for query 7.')
