from app.core.database import SessionLocal
from app.models.event import Event
from app.utils.hashing import fix_mojibake
from app.services.classification import KeywordDomainClassifier

db = SessionLocal()
classifier = KeywordDomainClassifier()
events = db.query(Event).all()
updated = 0
for e in events:
    changed = False
    new_title = fix_mojibake(e.title)
    if new_title != e.title:
        e.title = new_title
        changed = True
        
    new_summary = fix_mojibake(e.summary)
    if new_summary != e.summary:
        e.summary = new_summary
        changed = True
        
    if e.why_it_matters:
        new_why = fix_mojibake(e.why_it_matters)
        if new_why != e.why_it_matters:
            e.why_it_matters = new_why
            changed = True

    new_domain = classifier.classify(e.title, e.summary, default_domain=e.domain)
    if new_domain != e.domain:
        e.domain = new_domain
        changed = True

    if changed:
        updated += 1

db.commit()
print(f'Fixed {updated} events.')
