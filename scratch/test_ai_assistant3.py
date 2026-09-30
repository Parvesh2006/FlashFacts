import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.repositories.event_repository import EventRepository
from app.services.exam_classification_service import ExamClassificationService
from app.services.ai_assistant import EXAM_DEFINITIONS
db = SessionLocal()
repo = EventRepository(db)
svc = ExamClassificationService(db)
events, _ = repo.list_events(domain='Technology', geography='India', start_date=None, end_date=None, limit=50)
print('Got', len(events))
for e in events[:1]:
    exam_def = EXAM_DEFINITIONS.get("tnpsc-group-4")
    try:
        rel = svc.score_event_for_exam(e, exam_def)
        print('Rel:', rel)
    except Exception as exc:
        print('Error:', exc)
