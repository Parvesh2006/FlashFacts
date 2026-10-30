from typing import List, Optional, Tuple
from sqlalchemy import or_, desc, distinct
from sqlalchemy.orm import Session
from app.models.pyq_paper import PYQPaper
from app.schemas.pyq_paper import PYQPaperCreate, PYQPaperFilterOptions


class PYQPaperRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, paper_id: str) -> Optional[PYQPaper]:
        return self.db.query(PYQPaper).filter(PYQPaper.id == paper_id).first()

    def get_by_checksum(self, checksum: str) -> Optional[PYQPaper]:
        if not checksum:
            return None
        return self.db.query(PYQPaper).filter(PYQPaper.checksum_sha256 == checksum).first()

    def list_papers(
        self,
        category: Optional[str] = None,
        exam_name: Optional[str] = None,
        year: Optional[int] = None,
        subject: Optional[str] = None,
        language: Optional[str] = None,
        availability: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[PYQPaper], int]:
        query = self.db.query(PYQPaper)

        if category:
            query = query.filter(PYQPaper.exam_category.ilike(f"%{category.strip()}%"))
        if exam_name:
            query = query.filter(PYQPaper.exam_name.ilike(f"%{exam_name.strip()}%"))
        if year:
            query = query.filter(PYQPaper.year == year)
        if subject:
            query = query.filter(PYQPaper.subject.ilike(f"%{subject.strip()}%"))
        if language:
            query = query.filter(PYQPaper.language.ilike(f"%{language.strip()}%"))
        if availability:
            query = query.filter(PYQPaper.availability_status == availability.strip())
        if search_query:
            sq = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    PYQPaper.title.ilike(sq),
                    PYQPaper.exam_name.ilike(sq),
                    PYQPaper.subject.ilike(sq),
                    PYQPaper.paper_code.ilike(sq),
                    PYQPaper.authority.ilike(sq),
                )
            )

        total = query.count()
        papers = (
            query.order_by(desc(PYQPaper.year), desc(PYQPaper.exam_date), PYQPaper.exam_name)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return papers, total

    def get_filter_options(self) -> PYQPaperFilterOptions:
        categories = [
            c[0]
            for c in self.db.query(PYQPaper.exam_category)
            .distinct()
            .order_by(PYQPaper.exam_category)
            .all()
            if c[0]
        ]
        exams = [
            e[0]
            for e in self.db.query(PYQPaper.exam_name)
            .distinct()
            .order_by(PYQPaper.exam_name)
            .all()
            if e[0]
        ]
        years = [
            y[0]
            for y in self.db.query(PYQPaper.year)
            .distinct()
            .order_by(desc(PYQPaper.year))
            .all()
            if y[0]
        ]
        subjects = [
            s[0]
            for s in self.db.query(PYQPaper.subject)
            .distinct()
            .order_by(PYQPaper.subject)
            .all()
            if s[0]
        ]
        languages = [
            l[0]
            for l in self.db.query(PYQPaper.language)
            .distinct()
            .order_by(PYQPaper.language)
            .all()
            if l[0]
        ]

        return PYQPaperFilterOptions(
            categories=categories,
            exams=exams,
            years=years,
            subjects=subjects,
            languages=languages,
        )

    def create(self, paper_in: PYQPaperCreate) -> PYQPaper:
        data = paper_in.model_dump()
        paper = PYQPaper(**data)
        self.db.add(paper)
        self.db.commit()
        self.db.refresh(paper)
        return paper

    def increment_download(self, paper_id: str) -> Optional[PYQPaper]:
        paper = self.get(paper_id)
        if paper:
            paper.download_count += 1
            self.db.commit()
            self.db.refresh(paper)
        return paper
