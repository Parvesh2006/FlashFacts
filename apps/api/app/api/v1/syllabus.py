from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.syllabus import (
    ExamSyllabusResponse,
    UpdateTopicProgressRequest,
    TopicProgressResponse,
)
from app.services.syllabus_service import SyllabusService

router = APIRouter()


@router.get("/{exam_name}", response_model=ExamSyllabusResponse)
def get_syllabus(
    exam_name: str,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Retrieve authentic, structured syllabus for the specified target examination.
    Includes personal topic completion progress if authenticated (registered or guest session),
    or returns default syllabus topic status without creating an accidental guest database row.
    """
    service = SyllabusService(db)
    user_id = user.id if user else None
    return service.get_exam_syllabus(user_id=user_id, exam_name=exam_name)


@router.post("/progress", response_model=TopicProgressResponse)
def update_syllabus_progress(
    req: UpdateTopicProgressRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a student's completion status (not_started, in_progress, completed, needs_revision)
    and personal revision notes for a specific syllabus topic.
    """
    service = SyllabusService(db)
    try:
        return service.update_progress(
            user_id=user.id,
            topic_id=req.topic_id,
            status=req.status,
            notes=req.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
