from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ai_assistant import FlashFactsAIAssistant

router = APIRouter(prefix="/ask", tags=["Ask AI"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language question")
    history: Optional[List[Dict[str, Any]]] = Field(None, description="Conversational follow-up history")


class SourceItem(BaseModel):
    name: str
    url: Optional[str] = None
    date: Optional[str] = None


class AskResponseSchema(BaseModel):
    answer: str
    filters: Optional[Dict[str, Any]] = None
    sources: Optional[List[SourceItem]] = None
    events_found: Optional[int] = 0
    provider: Optional[str] = "ai"


@router.post("", response_model=AskResponseSchema)
def ask_ai_assistant(req: AskRequest, db: Session = Depends(get_db)):
    """Process natural language question and return grounded exam-focused answer."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    assistant = FlashFactsAIAssistant(db)
    result = assistant.answer_question(req.question, history=req.history)
    return result
