from pydantic import BaseModel, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import re


class PYQBase(BaseModel):
    exam_name: str
    year: int
    paper_name: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    source: Optional[str] = None
    language: str = "en"
    is_verified: bool = True
    question_type: str = "syllabus_practice"
    quality_status: str = "valid"
    rejection_reason: Optional[str] = None
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None

    @model_validator(mode="after")
    def validate_mcq_integrity(self):
        # Allow invalid records to be deserialized for audit/inspection
        if getattr(self, "quality_status", "valid") == "invalid":
            return self

        # 1. Exactly 4 options required for playable/valid MCQs
        if not self.options or len(self.options) != 4:
            raise ValueError(
                f"MCQ must have exactly 4 options, found {len(self.options) if self.options else 0}"
            )

        # 2. Check each option: non-empty, no single-character non-digit fragments
        cleaned = []
        for idx, opt in enumerate(self.options):
            if not isinstance(opt, str) or not opt.strip():
                raise ValueError(f"Option {idx + 1} cannot be empty or whitespace-only")
            clean_text = re.sub(r"^[A-D][.)]\s*", "", opt.strip(), flags=re.IGNORECASE).strip()
            text_to_check = clean_text or opt.strip()
            if len(text_to_check) <= 1 and not text_to_check.isdigit():
                raise ValueError(
                    f"Option {idx + 1} is an invalid single-character fragment: '{opt}'"
                )
            cleaned.append(clean_text or opt.strip())

        # 3. Check for distinct options
        if len(set(o.lower() for o in cleaned)) != 4:
            raise ValueError(f"MCQ options must all be distinct, found duplicates")

        # 4. Validate correct_answer matches one of the options
        ans = (self.correct_answer or "").strip()
        if not ans:
            raise ValueError("correct_answer cannot be empty")

        if ans.upper() in {"A", "B", "C", "D"}:
            return self

        clean_ans = re.sub(r"^[A-D][.)]\s*", "", ans, flags=re.IGNORECASE).strip().lower()
        if clean_ans in [o.lower() for o in cleaned] or ans.lower() in [o.lower() for o in self.options]:
            return self

        raise ValueError(
            f"correct_answer '{ans}' does not match any of the 4 options: {self.options}"
        )


class PYQCreate(PYQBase):
    pass


class PYQResponse(PYQBase):
    id: int
    is_bookmarked: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PYQFiltersResponse(BaseModel):
    exams: List[str]
    years: List[int]
    subjects: List[str]
    topics: List[str]
    total_count: int


class PYQBookmarkResponse(BaseModel):
    pyq_id: int
    bookmarked: bool
    message: str
