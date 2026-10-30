from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user_optional, get_current_user
from app.models.user import User
from app.schemas.mock_test import (
    MockTestCreate,
    MockTestResponse,
    MockTestSummary,
    MockTestAttemptCreate,
    MockTestAttemptResponse,
    MockTestAttemptSummary,
    MockTestQuestionSchema,
    MockTestAnswerReview,
)
from app.services.mock_test_service import MockTestService

router = APIRouter()


@router.get("/eligible-counts")
def get_eligible_counts(db: Session = Depends(get_db)):
    """Return available verified question counts and supported test lengths by exam."""
    service = MockTestService(db)
    return service.get_eligible_counts()


@router.get("/", response_model=List[MockTestSummary])
def list_mock_tests(
    exam_name: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Browse ready mock tests by exam, domain, difficulty, and question count."""
    service = MockTestService(db)
    tests = service.list_tests(exam_name=exam_name, domain=domain, limit=limit, offset=offset)
    return [MockTestSummary.model_validate(t) for t in tests]


@router.get("/attempts", response_model=List[MockTestAttemptSummary])
def list_attempts(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full attempt history for the authenticated student."""
    service = MockTestService(db)
    return service.list_user_attempts(user_id=user.id, limit=limit, offset=offset)


@router.post("/", response_model=MockTestResponse, status_code=201)
def create_mock_test(
    test_in: MockTestCreate,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Create a new dynamically generated mock test based on authentic PYQs and exam-relevant current affairs."""
    service = MockTestService(db)
    try:
        test = service.create_mock_test(
            exam_name=test_in.exam_name,
            total_questions=test_in.total_questions,
            time_limit_minutes=test_in.time_limit_minutes,
            negative_marking=test_in.negative_marking,
            include_pyqs=test_in.include_pyqs,
            include_events=test_in.include_events,
            domain=test_in.domain,
            user_id=user.id if user else None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    if test.status != "ready":
        raise HTTPException(
            status_code=422,
            detail=(
                "Mock test generation failed: no suitable questions "
                "were available. Add verified PYQs or eligible current-affairs events."
            ),
        )

    questions_data = [
        MockTestQuestionSchema(
            id=q.id,
            question_order=q.question_order,
            is_pyq=q.is_pyq,
            pyq_id=q.pyq_id,
            event_id=q.event_id,
            question_text=q.question_text,
            options=q.options,
        )
        for q in test.questions
    ]

    return MockTestResponse(
        id=test.id,
        exam_name=test.exam_name,
        title=getattr(test, "title", None),
        domain=test.domain,
        language=test.language,
        difficulty=test.difficulty,
        total_questions=test.total_questions,
        time_limit_minutes=test.time_limit_minutes,
        negative_marking=test.negative_marking,
        status=test.status,
        created_at=test.created_at,
        updated_at=test.updated_at,
        questions=questions_data,
    )


@router.get("/{test_id}", response_model=MockTestResponse)
def get_mock_test(test_id: str, db: Session = Depends(get_db)):
    """Get mock test interface with questions (hiding answers and explanations for exam integrity)."""
    service = MockTestService(db)
    test = service.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Mock Test not found")

    questions_data = [
        MockTestQuestionSchema(
            id=q.id,
            question_order=q.question_order,
            is_pyq=q.is_pyq,
            pyq_id=q.pyq_id,
            event_id=q.event_id,
            question_text=q.question_text,
            options=q.options,
        )
        for q in test.questions
    ]

    return MockTestResponse(
        id=test.id,
        exam_name=test.exam_name,
        title=getattr(test, "title", None),
        domain=test.domain,
        language=test.language,
        difficulty=test.difficulty,
        total_questions=test.total_questions,
        time_limit_minutes=test.time_limit_minutes,
        negative_marking=test.negative_marking,
        status=test.status,
        created_at=test.created_at,
        updated_at=test.updated_at,
        questions=questions_data,
    )


@router.post(
    "/{test_id}/attempts",
    response_model=MockTestAttemptResponse,
    status_code=201,
)
def submit_mock_test_attempt(
    test_id: str,
    attempt_in: MockTestAttemptCreate,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Submit test answers, calculate server-side score with negative marking,
    and automatically log mistakes into the student's Mistake Book if authenticated.
    """
    service = MockTestService(db)

    try:
        user_id = user.id if user else None
        attempt = service.submit_attempt(
            test_id=test_id,
            answers=attempt_in.answers,
            user_id=user_id,
            time_taken_seconds=attempt_in.time_taken_seconds,
            review_marked=attempt_in.review_marked,
        )
        test = service.get_test(test_id)

        if not test:
            raise HTTPException(status_code=404, detail="Mock Test not found")

        review = []
        for question in test.questions:
            raw_answer = attempt.answers.get(str(question.id))
            selected_letter = service._answer_letter(raw_answer, question.options) if raw_answer else None
            correct_letter = service._answer_letter(
                question.correct_answer, question.options
            )

            is_correct = (
                selected_letter is not None
                and correct_letter is not None
                and selected_letter == correct_letter
            )

            review.append(
                MockTestAnswerReview(
                    question_id=question.id,
                    question_order=question.question_order,
                    question_text=question.question_text,
                    options=question.options,
                    selected_answer=selected_letter or raw_answer,
                    correct_answer=correct_letter or question.correct_answer,
                    is_correct=is_correct,
                    explanation=question.explanation,
                )
            )

        return MockTestAttemptResponse(
            id=attempt.id,
            test_id=attempt.test_id,
            user_id=attempt.user_id,
            score=attempt.score,
            accuracy=attempt.accuracy,
            total_answered=attempt.total_answered,
            incorrect_count=attempt.incorrect_count,
            unanswered_count=attempt.unanswered_count,
            time_taken_seconds=attempt.time_taken_seconds,
            is_submitted=attempt.is_submitted,
            submitted_at=attempt.submitted_at,
            review=review,
        )

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/{test_id}/attempts/{attempt_id}",
    response_model=MockTestAttemptResponse,
)
def get_attempt_review(
    test_id: str,
    attempt_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Retrieve full review and explanation breakdown for a submitted attempt."""
    service = MockTestService(db)
    attempt = service.get_attempt(attempt_id)
    if not attempt or attempt.test_id != test_id:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.user_id:
        if not user or user.id != attempt.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this attempt",
            )

    test = service.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Mock Test not found")

    review = []
    for question in test.questions:
        raw_answer = attempt.answers.get(str(question.id))
        selected_letter = service._answer_letter(raw_answer, question.options) if raw_answer else None
        correct_letter = service._answer_letter(
            question.correct_answer, question.options
        )

        is_correct = (
            selected_letter is not None
            and correct_letter is not None
            and selected_letter == correct_letter
        )

        review.append(
            MockTestAnswerReview(
                question_id=question.id,
                question_order=question.question_order,
                question_text=question.question_text,
                options=question.options,
                selected_answer=selected_letter or raw_answer,
                correct_answer=correct_letter or question.correct_answer,
                is_correct=is_correct,
                explanation=question.explanation,
            )
        )

    return MockTestAttemptResponse(
        id=attempt.id,
        test_id=attempt.test_id,
        user_id=attempt.user_id,
        score=attempt.score,
        accuracy=attempt.accuracy,
        total_answered=attempt.total_answered,
        incorrect_count=attempt.incorrect_count,
        unanswered_count=attempt.unanswered_count,
        time_taken_seconds=attempt.time_taken_seconds,
        is_submitted=attempt.is_submitted,
        submitted_at=attempt.submitted_at,
        review=review,
    )
