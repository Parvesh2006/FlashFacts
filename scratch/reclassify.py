from app.core.database import SessionLocal
from app.models.event import Event
from app.services.exam_classification_service import ExamClassificationService
db = SessionLocal()
service = ExamClassificationService(db)
events = db.query(Event).all()
updated = 0
for e in events:
    service.classify_event(e)
    updated += 1
db.commit()
print(f'Re-classified {updated} events.')
