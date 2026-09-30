"""
Product Verification Script - writes results to JSON for inspection.
Run: $env:PYTHONPATH="apps/api"; python verify_product.py
"""
import sys, os, json, traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps", "api"))

from app.core.database import SessionLocal, Base, engine
from app.services.ai_assistant import FlashFactsAIAssistant

QUERIES = [
    ("Q1_india",    "What are the latest Indian current affairs?"),
    ("Q2_tn",       "What are the important Tamil Nadu current affairs?"),
    ("Q3_tnpsc",    "Give me important current affairs for TNPSC Group 4."),
    ("Q4_domain",   "Give me Indian science and technology current affairs from this month."),
    ("Q5_mcq",      "Create 5 MCQs from these current affairs."),
    ("Q6_noevid",   "What happened in Antarctica in 2050?"),
]

def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    assistant = FlashFactsAIAssistant(db)
    report = {}

    for key, question in QUERIES:
        try:
            res = assistant.answer_question(question)
            # strip non-ascii for safe JSON serialization
            answer_safe = res.get("answer","").encode("ascii","replace").decode("ascii")
            sources = res.get("sources") or []
            filters = res.get("filters") or {}
            report[key] = {
                "question": question,
                "events_found": res.get("events_found",0),
                "provider": res.get("provider",""),
                "filters": filters,
                "sources": sources[:6],
                "answer_ascii": answer_safe[:1000],
                "answer_length": len(res.get("answer","")),
                "mlops_metadata": res.get("mlops_metadata"),
            }
        except Exception as exc:
            report[key] = {"question": question, "error": str(exc), "traceback": traceback.format_exc()}

    out_path = "verify_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"Results written to {out_path}")
    db.close()

if __name__ == "__main__":
    run()
