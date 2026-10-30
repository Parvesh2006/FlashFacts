from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class PYQPaperBase(BaseModel):
    id: str
    exam_name: str
    exam_category: str
    year: int
    exam_date: Optional[date] = None
    subject: str
    language: str = "en"
    shift_session: Optional[str] = None
    paper_code: Optional[str] = None
    title: str
    source_url: str
    pdf_url: Optional[str] = None
    authority: str
    checksum_sha256: Optional[str] = None
    verification_status: str = "unverified"
    redistribution_status: str = "unknown"
    file_size_bytes: Optional[int] = None
    mime_type: str = "application/pdf"
    availability_status: str = "source_link_only"
    download_count: int = 0
    last_verified_at: Optional[datetime] = None


class PYQPaperCreate(PYQPaperBase):
    storage_path: Optional[str] = None


class PYQPaperUpdate(BaseModel):
    title: Optional[str] = None
    source_url: Optional[str] = None
    pdf_url: Optional[str] = None
    storage_path: Optional[str] = None
    availability_status: Optional[str] = None
    verification_status: Optional[str] = None
    download_count: Optional[int] = None
    last_verified_at: Optional[datetime] = None


class PYQPaperResponse(PYQPaperBase):
    created_at: datetime
    updated_at: datetime
    has_local_file: bool = False
    source_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PYQPaperListResponse(BaseModel):
    items: List[PYQPaperResponse]
    total: int
    limit: int
    offset: int


class PYQPaperFilterOptions(BaseModel):
    categories: List[str]
    exams: List[str]
    years: List[int]
    subjects: List[str]
    languages: List[str]
    availability_statuses: List[str] = ["available", "source_link_only"]
