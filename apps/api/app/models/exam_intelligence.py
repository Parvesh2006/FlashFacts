from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

EXAM_TYPES = ["TNPSC", "UPSC", "SSC", "BANKING", "RAILWAY", "GENERAL_GOVT"]
RELEVANCE_LEVELS = ["VERY_HIGH", "HIGH", "MEDIUM", "LOW", "NOT_RELEVANT"]
IMPORTANCE_LEVELS = ["MUST_KNOW", "IMPORTANT", "USEFUL", "BACKGROUND"]
GEOGRAPHIC_LEVELS = ["INDIA", "TAMIL_NADU", "INDIAN_STATES", "UNION_TERRITORIES", "INTERNATIONAL"]


class EventExamMetadata(Base):
    __tablename__ = "event_exam_metadata"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, unique=True, index=True)

    exam_importance = Column(String(50), nullable=False, default="USEFUL", index=True)
    geographic_level = Column(String(50), nullable=False, default="INDIA", index=True)
    primary_state = Column(String(100), nullable=True, index=True)
    why_it_matters = Column(Text, nullable=True)

    exam_facts_json = Column(Text, nullable=True, default="[]")
    question_angles_json = Column(Text, nullable=True, default="[]")
    relevance_factors_json = Column(Text, nullable=True, default="{}")

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    event = relationship("Event", back_populates="exam_metadata")

    @property
    def exam_facts(self):
        if not self.exam_facts_json:
            return []
        try:
            return json.loads(self.exam_facts_json)
        except Exception:
            return []

    @exam_facts.setter
    def exam_facts(self, val):
        self.exam_facts_json = json.dumps(val or [])

    @property
    def question_angles(self):
        if not self.question_angles_json:
            return []
        try:
            return json.loads(self.question_angles_json)
        except Exception:
            return []

    @question_angles.setter
    def question_angles(self, val):
        self.question_angles_json = json.dumps(val or [])

    @property
    def relevance_factors(self):
        if not self.relevance_factors_json:
            return {}
        try:
            return json.loads(self.relevance_factors_json)
        except Exception:
            return {}

    @relevance_factors.setter
    def relevance_factors(self, val):
        self.relevance_factors_json = json.dumps(val or {})


class EventExamRelevance(Base):
    __tablename__ = "event_exam_relevance"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    exam_type = Column(String(50), nullable=False, index=True)
    relevance_level = Column(String(50), nullable=False, default="MEDIUM", index=True)
    relevance_score = Column(Integer, nullable=False, default=50, index=True)
    explanation = Column(Text, nullable=True)

    @property
    def why_relevant(self):
        return self.explanation

    @why_relevant.setter
    def why_relevant(self, value):
        self.explanation = value

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    event = relationship("Event", back_populates="exam_relevances")


Index("ix_event_exam_relevance_event_exam", EventExamRelevance.event_id, EventExamRelevance.exam_type, unique=True)

