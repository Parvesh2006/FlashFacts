from app.core.database import SessionLocal
from app.models.event import Event
from app.utils.hashing import fix_mojibake

db = SessionLocal()
events = db.query(Event).all()
updated = 0
for e in events:
    changed = False
    new_t = fix_mojibake(e.title)
    if new_t != e.title:
        e.title = new_t
        changed = True
    
    new_s = fix_mojibake(e.summary)
    if new_s != e.summary:
        e.summary = new_s
        changed = True
    
    if changed:
        updated += 1

db.commit()
print(f'Fixed mojibake in {updated} events.')
