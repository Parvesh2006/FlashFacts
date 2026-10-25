import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    is_guest = Column(Boolean, default=True, nullable=False)
    target_exam = Column(String(100), default="TNPSC Group 4", nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @classmethod
    def create_guest(cls, target_exam: str = "TNPSC Group 4") -> "User":
        uid = str(uuid.uuid4())
        short_id = uid[:8]
        return cls(
            id=uid,
            username=f"aspirant_{short_id}",
            is_guest=True,
            target_exam=target_exam,
        )
