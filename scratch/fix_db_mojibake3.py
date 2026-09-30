from app.core.database import SessionLocal
from app.models.exam_intelligence import EventExamMetadata
from app.utils.hashing import fix_mojibake

db = SessionLocal()
meta = db.query(EventExamMetadata).all()
updated = 0
for m in meta:
    changed = False
    
    if m.why_it_matters:
        new_w = fix_mojibake(m.why_it_matters)
        if new_w != m.why_it_matters:
            m.why_it_matters = new_w
            changed = True
            
    if m.exam_facts:
        new_f = fix_mojibake(m.exam_facts)
        if new_f != m.exam_facts:
            m.exam_facts = new_f
            changed = True

    if m.question_angles:
        new_q = fix_mojibake(m.question_angles)
        if new_q != m.question_angles:
            m.question_angles = new_q
            changed = True

    if m.relevance_factors:
        new_r = fix_mojibake(m.relevance_factors)
        if new_r != m.relevance_factors:
            m.relevance_factors = new_r
            changed = True

    if changed:
        updated += 1

db.commit()
print(f'Fixed mojibake in {updated} metadata records.')
