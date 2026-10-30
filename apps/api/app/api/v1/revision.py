from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.revision import (
    RevisionItemResponse,
    SaveRevisionRequest,
    RetryRevisionRequest,
    RetryRevisionResponse,
    UpdateRevisionStatusRequest,
    RevisionSummaryResponse,
)
from app.services.revision_service import RevisionService

router = APIRouter()


@router.get("/", response_model=List[RevisionItemResponse])
def list_revision_items(
    exam_name: Optional[str] = None,
    subject: Optional[str] = None,
    status: Optional[str] = Query("all", pattern="^(all|pending|revised)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve private mistake book and smart revision items for the authenticated student."""
    service = RevisionService(db)
    items = service.list_items(
        user_id=user.id,
        exam_name=exam_name,
        subject=subject,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [RevisionItemResponse.model_validate(it) for it in items]


@router.get("/summary", response_model=RevisionSummaryResponse)
def get_revision_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get count totals and filter tags for the student's Mistake Book."""
    service = RevisionService(db)
    return service.get_summary(user_id=user.id)


@router.post("/save", response_model=RevisionItemResponse, status_code=201)
def save_revision_item(
    req: SaveRevisionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually bookmark or add an authentic question to the student's Mistake Book."""
    service = RevisionService(db)
    item = service.save_item(user_id=user.id, req=req)
    return RevisionItemResponse.model_validate(item)


@router.post("/{item_id}/retry", response_model=RetryRevisionResponse)
def retry_revision_question(
    item_id: str,
    req: RetryRevisionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retry a question from the Mistake Book, calculate spaced-repetition timing, and update revision status."""
    service = RevisionService(db)
    try:
        return service.retry_item(
            user_id=user.id, item_id=item_id, selected_answer=req.selected_answer
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{item_id}/status", response_model=RevisionItemResponse)
def update_revision_status(
    item_id: str,
    req: UpdateRevisionStatusRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a question as revised or pending in the student's Mistake Book."""
    service = RevisionService(db)
    try:
        item = service.mark_status(
            user_id=user.id, item_id=item_id, is_revised=req.is_revised
        )
        return RevisionItemResponse.model_validate(item)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{item_id}", status_code=204)
def delete_revision_item(
    item_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a question from the student's Mistake Book."""
    service = RevisionService(db)
    success = service.delete_item(user_id=user.id, item_id=item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return None
