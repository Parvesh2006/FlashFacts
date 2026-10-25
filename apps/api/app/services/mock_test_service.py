import re
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.mock_test import MockTest, MockTestQuestion, MockTestAttempt
from app.models.pyq import PYQ
from app.models.event import Event
from app.models.revision_item import RevisionItem
from app.services.exam_intelligence import ExamIntelligenceService


EXAM_NEGATIVE_MARKING_MAP = {
    "tnpsc": 0.0,
    "tnpsc group 4": 0.0,
    "tnpsc group 2": 0.0,
    "upsc": 0.33,
    "upsc cse": 0.33,
    "ssc": 0.50,
    "ssc cgl": 0.50,
    "ssc chsl": 0.50,
    "rrb": 0.33,
    "rrb ntpc": 0.33,
    "banking": 0.25,
}


class MockTestService:
    def __init__(self, db: Session):
        self.db = db
        self.exam_intel = ExamIntelligenceService(db)

    @staticmethod
    def _answer_letter(answer: Optional[str], options: List[str]) -> Optional[str]:
        if not answer:
            return None

        value = str(answer).strip()
        if value.upper() in {"A", "B", "C", "D"}:
            return value.upper()

        match = re.match(r"^([A-D])(?:[.)]\s*|\s+)", value, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        for index, option in enumerate(options):
            letter = chr(65 + index)
            option_text = re.sub(
                r"^[A-D][.)]\s*",
                "",
                str(option).strip(),
                flags=re.IGNORECASE,
            )
            if value.casefold() in {
                str(option).strip().casefold(),
                option_text.casefold(),
            }:
                return letter

        return None

    def get_default_negative_marking(self, exam_name: str) -> float:
        name_lower = exam_name.lower().strip()
        for key, mark in EXAM_NEGATIVE_MARKING_MAP.items():
            if key in name_lower:
                return mark
        return 0.0

    def list_tests(
        self,
        exam_name: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MockTest]:
        stmt = select(MockTest).where(MockTest.status == "ready")
        if exam_name:
            stmt = stmt.where(MockTest.exam_name.ilike(f"%{exam_name}%"))
        if domain:
            stmt = stmt.where(MockTest.domain.ilike(f"%{domain}%"))
        stmt = stmt.order_by(desc(MockTest.created_at)).offset(offset).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def create_mock_test(
        self,
        exam_name: str,
        total_questions: int = 10,
        time_limit_minutes: int = 30,
        negative_marking: Optional[float] = None,
        include_pyqs: bool = True,
        include_events: bool = True,
        domain: Optional[str] = None,
    ) -> MockTest:
        if negative_marking is None:
            negative_marking = self.get_default_negative_marking(exam_name)

        # Create test record
        test = MockTest(
            exam_name=exam_name,
            total_questions=total_questions,
            time_limit_minutes=time_limit_minutes,
            negative_marking=negative_marking,
            domain=domain,
            status="generating",
        )
        self.db.add(test)
        self.db.commit()
        self.db.refresh(test)

        questions_needed = total_questions
        current_order = 1

        # 1. Fetch authentic PYQs
        if include_pyqs:
            pyq_query = select(PYQ).where(PYQ.exam_name.ilike(f"%{exam_name}%"))
            if domain:
                pyq_query = pyq_query.where(PYQ.subject == domain)
            pyqs = list(self.db.execute(pyq_query).scalars().all())
            random.shuffle(pyqs)

            pyq_count = min(
                questions_needed // 2 if include_events else questions_needed,
                len(pyqs),
            )
            selected_pyqs = pyqs[:pyq_count]

            for pyq in selected_pyqs:
                mq = MockTestQuestion(
                    test_id=test.id,
                    question_order=current_order,
                    is_pyq=True,
                    pyq_id=pyq.id,
                    question_text=pyq.question_text,
                    options=pyq.options,
                    correct_answer=pyq.correct_answer,
                    explanation=pyq.explanation,
                )
                self.db.add(mq)
                current_order += 1
                questions_needed -= 1

        # 2. Fetch Exam-Relevant Events and Generate MCQs
        if include_events and questions_needed > 0:
            exam_id = None
            for def_data in self.exam_intel.get_all_exams():
                if def_data["name"].lower() in exam_name.lower() or exam_name.lower() in def_data["name"].lower():
                    exam_id = def_data["id"]
                    break

            # Filter out non-exam domains
            non_exam_domains = ("Entertainment", "Crime", "Lifestyle", "Gossip", "Cinema")
            event_query = (
                select(Event)
                .where(Event.summary.is_not(None))
                .where(~Event.domain.in_(non_exam_domains))
            )
            if domain:
                event_query = event_query.where(Event.domain == domain)

            events = list(
                self.db.execute(
                    event_query.order_by(Event.importance_score.desc()).limit(300)
                ).scalars().all()
            )

            def relevance_score(event):
                title = (event.title or "").lower()
                summary = (event.summary or "").lower()
                context = (getattr(event, "why_it_matters", None) or "").lower()
                text = f"{title} {summary} {context}"
                score = float(event.importance_score or 0)

                tamil_nadu_terms = (
                    "tamil nadu", "chennai", "madurai", "coimbatore",
                    "cauvery", "kaveri", "tnpsc", "tamil nadu government",
                    "tamil nadu chief minister", "tn government", "stalin"
                )
                india_terms = (
                    "india", "indian government", "government of india",
                    "prime minister", "ministry", "parliament", "supreme court",
                    "reserve bank of india", "rbi", "isro", "election commission",
                    "national scheme", "union budget"
                )
                exam_terms = (
                    "scheme", "policy", "budget", "appointment", "award",
                    "report", "census", "mission", "conservation", "court",
                    "education", "public health", "infrastructure", "amendment"
                )

                if any(term in text for term in tamil_nadu_terms):
                    score += 45 if "TNPSC" in exam_name.upper() else 20

                if any(term in text for term in india_terms):
                    score += 20

                score += sum(4 for term in exam_terms if term in text)

                if len(summary.strip()) < 100:
                    score -= 15

                return score

            events.sort(key=relevance_score, reverse=True)

            for event in events:
                if questions_needed <= 0:
                    break

                mcqs = self.exam_intel.generate_mcqs(event.id, exam_id=exam_id, count=1)
                if mcqs and mcqs.get("mcqs"):
                    generated_q = mcqs["mcqs"][0]
                    mq = MockTestQuestion(
                        test_id=test.id,
                        question_order=current_order,
                        is_pyq=False,
                        event_id=event.id,
                        question_text=generated_q["question"],
                        options=generated_q["options"],
                        correct_answer=generated_q["correct_answer"],
                        explanation=generated_q["explanation"],
                    )
                    self.db.add(mq)
                    current_order += 1
                    questions_needed -= 1

        question_count = current_order - 1
        test.status = "ready" if question_count > 0 else "failed"
        self.db.commit()
        self.db.refresh(test)
        return test

    def get_test(self, test_id: str) -> Optional[MockTest]:
        return self.db.execute(select(MockTest).where(MockTest.id == test_id)).scalar_one_or_none()

    def submit_attempt(
        self,
        test_id: str,
        answers: Dict[str, str],
        user_id: Optional[str] = None,
        time_taken_seconds: int = 0,
        review_marked: Optional[List[int]] = None,
    ) -> MockTestAttempt:
        test = self.get_test(test_id)
        if not test:
            raise ValueError("Test not found")

        correct_count = 0
        incorrect_count = 0
        total_answered = 0
        neg_mark = float(test.negative_marking or 0.0)

        mistakes_to_record = []

        for q in test.questions:
            ans = answers.get(str(q.id))
            selected_letter = self._answer_letter(ans, q.options) if ans else None
            correct_letter = self._answer_letter(q.correct_answer, q.options)

            if ans and selected_letter is not None:
                total_answered += 1
                if selected_letter == correct_letter:
                    correct_count += 1
                else:
                    incorrect_count += 1
                    if user_id:
                        mistakes_to_record.append({
                            "question": q,
                            "selected": selected_letter,
                            "correct": correct_letter or q.correct_answer,
                            "outcome": "incorrect",
                        })
            else:
                if user_id:
                    mistakes_to_record.append({
                        "question": q,
                        "selected": None,
                        "correct": correct_letter or q.correct_answer,
                        "outcome": "skipped",
                    })

        total_q = len(test.questions)
        unanswered_count = total_q - total_answered

        # Server-side score with negative marking
        raw_score = (correct_count * 1.0) - (incorrect_count * neg_mark)
        final_score = round(max(0.0, raw_score), 2)
        accuracy = int((correct_count / total_q) * 100) if total_q > 0 else 0

        attempt = MockTestAttempt(
            test_id=test_id,
            user_id=user_id,
            answers=answers,
            review_marked=review_marked or [],
            score=final_score,
            accuracy=accuracy,
            total_answered=total_answered,
            incorrect_count=incorrect_count,
            unanswered_count=unanswered_count,
            time_taken_seconds=time_taken_seconds,
            is_submitted=True,
        )
        self.db.add(attempt)

        # Idempotently auto-record mistakes into Mistake Book for this user
        if user_id and mistakes_to_record:
            for m in mistakes_to_record:
                q_obj = m["question"]
                existing_rev = self.db.query(RevisionItem).filter(
                    RevisionItem.user_id == user_id,
                    RevisionItem.question_text == q_obj.question_text,
                ).first()

                if existing_rev:
                    existing_rev.mistake_count += 1
                    existing_rev.selected_answer = m["selected"]
                    existing_rev.outcome = m["outcome"]
                    existing_rev.is_revised = False
                    existing_rev.next_review_at = datetime.now(timezone.utc) + timedelta(days=1)
                    existing_rev.updated_at = datetime.now(timezone.utc)
                else:
                    new_rev = RevisionItem(
                        user_id=user_id,
                        question_source="mock_test",
                        question_id=q_obj.id,
                        mock_test_id=test.id,
                        exam_name=test.exam_name,
                        subject=test.domain or "General Studies",
                        question_text=q_obj.question_text,
                        options=q_obj.options,
                        selected_answer=m["selected"],
                        correct_answer=m["correct"],
                        explanation=q_obj.explanation,
                        outcome=m["outcome"],
                        mistake_count=1,
                        is_revised=False,
                        next_review_at=datetime.now(timezone.utc) + timedelta(days=1),
                    )
                    self.db.add(new_rev)

        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def list_user_attempts(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(MockTestAttempt, MockTest)
            .join(MockTest, MockTest.id == MockTestAttempt.test_id)
            .where(MockTestAttempt.user_id == user_id)
            .order_by(desc(MockTestAttempt.submitted_at))
            .offset(offset)
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        results = []
        for attempt, test in rows:
            results.append({
                "id": attempt.id,
                "test_id": attempt.test_id,
                "exam_name": test.exam_name,
                "score": attempt.score,
                "accuracy": attempt.accuracy,
                "total_answered": attempt.total_answered,
                "total_questions": test.total_questions,
                "time_taken_seconds": attempt.time_taken_seconds,
                "submitted_at": attempt.submitted_at,
            })
        return results

    def get_attempt(self, attempt_id: str) -> Optional[MockTestAttempt]:
        return self.db.execute(
            select(MockTestAttempt).where(MockTestAttempt.id == attempt_id)
        ).scalar_one_or_none()
