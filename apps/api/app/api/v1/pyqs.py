import os
import re
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user_optional, get_current_user
from app.models.user import User
from app.models.pyq import PYQ
from app.models.pyq_paper import PYQPaper
from app.schemas.pyq import (
    PYQResponse,
    PYQCreate,
    PYQFiltersResponse,
    PYQBookmarkResponse,
)
from app.schemas.pyq_paper import (
    PYQPaperResponse,
    PYQPaperCreate,
    PYQPaperListResponse,
    PYQPaperFilterOptions,
)
from app.repositories.pyq_repository import PYQRepository
from app.repositories.pyq_paper_repository import PYQPaperRepository

router = APIRouter()

def get_base_storage_dir() -> Path:
    env_dir = os.environ.get("PYQ_STORAGE_DIR")
    if env_dir and Path(env_dir).is_dir():
        return Path(env_dir).resolve()

    search_roots = [Path.cwd().resolve()] + list(Path(__file__).resolve().parents)
    for root in search_roots:
        candidate = root / "data" / "pyq_pdfs"
        if candidate.is_dir():
            return candidate.resolve()
        candidate_direct = root / "pyq_pdfs"
        if candidate_direct.is_dir():
            return candidate_direct.resolve()

    return (Path(__file__).resolve().parents[5] / "data" / "pyq_pdfs").resolve()


def resolve_safe_pdf_path(storage_path: Optional[str]) -> Optional[Path]:
    """
    Validates that a local PDF file path does not escape storage directory (Path Traversal Protection)
    and actually exists as a valid regular file.
    """
    if not storage_path:
        return None
    base_dir = get_base_storage_dir()
    p = Path(storage_path)

    # Protect against path traversal and resolve candidate
    candidates = []
    if p.is_absolute():
        candidates.append(p.resolve())
    else:
        candidates.append((base_dir / p.name).resolve())
        candidates.append((base_dir.parent / p).resolve())
        candidates.append((base_dir / p).resolve())

    for c in candidates:
        try:
            # Check path containment within approved storage
            if c.is_file() and (base_dir in c.parents or c.parent == base_dir):
                return c
        except Exception:
            continue
    return None


def verify_pdf_magic_bytes(file_path: Path) -> bool:
    """Verifies that the document begins with the standard %PDF- magic signature."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
            return header == b"%PDF-"
    except Exception:
        return False


# =========================================================================
# PYQ PAPERS (Genuine Full Examination Question Paper PDFs)
# =========================================================================

@router.get("/papers/filters", response_model=PYQPaperFilterOptions)
def get_pyq_paper_filters(db: Session = Depends(get_db)):
    """Retrieve distinct categories, exams, years, subjects, and languages from verified question papers."""
    repo = PYQPaperRepository(db)
    return repo.get_filter_options()


@router.get("/papers", response_model=PYQPaperListResponse)
def list_pyq_papers(
    category: Optional[str] = Query(None, description="Filter by exam category (e.g. TNPSC, UPSC, SSC, RRB)"),
    exam_name: Optional[str] = Query(None, description="Filter by exam name (e.g. TNPSC Group 4, UPSC CSE Prelims)"),
    year: Optional[int] = Query(None, description="Filter by examination year"),
    subject: Optional[str] = Query(None, description="Filter by subject or paper title"),
    language: Optional[str] = Query(None, description="Filter by paper language"),
    q: Optional[str] = Query(None, description="Keyword search across paper title, exam name, subject, or code"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Browse verified previous-year question papers with multi-attribute filtering and pagination."""
    repo = PYQPaperRepository(db)
    papers, total = repo.list_papers(
        category=category,
        exam_name=exam_name,
        year=year,
        subject=subject,
        language=language,
        search_query=q,
        limit=limit,
        offset=offset,
    )

    items = []
    for p in papers:
        local_file = resolve_safe_pdf_path(p.storage_path)
        items.append(
            PYQPaperResponse(
                id=p.id,
                exam_name=p.exam_name,
                exam_category=p.exam_category,
                year=p.year,
                exam_date=p.exam_date,
                subject=p.subject,
                language=p.language,
                shift_session=p.shift_session,
                paper_code=p.paper_code,
                title=p.title,
                source_url=p.source_url,
                pdf_url=p.pdf_url,
                authority=p.authority,
                checksum_sha256=p.checksum_sha256,
                verification_status=p.verification_status,
                redistribution_status=p.redistribution_status,
                file_size_bytes=p.file_size_bytes,
                mime_type=p.mime_type,
                availability_status=p.availability_status,
                download_count=p.download_count,
                created_at=p.created_at,
                updated_at=p.updated_at,
                has_local_file=local_file is not None,
            )
        )

    return PYQPaperListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/papers/{paper_id}", response_model=PYQPaperResponse)
