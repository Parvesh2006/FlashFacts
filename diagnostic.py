import sys
sys.path.insert(0, 'apps/api')
from app.core.database import SessionLocal
from app.services.ai_assistant import FlashFactsAIAssistant
from app.models.event import Event

db = SessionLocal()
ast = FlashFactsAIAssistant(db)

queries = [
    "Give me 5 MCQs from Indian science and technology current affairs",
    "Give me some MCQs about climate tech companies",
    "Give me 5 TNPSC Group 4 current affairs MCQs"
]

for i, q in enumerate(queries, 1):
    print(f"\n{'='*50}\nQUERY {i}: {q}\n{'='*50}")
    filters = ast.parse_query(q)
    print("A. Parsed Filters:")
    for k, v in filters.items():
        print(f"   {k}: {v}")
    
    print(f"B. output_format: {filters.get('output_format')}")
    print(f"C. mcq_count: {filters.get('mcq_count')}")
    print(f"D. domain: {filters.get('domain')}")
    print(f"E. location_name: {filters.get('location_name')}")
    print(f"F. exam_id / exam_code: {filters.get('exam_id')} / {filters.get('exam_code')}")
    print(f"G. query_text: {filters.get('query_text')}")
    print(f"H. start_date / end_date: {filters.get('start_date')} / {filters.get('end_date')}")
    
    domain = filters.get("domain")
    start_date = filters.get("start_date")
    end_date = filters.get("end_date")
    location_name = filters.get("location_name")
    query_text = filters.get("query_text")

    events = []

    print("\nRetrieval Trace:")
    if location_name:
        loc = ast.location_service.find_by_name(location_name)
        if loc:
            loc_res = ast.location_service.get_location_events(loc.id, limit=50)
            event_ids = [e["id"] for e in loc_res.get("events", [])]
            if event_ids:
                events = ast.db.query(Event).filter(Event.id.in_(event_ids)).all()
            print(f"   -> Location-based retrieval for '{location_name}' returned {len(events)} events.")
        else:
            print(f"   -> Location '{location_name}' not found.")

    if not events:
        if query_text and len(query_text) > 2:
            events, _ = ast.event_repo.search_events(
                query_text=query_text,
                domain=domain,
                start_date=start_date,
                end_date=end_date,
                limit=50,
            )
            print(f"   -> Keyword search for '{query_text}' returned {len(events)} events.")

    if not events:
        events, _ = ast.event_repo.list_events(
            domain=domain,
            start_date=start_date,
            end_date=end_date,
            sort="important",
            limit=50,
        )
        print(f"   -> Fallback list_events (domain={domain}) returned {len(events)} events.")

    print(f"   -> BEFORE domain filter: {len(events)} events")
    if domain:
        events = [e for e in events if e.domain and e.domain.lower() == domain.lower()]
        print(f"   -> AFTER domain filter: {len(events)} events")

    print(f"\nJ. Number of events returned BEFORE scoring: {len(events)}")
    
    scored_events = []
    if events:
        for e in events:
            score = float(e.importance_score or 50)
            if filters.get("importance") == "high":
                if score < 60: score -= 50
            
            exam_rels = []
            if filters.get("exam_id"):
                rel = ast.exam_service.get_event_exam_relevance(e.id)
                exam_rels = rel.get("relevant_exams", [])
                if any(r["exam_id"] == filters["exam_id"] for r in exam_rels):
                    score += 20
                else:
                    score -= 10
            scored_events.append((e, score, exam_rels))
            
        scored_events.sort(key=lambda x: x[1], reverse=True)
    
    final_events = [item for item in scored_events[:10]]
    
    print(f"K. Number returned AFTER scoring: {len(final_events)}")
    
    print("\nI. Exact events returned by _retrieve_candidate_events() (AFTER SCORING):")
    for e, score, rels in final_events:
        print(f"   - ID: {e.id} | Title: {str(e.title)[:40]}... | Domain: {e.domain} | Date: {e.event_date} | Importance: {e.importance_score} | Final Score: {score}")
        if filters.get("exam_id"):
            print(f"     -> Exam Rels: {[(r['exam_id'], r['relevance_score']) for r in rels]}")
        
    # Analysis L, M, N
    print(f"\nL. Location filter restriction: HARD filter (if location is specified, it strictly looks up location events; if it finds any, it skips keyword search. If it finds none, it falls back).")
    print(f"M. Exam filter restriction: SOFT filter (only used for +20/-10 ranking during scoring, doesn't restrict initial retrieval).")
    print(f"N. Domain filter restriction: HARD filter (applied as a list comprehension `[e for e in events if e.domain == domain]` AFTER location/keyword retrieval).")
    
# Specific DB queries for Query 1
print("\n" + "="*50 + "\nDB COUNTS FOR QUERY 1\n" + "="*50)
from sqlalchemy import text
res_tech = db.execute(text("SELECT COUNT(*) FROM events WHERE domain = 'Technology'")).scalar()
res_sci = db.execute(text("SELECT COUNT(*) FROM events WHERE domain = 'Science'")).scalar()
res_ind = db.execute(text("SELECT COUNT(*) FROM events e JOIN event_locations el ON e.id=el.event_id JOIN geographic_locations l ON el.location_id=l.id WHERE l.name='India'")).scalar()
res_ind_tech = db.execute(text("SELECT COUNT(*) FROM events e JOIN event_locations el ON e.id=el.event_id JOIN geographic_locations l ON el.location_id=l.id WHERE l.name='India' AND e.domain='Technology'")).scalar()
res_ind_sci = db.execute(text("SELECT COUNT(*) FROM events e JOIN event_locations el ON e.id=el.event_id JOIN geographic_locations l ON el.location_id=l.id WHERE l.name='India' AND e.domain='Science'")).scalar()

print(f"Total Technology events: {res_tech}")
print(f"Total Science events: {res_sci}")
print(f"Total India-associated events: {res_ind}")
print(f"Total India-associated Technology events: {res_ind_tech}")
print(f"Total India-associated Science events: {res_ind_sci}")

# Compare without location_name="India"
print("\nCompare Q1 without location_name='India':")
filters_no_loc = ast.parse_query(queries[0])
filters_no_loc["location_name"] = None
events_no_loc = ast._retrieve_candidate_events(filters_no_loc)
print(f"Returned events without location filter: {len(events_no_loc)}")
