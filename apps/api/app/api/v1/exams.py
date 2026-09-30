from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.exam_intelligence import ExamIntelligenceService, EXAM_DEFINITIONS

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("")
def get_exams():
    """Return all supported exam categories."""
    return [
        {
            "id": d["id"],
            "name": d["name"],
            "code": d["code"],
            "description": d["description"],
            "category": d["category"],
        }
        for d in EXAM_DEFINITIONS.values()
    ]


@router.get("/{exam_id}")
def get_exam(exam_id: str):
    """Return details of a specific exam."""
    exam = EXAM_DEFINITIONS.get(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return {
        "id": exam["id"],
        "name": exam["name"],
        "code": exam["code"],
        "description": exam["description"],
        "category": exam["category"],
        "section_label": exam["section_label"],
    }


@router.get("/{exam_id}/events")
def get_exam_events(
    exam_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Return current-affairs events relevant to a specific exam."""
    if exam_id not in EXAM_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Exam not found")
    service = ExamIntelligenceService(db)
    return service.get_exam_events(exam_id, limit=limit, offset=offset)


@router.get("/{exam_id}/events/{event_id}/mcq")
def get_exam_event_mcq(
    exam_id: str,
    event_id: int,
    count: int = Query(3, ge=1, le=5),
    db: Session = Depends(get_db),
):
    """Generate MCQs for a specific event in the context of an exam."""
    if exam_id not in EXAM_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Exam not found")
    service = ExamIntelligenceService(db)
    result = service.generate_mcqs(event_id, exam_id=exam_id, count=count)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