def get_pyq_paper(paper_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata and provenance for a single verified question paper."""
    repo = PYQPaperRepository(db)
    paper = repo.get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Question paper not found")

    local_file = resolve_safe_pdf_path(paper.storage_path)
    return PYQPaperResponse(
        id=paper.id,
        exam_name=paper.exam_name,
        exam_category=paper.exam_category,
        year=paper.year,
        exam_date=paper.exam_date,
        subject=paper.subject,
        language=paper.language,
        shift_session=paper.shift_session,
        paper_code=paper.paper_code,
        title=paper.title,
        source_url=paper.source_url,
        pdf_url=paper.pdf_url,
        authority=paper.authority,
        checksum_sha256=paper.checksum_sha256,
        verification_status=paper.verification_status,
        redistribution_status=paper.redistribution_status,
        file_size_bytes=paper.file_size_bytes,
        mime_type=paper.mime_type,
        availability_status=paper.availability_status,
        download_count=paper.download_count,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
        has_local_file=local_file is not None,
    )


@router.get("/papers/{paper_id}/pdf")
def view_pyq_paper_pdf(paper_id: str, db: Session = Depends(get_db)):
    """
    Open or stream the verified question paper PDF for browser inline viewing.
    Falls back gracefully to the verified official source URL if local file is unavailable.
    """
    repo = PYQPaperRepository(db)
    paper = repo.get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Question paper not found")

    if paper.availability_status == "restricted":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this document is restricted by the issuing examination authority.",
        )

    # 1. Check local storage
    local_file = resolve_safe_pdf_path(paper.storage_path)
    if local_file:
        if not verify_pdf_magic_bytes(local_file):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stored document failed PDF signature validation.",
            )
        return FileResponse(
            path=str(local_file),
            media_type="application/pdf",
            filename=f"{paper.id}.pdf",
        )

    # 2. Redirect to verified direct PDF URL if available
    if paper.pdf_url:
        return RedirectResponse(url=paper.pdf_url, status_code=307)

    # 3. Fallback to original source page
    if paper.source_url:
        return RedirectResponse(url=paper.source_url, status_code=307)

    raise HTTPException(status_code=404, detail="No authorized PDF location configured for this paper.")


@router.get("/papers/{paper_id}/download")
def download_pyq_paper_pdf(paper_id: str, db: Session = Depends(get_db)):
    """
    Download verified question paper PDF with Content-Disposition attachment headers,
    recording download statistics when permitted.
    """
    repo = PYQPaperRepository(db)
    paper = repo.get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Question paper not found")

    if paper.availability_status == "restricted":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Direct download is restricted by the issuing authority.",
        )

    repo.increment_download(paper_id)

    # Sanitize download filename
    clean_title = re.sub(r"[^a-zA-Z0-9_\-]", "_", paper.title)[:60]
    filename = f"{clean_title}_{paper.year}.pdf"

    local_file = resolve_safe_pdf_path(paper.storage_path)
    if local_file:
        if not verify_pdf_magic_bytes(local_file):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stored document failed PDF signature validation.",
            )
        return FileResponse(
            path=str(local_file),
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    if paper.pdf_url:
        return RedirectResponse(url=paper.pdf_url, status_code=307)

    if paper.source_url:
        return RedirectResponse(url=paper.source_url, status_code=307)

    raise HTTPException(status_code=404, detail="No downloadable file available for this paper.")


@router.post("/papers", response_model=PYQPaperResponse, status_code=201)
def create_pyq_paper(
    paper_in: PYQPaperCreate,
    x_admin_key: Optional[str] = Header(None),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Admin or automated ingestion endpoint to register verified question papers.
    Strictly forbids unauthorized user submissions.
    """
    secret = getattr(settings, "SECRET_KEY", "flashfacts_secure_exam_portal_key_2026")
    is_admin_key_valid = x_admin_key and x_admin_key == secret
    is_admin_user = user and not user.is_guest

    if not is_admin_key_valid and not is_admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin authorization or ingestion secret required to publish verified papers.",
        )

    repo = PYQPaperRepository(db)
    existing = repo.get(paper_in.id)
    if existing:
        raise HTTPException(status_code=400, detail="Paper with this ID already registered.")

    if paper_in.checksum_sha256:
        dup = repo.get_by_checksum(paper_in.checksum_sha256)
        if dup:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate paper document detected with matching SHA-256 checksum (ID: {dup.id}).",
            )

    paper = repo.create(paper_in)
    return PYQPaperResponse(
        id=paper.id,
        exam_name=paper.exam_name,
        exam_category=paper.exam_category,
        year=paper.year,
        exam_date=paper.exam_date,
        subject=paper.subject,
        language=paper.language,
        shift_session=paper.shift_session,
        paper_code=paper.paper_code,
        title=paper.title,
        source_url=paper.source_url,
        pdf_url=paper.pdf_url,
        authority=paper.authority,
        checksum_sha256=paper.checksum_sha256,
        verification_status=paper.verification_status,
        redistribution_status=paper.redistribution_status,
        file_size_bytes=paper.file_size_bytes,
        mime_type=paper.mime_type,
        availability_status=paper.availability_status,
        download_count=paper.download_count,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
        has_local_file=resolve_safe_pdf_path(paper.storage_path) is not None,
    )


