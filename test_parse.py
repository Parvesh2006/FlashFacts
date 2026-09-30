from app.core.database import SessionLocal
from app.services.ai_assistant import FlashFactsAIAssistant

db = SessionLocal()
ai = FlashFactsAIAssistant(db)
filters = ai.parse_query("Give me 5 MCQs from Indian science and technology current affairs")
print(filters)
