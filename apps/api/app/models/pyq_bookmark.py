import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class PYQBookmark(Base):
    __tablename__ = "pyq_bookmarks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pyq_id = Column(Integer, ForeignKey("pyqs.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    pyq = relationship("PYQ")

    __table_args__ = (
        UniqueConstraint("user_id", "pyq_id", name="uq_user_pyq_bookmark"),
    )