# =========================================================================
# INDIVIDUAL PARSED PYQ QUESTIONS (Existing Feature Preserved)
# =========================================================================

@router.get("/filters", response_model=PYQFiltersResponse)
def get_pyq_filters(
    exam_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve distinct filter values (exams, years, subjects, topics) from real PYQ data."""
    repo = PYQRepository(db)
    return repo.get_filter_options(exam_name=exam_name)


@router.get("/bookmarks", response_model=List[PYQResponse])
def get_user_bookmarks(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve authentic PYQs bookmarked by the current student."""
    repo = PYQRepository(db)
    return repo.list_bookmarks(user_id=user.id, limit=limit, offset=offset)


@router.post("/{pyq_id}/bookmark", response_model=PYQBookmarkResponse)
def toggle_pyq_bookmark(
    pyq_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle bookmark state on a PYQ for the current student."""
    repo = PYQRepository(db)
    pyq = repo.get(pyq_id)
    if not pyq:
        raise HTTPException(status_code=404, detail="PYQ not found")

    is_bookmarked = repo.toggle_bookmark(user_id=user.id, pyq_id=pyq_id)
    return PYQBookmarkResponse(
        pyq_id=pyq_id,
        bookmarked=is_bookmarked,
        message="Question bookmarked" if is_bookmarked else "Bookmark removed",
    )


@router.get("/", response_model=List[PYQResponse])
def get_pyqs(
    exam_name: Optional[str] = None,
    year: Optional[int] = None,
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    language: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Retrieve real previous-year questions filtered by exam, year, subject, topic, language, and keyword search."""
    repo = PYQRepository(db)
    user_id = user.id if user else None
    return repo.list_by_exam(
        exam_name=exam_name,
        year=year,
        subject=subject,
        topic=topic,
        language=language,
        search_query=q,
        limit=limit,
        offset=offset,
        user_id=user_id,
    )


@router.get("/{pyq_id}", response_model=PYQResponse)
def get_pyq(
    pyq_id: int,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    repo = PYQRepository(db)
    pyq = repo.get(pyq_id)
    if not pyq:
        raise HTTPException(status_code=404, detail="PYQ not found")

    is_bookmarked = False
    if user:
        from app.models.pyq_bookmark import PYQBookmark
        bm = db.query(PYQBookmark).filter(
            PYQBookmark.user_id == user.id,
            PYQBookmark.pyq_id == pyq.id,
        ).first()
        is_bookmarked = bm is not None

    return PYQResponse(
        id=pyq.id,
        exam_name=pyq.exam_name,
        year=pyq.year,
        paper_name=pyq.paper_name,
        subject=pyq.subject,
        topic=pyq.topic,
        source=pyq.source,
        language=pyq.language or "en",
        is_verified=pyq.is_verified if pyq.is_verified is not None else True,
        question_text=pyq.question_text,
        options=pyq.options,
        correct_answer=pyq.correct_answer,
        explanation=pyq.explanation,
        is_bookmarked=is_bookmarked,
        created_at=pyq.created_at,
        updated_at=pyq.updated_at,
    )


@router.post("/", response_model=PYQResponse, status_code=201)
def create_pyq(pyq_in: PYQCreate, db: Session = Depends(get_db)):
    repo = PYQRepository(db)
    created = repo.create(**pyq_in.model_dump())
    return PYQResponse(
        id=created.id,
        exam_name=created.exam_name,
        year=created.year,
        paper_name=created.paper_name,
        subject=created.subject,
        topic=created.topic,
        source=created.source,
        language=created.language or "en",
        is_verified=created.is_verified if created.is_verified is not None else True,
        question_text=created.question_text,
        options=created.options,
        correct_answer=created.correct_answer,
        explanation=created.explanation,
        is_bookmarked=False,
        created_at=created.created_at,
        updated_at=created.updated_at,
    )
