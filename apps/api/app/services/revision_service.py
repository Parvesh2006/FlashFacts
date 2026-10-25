from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func, distinct

from app.models.revision_item import RevisionItem
from app.services.mock_test_service import MockTestService
from app.schemas.revision import (
    RevisionItemResponse,
    SaveRevisionRequest,
    RetryRevisionResponse,
    RevisionSummaryResponse,
)


class RevisionService:
    def __init__(self, db: Session):
        self.db = db

    def list_items(
        self,
        user_id: str,
        exam_name: Optional[str] = None,
        subject: Optional[str] = None,
        status: Optional[str] = None,  # "pending", "revised", "all"
        limit: int = 50,
        offset: int = 0,
    ) -> List[RevisionItem]:
        stmt = select(RevisionItem).where(RevisionItem.user_id == user_id)

        if exam_name:
            stmt = stmt.where(RevisionItem.exam_name.ilike(f"%{exam_name}%"))
        if subject:
            stmt = stmt.where(RevisionItem.subject.ilike(f"%{subject}%"))
        if status == "pending":
            stmt = stmt.where(RevisionItem.is_revised == False)
        elif status == "revised":
            stmt = stmt.where(RevisionItem.is_revised == True)

        stmt = stmt.order_by(
            RevisionItem.is_revised.asc(),
            RevisionItem.mistake_count.desc(),
            desc(RevisionItem.updated_at),
        ).offset(offset).limit(limit)

        return self.db.execute(stmt).scalars().all()

    def get_summary(self, user_id: str) -> RevisionSummaryResponse:
        total = (
            self.db.query(func.count(RevisionItem.id))
            .filter(RevisionItem.user_id == user_id)
            .scalar()
            or 0
        )
        pending = (
            self.db.query(func.count(RevisionItem.id))
            .filter(RevisionItem.user_id == user_id, RevisionItem.is_revised == False)
            .scalar()
            or 0
        )
        revised = total - pending

        exams = [
            r[0]
            for r in self.db.execute(
                select(distinct(RevisionItem.exam_name))
                .where(RevisionItem.user_id == user_id)
                .order_by(RevisionItem.exam_name)
            ).all()
            if r[0]
        ]

        subjects = [
            r[0]
            for r in self.db.execute(
                select(distinct(RevisionItem.subject))
                .where(RevisionItem.user_id == user_id, RevisionItem.subject.is_not(None))
                .order_by(RevisionItem.subject)
            ).all()
            if r[0]
        ]

        return RevisionSummaryResponse(
            total_count=total,
            pending_count=pending,
            revised_count=revised,
            exams=exams,
            subjects=subjects,
        )

    def save_item(self, user_id: str, req: SaveRevisionRequest) -> RevisionItem:
        existing = (
            self.db.query(RevisionItem)
            .filter(
                RevisionItem.user_id == user_id,
                RevisionItem.question_text == req.question_text,
            )
            .first()
        )

        if existing:
            existing.mistake_count += 1
            existing.is_revised = False
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        item = RevisionItem(
            user_id=user_id,
            question_source=req.question_source,
            exam_name=req.exam_name,
            subject=req.subject or "General Studies",
            topic=req.topic,
            question_text=req.question_text,
            options=req.options,
            selected_answer=req.selected_answer,
            correct_answer=req.correct_answer,
            explanation=req.explanation,
            outcome="saved",
            mistake_count=1,
            is_revised=False,
            next_review_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def retry_item(
        self, user_id: str, item_id: str, selected_answer: str
    ) -> RetryRevisionResponse:
        item = (
            self.db.query(RevisionItem)
            .filter(RevisionItem.id == item_id, RevisionItem.user_id == user_id)
            .first()
        )
        if not item:
            raise ValueError("Revision item not found")

        selected_letter = MockTestService._answer_letter(selected_answer, item.options)
        correct_letter = MockTestService._answer_letter(item.correct_answer, item.options) or item.correct_answer

        is_correct = (
            selected_letter is not None
            and correct_letter is not None
            and selected_letter == correct_letter
        )

        now = datetime.now(timezone.utc)
        item.last_reviewed_at = now
        item.selected_answer = selected_letter or selected_answer

        if is_correct:
            item.is_revised = True
            # Spaced repetition scheduling: interval grows with mastery
            interval_days = 3 if item.mistake_count <= 1 else 7
            item.next_review_at = now + timedelta(days=interval_days)
        else:
            item.mistake_count += 1
            item.is_revised = False
            item.next_review_at = now + timedelta(days=1)

        item.updated_at = now
        self.db.commit()
        self.db.refresh(item)

        return RetryRevisionResponse(
            id=item.id,
            is_correct=is_correct,
            selected_letter=selected_letter,
            correct_letter=correct_letter,
            mistake_count=item.mistake_count,
            is_revised=item.is_revised,
            next_review_at=item.next_review_at,
            explanation=item.explanation,
        )

    def mark_status(self, user_id: str, item_id: str, is_revised: bool) -> RevisionItem:
        item = (
            self.db.query(RevisionItem)
            .filter(RevisionItem.id == item_id, RevisionItem.user_id == user_id)
            .first()
        )
        if not item:
            raise ValueError("Revision item not found")

        item.is_revised = is_revised
        item.updated_at = datetime.now(timezone.utc)
        if is_revised:
            item.last_reviewed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_item(self, user_id: str, item_id: str) -> bool:
        item = (
            self.db.query(RevisionItem)
            .filter(RevisionItem.id == item_id, RevisionItem.user_id == user_id)
            .first()
        )
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True
