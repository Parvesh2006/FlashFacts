import asyncio
import os
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.event import Base
from app.services.ai_assistant import FlashFactsAIAssistant
from app.core.config import settings

# Wait, we need the test database or just dev database.
engine = create_engine("sqlite:///./flashfacts_dev.db")
SessionLocal = sessionmaker(bind=engine)

def main():
    db = SessionLocal()
    assistant = FlashFactsAIAssistant(db)

    questions = [
        "What are the latest important developments relevant to TNPSC Group 4?",
        "Explain the Indian Constitution in simple Tamil.",
        "Why is this event important for Tamil Nadu government exam preparation?"
    ]

    for q in questions:
        print(f"\nQ: {q}")
        try:
            res = assistant.answer_question(q)
            # print answer with encoding handling
            print(res["answer"].encode("utf-8").decode("utf-8"))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
