import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Date, BigInteger, Index
from app.core.database import Base


class PYQPaper(Base):
    __tablename__ = "pyq_papers"

    id = Column(String(64), primary_key=True, index=True)
    exam_name = Column(String(100), nullable=False, index=True)
    exam_category = Column(String(50), nullable=False, index=True)  # TNPSC, UPSC, SSC, RRB
    year = Column(Integer, nullable=False, index=True)
    exam_date = Column(Date, nullable=True)
    subject = Column(String(150), nullable=False, index=True)
    language = Column(String(20), nullable=False, default="en", index=True)
    shift_session = Column(String(50), nullable=True)
    paper_code = Column(String(50), nullable=True, index=True)
    title = Column(String(255), nullable=False)

    source_url = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=True)  # local storage path or relative artifact path
    pdf_url = Column(Text, nullable=True)       # public/authorized direct URL
    authority = Column(String(200), nullable=False)

    checksum_sha256 = Column(String(64), nullable=True, index=True)
    verification_status = Column(String(30), nullable=False, default="verified_official")
    redistribution_status = Column(String(50), nullable=False, default="official_open_access")
    file_size_bytes = Column(BigInteger, nullable=True)
    mime_type = Column(String(50), nullable=False, default="application/pdf")
    availability_status = Column(String(30), nullable=False, default="available")  # available, source_link_only, restricted
    download_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_pyq_papers_exam_year", "exam_name", "year"),
        Index("ix_pyq_papers_category_year", "exam_category", "year"),
    )
