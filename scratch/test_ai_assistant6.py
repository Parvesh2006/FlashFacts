import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.services.ai_assistant import FlashFactsAIAssistant
db = SessionLocal()
assistant = FlashFactsAIAssistant(db)
res = assistant.answer_question("Create 5 MCQs from recent Indian science and technology current affairs.")
print("Events found:", res.get("events_found"))
if res.get("events_found") > 0:
    print("Answer excerpt:", res.get("answer")[:200])
