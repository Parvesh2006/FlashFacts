import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.services.ai_assistant import FlashFactsAIAssistant, EXAM_DEFINITIONS
db = SessionLocal()
assistant = FlashFactsAIAssistant(db)
filters = assistant.parse_query("Create 5 MCQs from recent Indian science and technology current affairs.")
events, _ = assistant.event_repo.list_events(
    domain=filters.get('domain'),
    start_date=filters.get('start_date'),
    end_date=filters.get('end_date'),
    exam=filters.get('exam_id'),
    geography=filters.get('location_name'),
    sort='important',
    limit=50
)
events = [e for e in events if e.domain and e.domain.lower() == filters.get('domain').lower()]
print("after domain filter:", len(events))
exam_def = EXAM_DEFINITIONS.get("tnpsc-group-4")
scored_events = []
for e in events:
    score = e.importance_score or 50
    try:
        rel = assistant.exam_service.score_event_for_exam(e, exam_def)
    except Exception as e:
        print("EXCEPTION:", e)
        break
    score += rel.get("relevance_score", 0)
    scored_events.append((e, score))
print("Scored events:", len(scored_events))
