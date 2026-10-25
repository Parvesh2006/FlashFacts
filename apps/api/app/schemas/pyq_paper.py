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
    verification_status: str = "verified_official"
    redistribution_status: str = "official_open_access"
    file_size_bytes: Optional[int] = None
    mime_type: str = "application/pdf"
    availability_status: str = "available"
    download_count: int = 0


class PYQPaperCreate(PYQPaperBase):
    storage_path: Optional[str] = None


class PYQPaperUpdate(BaseModel):
    title: Optional[str] = None
    pdf_url: Optional[str] = None
    storage_path: Optional[str] = None
    availability_status: Optional[str] = None
    verification_status: Optional[str] = None
    download_count: Optional[int] = None


class PYQPaperResponse(PYQPaperBase):
    created_at: datetime
    updated_at: datetime
    has_local_file: bool = False

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
