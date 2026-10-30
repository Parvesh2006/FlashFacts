from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, distinct
from app.models.pyq import PYQ
from app.models.pyq_bookmark import PYQBookmark


class PYQRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, pyq_id: int) -> Optional[PYQ]:
        return self.db.execute(select(PYQ).where(PYQ.id == pyq_id)).scalar_one_or_none()

    def list_by_exam(
        self,
        exam_name: Optional[str] = None,
        year: Optional[int] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        language: Optional[str] = None,
        question_type: Optional[str] = None,
        search_query: Optional[str] = None,
        include_invalid: bool = False,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(PYQ)

        if not include_invalid:
            stmt = stmt.where(PYQ.quality_status == "valid", PYQ.is_verified == True)

        if question_type:
            stmt = stmt.where(PYQ.question_type == question_type)
        if exam_name:
            stmt = stmt.where(PYQ.exam_name.ilike(f"%{exam_name}%"))
        if year:
            stmt = stmt.where(PYQ.year == year)
        if subject:
            stmt = stmt.where(PYQ.subject.ilike(f"%{subject}%"))
        if topic:
            stmt = stmt.where(PYQ.topic.ilike(f"%{topic}%"))
        if language:
            stmt = stmt.where(PYQ.language.ilike(f"%{language}%"))
        if search_query:
            term = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    PYQ.question_text.ilike(term),
                    PYQ.subject.ilike(term),
                    PYQ.topic.ilike(term),
                    PYQ.explanation.ilike(term),
                )
            )

        stmt = stmt.order_by(PYQ.year.desc(), PYQ.id.asc()).offset(offset).limit(limit)
        pyqs = self.db.execute(stmt).scalars().all()

        bookmarked_ids = set()
        if user_id:
            bm_stmt = select(PYQBookmark.pyq_id).where(PYQBookmark.user_id == user_id)
            bookmarked_ids = set(self.db.execute(bm_stmt).scalars().all())

        results = []
        for p in pyqs:
            item = {
                "id": p.id,
                "exam_name": p.exam_name,
                "year": p.year,
                "paper_name": p.paper_name,
                "subject": p.subject,
                "topic": p.topic,
                "source": p.source,
                "language": p.language or "en",
                "is_verified": p.is_verified if p.is_verified is not None else True,
                "question_type": getattr(p, "question_type", "syllabus_practice") or "syllabus_practice",
                "quality_status": getattr(p, "quality_status", "valid") or "valid",
                "question_text": p.question_text,
                "options": p.options,
                "correct_answer": p.correct_answer,
                "explanation": p.explanation,
                "is_bookmarked": p.id in bookmarked_ids,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            results.append(item)

        return results

    def create(self, **kwargs) -> PYQ:
        pyq = PYQ(**kwargs)
        self.db.add(pyq)
        self.db.commit()
        self.db.refresh(pyq)
        return pyq

    def toggle_bookmark(self, user_id: str, pyq_id: int) -> bool:
        bm = self.db.execute(
            select(PYQBookmark).where(
                PYQBookmark.user_id == user_id,
                PYQBookmark.pyq_id == pyq_id,
            )
        ).scalar_one_or_none()

        if bm:
            self.db.delete(bm)
            self.db.commit()
            return False
        else:
            new_bm = PYQBookmark(user_id=user_id, pyq_id=pyq_id)
            self.db.add(new_bm)
            self.db.commit()
            return True

    def list_bookmarks(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        stmt = (
            select(PYQ)
            .join(PYQBookmark, PYQBookmark.pyq_id == PYQ.id)
            .where(PYQBookmark.user_id == user_id)
            .order_by(PYQBookmark.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        pyqs = self.db.execute(stmt).scalars().all()
        return [
            {
                "id": p.id,
                "exam_name": p.exam_name,
                "year": p.year,
                "paper_name": p.paper_name,
                "subject": p.subject,
                "topic": p.topic,
                "source": p.source,
                "language": p.language or "en",
                "is_verified": p.is_verified if p.is_verified is not None else True,
                "question_type": getattr(p, "question_type", "syllabus_practice") or "syllabus_practice",
                "quality_status": getattr(p, "quality_status", "valid") or "valid",
                "rejection_reason": getattr(p, "rejection_reason", None),
                "question_text": p.question_text,
                "options": p.options,
                "correct_answer": p.correct_answer,
                "explanation": p.explanation,
                "is_bookmarked": True,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            for p in pyqs
        ]

    def get_filter_options(self, exam_name: Optional[str] = None) -> Dict[str, Any]:
        base = select(PYQ).where(PYQ.quality_status == "valid", PYQ.is_verified == True)
        if exam_name:
            base = base.where(PYQ.exam_name.ilike(f"%{exam_name}%"))

        exams = [r[0] for r in self.db.execute(select(distinct(PYQ.exam_name)).where(PYQ.quality_status == "valid", PYQ.is_verified == True).order_by(PYQ.exam_name)).all() if r[0]]

        years_stmt = select(distinct(PYQ.year)).where(PYQ.quality_status == "valid", PYQ.is_verified == True)
        if exam_name:
            years_stmt = years_stmt.where(PYQ.exam_name.ilike(f"%{exam_name}%"))
        years = [r[0] for r in self.db.execute(years_stmt.order_by(PYQ.year.desc())).all() if r[0]]

        subjects_stmt = select(distinct(PYQ.subject)).where(PYQ.subject.is_not(None), PYQ.quality_status == "valid", PYQ.is_verified == True)
        if exam_name:
            subjects_stmt = subjects_stmt.where(PYQ.exam_name.ilike(f"%{exam_name}%"))
        subjects = [r[0] for r in self.db.execute(subjects_stmt.order_by(PYQ.subject)).all() if r[0]]

        topics_stmt = select(distinct(PYQ.topic)).where(PYQ.topic.is_not(None), PYQ.quality_status == "valid", PYQ.is_verified == True)
        if exam_name:
            topics_stmt = topics_stmt.where(PYQ.exam_name.ilike(f"%{exam_name}%"))
        topics = [r[0] for r in self.db.execute(topics_stmt.order_by(PYQ.topic)).all() if r[0]]

        count_stmt = select(func.count(PYQ.id)).where(PYQ.quality_status == "valid", PYQ.is_verified == True)
        if exam_name:
            count_stmt = count_stmt.where(PYQ.exam_name.ilike(f"%{exam_name}%"))
        total = self.db.execute(count_stmt).scalar() or 0

        return {
            "exams": exams,
            "years": years,
            "subjects": subjects,
            "topics": topics,
            "total_count": total,
        }
