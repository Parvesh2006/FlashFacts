import re
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, or_
from collections import Counter

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

    @staticmethod
    def get_template_signature(
        exam_name: str,
        domain: Optional[str] = None,
        total_questions: int = 10,
        time_limit_minutes: int = 15,
        difficulty: str = "medium",
        negative_marking: float = 0.0,
        subject: Optional[str] = None,
    ) -> str:
        """
        Computes a stable identity for mock test templates based on exam,
        domain/subject, question count, duration, difficulty, and negative marking.
        Ensures identical test configurations collapse to a single template card.
        """
        exam_clean = " ".join((exam_name or "").lower().split())
        if "group 4" in exam_clean:
            exam_key = "tnpsc_group_4"
        elif "group 2" in exam_clean:
            exam_key = "tnpsc_group_2"
        elif "upsc" in exam_clean:
            exam_key = "upsc_cse"
        elif "ssc" in exam_clean:
            exam_key = "ssc_cgl"
        elif "rrb" in exam_clean:
            exam_key = "rrb_ntpc"
        else:
            exam_key = re.sub(r"[^a-z0-9]+", "_", exam_clean).strip("_")

        topic_str = (domain or subject or "").strip().lower()
        if not topic_str or topic_str in ("none", "null", "all", "general", "general knowledge", "general studies"):
            topic_key = "general_studies"
        else:
            topic_key = re.sub(r"[^a-z0-9]+", "_", topic_str).strip("_")

        diff_key = (difficulty or "medium").strip().lower()
        neg_key = f"{float(negative_marking or 0.0):.2f}"
        return f"{exam_key}::{topic_key}::{int(total_questions)}q::{int(time_limit_minutes)}m::{diff_key}::{neg_key}"

    def resolve_test_title(
        self,
        test: MockTest,
        questions: Optional[List[MockTestQuestion]] = None,
    ) -> tuple[str, Optional[str]]:
        """
        Derives a meaningful, descriptive title and primary subject grounded strictly in real test data.
        Returns: (title, primary_subject)
        """
        if getattr(test, "title", None) and test.title and not test.title.strip().endswith("Practice Test"):
            return test.title.strip(), getattr(test, "subject", None)

        if questions is None:
            questions = (
                self.db.query(MockTestQuestion)
                .filter(MockTestQuestion.test_id == test.id)
                .all()
            )

        subjects = []
        topics = []
        pyq_ids = [q.pyq_id for q in questions if q.is_pyq and q.pyq_id]
        if pyq_ids:
            pyqs = self.db.query(PYQ).filter(PYQ.id.in_(pyq_ids)).all()
            for p in pyqs:
                if p.subject and p.subject.strip():
                    subjects.append(p.subject.strip())
                if p.topic and p.topic.strip() and p.topic.strip().lower() not in ("general", "none"):
                    topics.append(p.topic.strip())

        subj_counts = Counter(subjects)
        top_subj = subj_counts.most_common(1)[0][0] if subj_counts else None

        exam = (test.exam_name or "Practice").strip()
        if "group 4" in exam.lower():
            display_exam = "TNPSC Group 4"
        elif "group 2" in exam.lower():
            display_exam = "TNPSC Group 2"
        elif "upsc" in exam.lower():
            display_exam = "UPSC CSE"
        elif "ssc" in exam.lower():
            display_exam = "SSC CGL"
        elif "rrb" in exam.lower():
            display_exam = "RRB NTPC"
        else:
            display_exam = exam

        # 1. If explicit domain is provided (e.g. Tamil Nadu General Knowledge, Indian Polity)
        dom = (test.domain or "").strip()
        if dom and dom.lower() not in ("none", "general", "null", "all"):
            clean_dom = dom
            if "Unit VIII" in clean_dom:
                clean_dom = "Tamil Society, Culture & Heritage"
            elif "Unit IX" in clean_dom:
                clean_dom = "Development Administration in Tamil Nadu"
            return f"{display_exam}: {clean_dom} Sectional Drill", clean_dom

        # 2. If questions cluster in a primary subject (>= 40% of questions)
        if top_subj:
            count = subj_counts[top_subj]
            if count >= max(2, int(len(questions) * 0.4)):
                clean_subj = top_subj
                if "Unit VIII" in clean_subj:
                    clean_subj = "Tamil Society, Culture & Heritage"
                elif "Unit IX" in clean_subj:
                    clean_subj = "Development Administration in Tamil Nadu"
                return f"{display_exam}: {clean_subj} Drill", clean_subj

        # 3. Comprehensive / Multi-subject based on exam & question count
        if "upsc" in display_exam.lower():
            if test.total_questions >= 25:
                return f"{display_exam}: General Studies Paper I Comprehensive Mock", "General Studies"
            return f"{display_exam}: General Studies Paper I Mini Mock", "General Studies"
        elif "ssc" in display_exam.lower():
            return f"{display_exam}: General Awareness Sectional Practice", "General Awareness"
        elif "rrb" in display_exam.lower():
            return f"{display_exam}: General Awareness CBT-1 Mock Drill", "General Awareness"
        elif test.total_questions >= 25:
            return f"{display_exam}: General Studies Comprehensive Mock", "General Studies"
        elif test.total_questions >= 10:
            return f"{display_exam}: General Studies Practice Drill", "General Studies"
        else:
            top_topic = Counter(topics).most_common(1)[0][0] if topics else None
            if top_topic:
                return f"{display_exam}: {top_topic} Quick Drill", top_subj or "General Studies"
            return f"{display_exam}: Speed Practice Drill", "General Studies"

    def list_tests(
        self,
        exam_name: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MockTest]:
        # 1. Retrieve all ready tests
        stmt = select(MockTest).where(MockTest.status == "ready")
        if exam_name:
            stmt = stmt.where(MockTest.exam_name.ilike(f"%{exam_name}%"))
        if domain:
            stmt = stmt.where(MockTest.domain.ilike(f"%{domain}%"))
        stmt = stmt.order_by(desc(MockTest.created_at))
        all_tests = self.db.execute(stmt).scalars().all()

        # 2. Filter out broken tests with 0 linked questions
        valid_tests = []
        for t in all_tests:
            q_cnt = self.db.query(MockTestQuestion).filter(MockTestQuestion.test_id == t.id).count()
            if q_cnt > 0:
                valid_tests.append((t, q_cnt))

        # 3. Deduplicate by stable template identity
        deduped: Dict[str, MockTest] = {}
        for test, q_cnt in valid_tests:
            title, subject = self.resolve_test_title(test)
            test.title = title
            test.subject = subject

            sig = self.get_template_signature(
                exam_name=test.exam_name,
                domain=test.domain,
                total_questions=test.total_questions,
                time_limit_minutes=test.time_limit_minutes,
                difficulty=test.difficulty,
                negative_marking=test.negative_marking,
                subject=subject,
            )
            test.template_key = sig

            if sig not in deduped:
                deduped[sig] = test
            else:
                existing = deduped[sig]
                existing_q_cnt = self.db.query(MockTestQuestion).filter(MockTestQuestion.test_id == existing.id).count()
                existing_attempts = self.db.query(MockTestAttempt).filter(MockTestAttempt.test_id == existing.id).count()
                current_attempts = self.db.query(MockTestAttempt).filter(MockTestAttempt.test_id == test.id).count()

                if (q_cnt >= test.total_questions and existing_q_cnt < existing.total_questions) or (current_attempts > 0 and existing_attempts == 0):
                    deduped[sig] = test

        # 4. Sort templates by question count desc and created_at desc
        results = list(deduped.values())
        results.sort(
            key=lambda x: (
                1 if x.total_questions >= 10 else 0,
                x.created_at or datetime.min.replace(tzinfo=timezone.utc),
            ),
            reverse=True,
        )

        return results[offset : offset + limit]

    def get_eligible_counts(self) -> Dict[str, Any]:
        """Return available unique verified questions and supported practice lengths by exam."""
        exams = ["TNPSC Group 4", "TNPSC Group 2", "UPSC CSE", "SSC CGL", "RRB NTPC"]
        result = {}
        for exam in exams:
            if "group 4" in exam.lower():
                cnt = self.db.query(PYQ).filter(
                    PYQ.exam_name.ilike("%TNPSC Group 4%"),
                    PYQ.quality_status == "valid",
                    PYQ.is_verified == True,
                ).count()
            elif "group 2" in exam.lower():
                cnt = self.db.query(PYQ).filter(
                    PYQ.exam_name.ilike("%TNPSC Group 2%"),
                    PYQ.quality_status == "valid",
                    PYQ.is_verified == True,
                ).count()
            elif "upsc" in exam.lower():
                cnt = self.db.query(PYQ).filter(
                    PYQ.exam_name.ilike("%UPSC%"),
                    PYQ.quality_status == "valid",
                    PYQ.is_verified == True,
                ).count()
            elif "ssc" in exam.lower():
                cnt = self.db.query(PYQ).filter(
                    PYQ.exam_name.ilike("%SSC%"),
                    PYQ.quality_status == "valid",
                    PYQ.is_verified == True,
                ).count()
            elif "rrb" in exam.lower():
                cnt = self.db.query(PYQ).filter(
                    PYQ.exam_name.ilike("%RRB%"),
                    PYQ.quality_status == "valid",
                    PYQ.is_verified == True,
                ).count()
            else:
                cnt = self.db.query(PYQ).filter(
                    PYQ.exam_name.ilike(f"%{exam}%"),
                    PYQ.quality_status == "valid",
                    PYQ.is_verified == True,
                ).count()

            lengths = [10]
            if cnt >= 25:
                lengths.append(25)
            if cnt >= 50:
                lengths.append(50)
            if cnt >= 100:
                lengths.append(100)

            full_length = 100 if ("upsc" in exam.lower() or "group 4" in exam.lower()) else (25 if "ssc" in exam.lower() else (40 if "rrb" in exam.lower() else 50))

            result[exam] = {
                "available_questions": cnt,
                "supported_lengths": lengths,
                "full_length": full_length,
            }
        return result

    def create_mock_test(
        self,
        exam_name: str,
        total_questions: int = 10,
        time_limit_minutes: int = 30,
        negative_marking: Optional[float] = None,
        include_pyqs: bool = True,
        include_events: bool = True,
        domain: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> MockTest:
        if negative_marking is None:
            negative_marking = self.get_default_negative_marking(exam_name)

        # 1. Query all eligible PYQs for this exam and optional domain
        exam_lower = exam_name.lower().strip()
        if "tnpsc group 4" in exam_lower:
            pyq_filter = PYQ.exam_name.ilike("%TNPSC Group 4%")
        elif "tnpsc group 2" in exam_lower or "tnpsc group ii" in exam_lower:
            pyq_filter = PYQ.exam_name.ilike("%TNPSC Group 2%")
        elif "tnpsc" in exam_lower:
            pyq_filter = PYQ.exam_name.ilike("%TNPSC%")
        elif "upsc" in exam_lower:
            pyq_filter = PYQ.exam_name.ilike("%UPSC%")
        elif "ssc" in exam_lower:
            pyq_filter = PYQ.exam_name.ilike("%SSC%")
        elif "rrb" in exam_lower:
            pyq_filter = PYQ.exam_name.ilike("%RRB%")
        else:
            pyq_filter = PYQ.exam_name.ilike(f"%{exam_name}%")

        pyq_query = select(PYQ).where(
            pyq_filter,
            PYQ.quality_status == "valid",
            PYQ.is_verified == True,
        )
        if domain:
            pyq_query = pyq_query.where(
                or_(PYQ.subject.ilike(f"%{domain}%"), PYQ.topic.ilike(f"%{domain}%"))
            )

        eligible_pyqs = list(self.db.execute(pyq_query).scalars().all())
        available_count = len(eligible_pyqs)

        if available_count == 0:
            raise ValueError(
                f"No questions are currently available for {exam_name}. Please choose another examination or refresh the question bank."
            )

        # If requested questions exceed available unique questions, explain shortage honestly
        if total_questions > available_count:
            raise ValueError(
                f"Requested {total_questions} questions for {exam_name}, but the question bank contains {available_count} verified questions. "
                f"Please select a practice length of {available_count} or fewer questions."
            )

        # 2. Non-repeating question selection: prioritize unattempted questions if user is logged in
        selected_pyqs = []
        if user_id:
            attempted_pyq_ids = set(
                self.db.execute(
                    select(MockTestQuestion.pyq_id)
                    .join(MockTestAttempt, MockTestAttempt.test_id == MockTestQuestion.test_id)
                    .where(MockTestAttempt.user_id == user_id)
                    .where(MockTestQuestion.pyq_id.isnot(None))
                ).scalars().all()
            )

            unattempted = [q for q in eligible_pyqs if q.id not in attempted_pyq_ids]
            attempted = [q for q in eligible_pyqs if q.id in attempted_pyq_ids]

            if len(unattempted) >= total_questions:
                selected_pyqs = random.sample(unattempted, total_questions)
            else:
                selected_pyqs = list(unattempted)
                needed = total_questions - len(selected_pyqs)
                random.shuffle(attempted)
                selected_pyqs.extend(attempted[:needed])
        else:
            # Guest/unauthenticated: randomized sample across full eligible set
            selected_pyqs = random.sample(eligible_pyqs, total_questions)

        # 3. Create test record
        test = MockTest(
            exam_name=exam_name,
            total_questions=len(selected_pyqs),
            time_limit_minutes=time_limit_minutes,
            negative_marking=negative_marking,
            domain=domain,
            status="generating",
        )
        self.db.add(test)
        self.db.commit()
        self.db.refresh(test)

        # 4. Insert questions with option shuffling & answer preservation
        for current_order, pyq in enumerate(selected_pyqs, start=1):
            original_options = [
                re.sub(r"^[A-D][.)]\s*", "", str(opt).strip(), flags=re.IGNORECASE)
                for opt in pyq.options
            ]
            raw_correct = str(pyq.correct_answer or "").strip()
            cleaned_correct = re.sub(r"^[A-D][.)]\s*", "", raw_correct, flags=re.IGNORECASE).strip()

            # Identify exact text of correct answer
            correct_text = cleaned_correct
            if raw_correct.upper() in {"A", "B", "C", "D"}:
                idx = ord(raw_correct.upper()) - 65
                if idx < len(original_options):
                    correct_text = original_options[idx]
            else:
                for opt in original_options:
                    if opt.casefold() == cleaned_correct.casefold() or opt.casefold() == raw_correct.casefold():
                        correct_text = opt
                        break

            # Dynamic Option Shuffling: randomize A/B/C/D order per test instance
            shuffled_options = list(original_options)
            random.shuffle(shuffled_options)

            mq = MockTestQuestion(
                test_id=test.id,
                question_order=current_order,
                is_pyq=True,
                pyq_id=pyq.id,
                question_text=pyq.question_text,
                options=shuffled_options,
                correct_answer=correct_text,
                explanation=pyq.explanation,
            )
            self.db.add(mq)

        test.status = "ready"
        self.db.commit()
        self.db.refresh(test)
        title, subject = self.resolve_test_title(test)
        test.title = title
        test.subject = subject
        return test

    def get_test(self, test_id: str) -> Optional[MockTest]:
        test = self.db.execute(select(MockTest).where(MockTest.id == test_id)).scalar_one_or_none()
        if test:
            title, subject = self.resolve_test_title(test)
            test.title = title
            test.subject = subject
        return test

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

    def ensure_default_templates(self) -> List[MockTest]:
        """
        Idempotently seeds distinct mock test templates for supported exams:
        TNPSC Group 4, TNPSC Group 2, UPSC CSE, SSC CGL, RRB NTPC.
        Guarantees that repeated runs or restarts never create duplicate templates.
        """
        specs = [
            {
                "exam_name": "TNPSC Group 4",
                "domain": None,
                "total_questions": 10,
                "time_limit_minutes": 15,
                "difficulty": "medium",
                "negative_marking": 0.0,
            },
            {
                "exam_name": "TNPSC Group 4",
                "domain": "History of Tamil Nadu",
                "total_questions": 10,
                "time_limit_minutes": 15,
                "difficulty": "medium",
                "negative_marking": 0.0,
            },
            {
                "exam_name": "TNPSC Group 4",
                "domain": "Indian Polity",
                "total_questions": 10,
                "time_limit_minutes": 15,
                "difficulty": "medium",
                "negative_marking": 0.0,
            },
            {
                "exam_name": "TNPSC Group 2",
                "domain": None,
                "total_questions": 10,
                "time_limit_minutes": 15,
                "difficulty": "medium",
                "negative_marking": 0.0,
            },
            {
                "exam_name": "UPSC CSE",
                "domain": None,
                "total_questions": 10,
                "time_limit_minutes": 15,
                "difficulty": "medium",
                "negative_marking": 0.33,
            },
            {
                "exam_name": "SSC CGL",
                "domain": None,
                "total_questions": 10,
                "time_limit_minutes": 15,
                "difficulty": "medium",
                "negative_marking": 0.50,
            },
            {
                "exam_name": "RRB NTPC",
                "domain": None,
                "total_questions": 10,
                "time_limit_minutes": 15,
                "difficulty": "medium",
                "negative_marking": 0.33,
            },
        ]

        existing_tests = self.db.query(MockTest).filter(MockTest.status == "ready").all()
        existing_signatures = set()
        for t in existing_tests:
            q_cnt = self.db.query(MockTestQuestion).filter(MockTestQuestion.test_id == t.id).count()
            if q_cnt >= t.total_questions:
                sig = self.get_template_signature(
                    exam_name=t.exam_name,
                    domain=t.domain,
                    total_questions=t.total_questions,
                    time_limit_minutes=t.time_limit_minutes,
                    difficulty=t.difficulty,
                    negative_marking=t.negative_marking,
                )
                existing_signatures.add(sig)

        created_templates = []
        for spec in specs:
            sig = self.get_template_signature(
                exam_name=spec["exam_name"],
                domain=spec.get("domain"),
                total_questions=spec["total_questions"],
                time_limit_minutes=spec["time_limit_minutes"],
                difficulty=spec["difficulty"],
                negative_marking=spec["negative_marking"],
            )
            if sig in existing_signatures:
                continue

            try:
                test = self.create_mock_test(
                    exam_name=spec["exam_name"],
                    domain=spec.get("domain"),
                    total_questions=spec["total_questions"],
                    time_limit_minutes=spec["time_limit_minutes"],
                    negative_marking=spec["negative_marking"],
                    difficulty=spec["difficulty"],
                    include_pyqs=True,
                    include_events=True,
                )
                existing_signatures.add(sig)
                created_templates.append(test)
            except Exception:
                continue

        return created_templates
