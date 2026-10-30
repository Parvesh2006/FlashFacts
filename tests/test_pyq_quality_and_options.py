import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.pyq import PYQ
from app.models.mock_test import MockTest, MockTestQuestion, MockTestAttempt
from app.services.mock_test_service import MockTestService
from app.schemas.pyq import PYQCreate, PYQResponse
from pydantic import ValidationError


def test_four_complete_options_required_for_valid_mcq():
    """Requirement 1 & 2: Valid MCQs must have exactly 4 non-empty, meaningful options."""
    # Valid payload should pass
    valid_data = {
        "exam_name": "TNPSC Group 4",
        "year": 2024,
        "question_text": "Which scheme provides financial assistance to female higher education students in Tamil Nadu?",
        "options": [
            "Pudhumai Penn Thittam",
            "Moovalur Ramamirtham Ammaiyar Scheme",
            "Kalaignar Magalir Urimai Thittam",
            "Thalikku Thangam Thittam",
        ],
        "correct_answer": "Pudhumai Penn Thittam",
        "question_type": "verified_pyq",
        "quality_status": "valid",
    }
    schema = PYQCreate(**valid_data)
    assert len(schema.options) == 4
    assert schema.correct_answer == "Pudhumai Penn Thittam"

    # Fewer than 4 options must fail
    with pytest.raises(ValidationError):
        PYQCreate(**{**valid_data, "options": ["A", "B", "C"]})

    # More than 4 options must fail
    with pytest.raises(ValidationError):
        PYQCreate(**{**valid_data, "options": ["A", "B", "C", "D", "E"]})


def test_single_letter_and_fragment_options_rejected():
    """Requirement 2: Single letter, punctuation mark, or empty fragment options are rejected."""
    base_data = {
        "exam_name": "TNPSC Group 4",
        "year": 2024,
        "question_text": "Sample question?",
        "correct_answer": "Opt 1",
        "quality_status": "valid",
    }

    # Empty string option
    with pytest.raises(ValidationError):
        PYQCreate(**{**base_data, "options": ["", "Opt 2", "Opt 3", "Opt 4"]})

    # Single letter non-digit fragment (e.g. 'E.', 'T.')
    with pytest.raises(ValidationError):
        PYQCreate(**{**base_data, "options": ["E.", "Opt 2", "Opt 3", "Opt 4"]})

    with pytest.raises(ValidationError):
        PYQCreate(**{**base_data, "options": ["A", "Opt 2", "Opt 3", "Opt 4"]})


def test_duplicate_options_rejected():
    """Requirement 3: Duplicate options must be rejected."""
    data = {
        "exam_name": "TNPSC Group 4",
        "year": 2024,
        "question_text": "Sample question?",
        "options": ["Option 1", "Option 2", "option 1", "Option 4"],
        "correct_answer": "Option 1",
        "quality_status": "valid",
    }
    with pytest.raises(ValidationError):
        PYQCreate(**data)


def test_correct_answer_must_match_options():
    """Requirement 2: correct_answer must point to one of the 4 options."""
    data = {
        "exam_name": "TNPSC Group 4",
        "year": 2024,
        "question_text": "Sample question?",
        "options": ["Chennai", "Madurai", "Coimbatore", "Trichy"],
        "correct_answer": "Salem",  # Not in options
        "quality_status": "valid",
    }
    with pytest.raises(ValidationError):
        PYQCreate(**data)


def test_option_shuffling_preserves_correct_answer(db_session: Session):
    """Requirement 4: When options are shuffled in mock tests, correct_answer remains accurate."""
    service = MockTestService(db_session)

    # Insert a verified question with clean canonical options
    q = PYQ(
        exam_name="TNPSC Group 4",
        year=2024,
        question_text="What is the capital of Tamil Nadu?",
        options=["Chennai", "Madurai", "Salem", "Tiruchirappalli"],
        correct_answer="Chennai",
        is_verified=True,
        quality_status="valid",
        question_type="verified_pyq",
    )
    db_session.add(q)
    db_session.commit()

    # Generate mock test
    test = service.create_mock_test(
        exam_name="TNPSC Group 4",
        total_questions=1,
    )
    mq = test.questions[0]

    # Verify options are present and correct_answer matches exact text
    assert len(mq.options) == 4
    assert set(mq.options) == {"Chennai", "Madurai", "Salem", "Tiruchirappalli"}
    assert mq.correct_answer == "Chennai"

    # Verify _answer_letter resolves the correct shuffled letter
    letter = service._answer_letter(mq.correct_answer, mq.options)
    assert letter in {"A", "B", "C", "D"}
    chosen_idx = ord(letter) - 65
    assert mq.options[chosen_idx] == "Chennai"


def test_malformed_and_generic_questions_excluded_from_api(client: TestClient, db_session: Session):
    """Requirement 5 & 6: Invalid and generic headline questions are excluded from practice API."""
    # Insert one valid and one invalid generic question
    valid_q = PYQ(
        exam_name="TNPSC Group 4",
        year=2024,
        question_text="Valid history question about Pallavas?",
        options=["Mahendravarman I", "Narasimhavarman I", "Simhavishnu", "Dantivarman"],
        correct_answer="Simhavishnu",
        is_verified=True,
        quality_status="valid",
        question_type="verified_pyq",
    )
    invalid_q = PYQ(
        exam_name="TNPSC Group 4",
        year=2024,
        question_text="In recent developments regarding Science, Technology & Innovation, which of the following is accurate concerning: 'NASA Announces Bold Science Initiatives'?",
        options=["E.", "T.", "T.", "A."],
        correct_answer="E.",
        is_verified=False,
        quality_status="invalid",
        question_type="invalid",
        rejection_reason="Generic headline template with canned distractors; unverified for competitive examination syllabus.",
    )
    db_session.add(valid_q)
    db_session.add(invalid_q)
    db_session.commit()

    # Query public practice API: should only return valid question
    res = client.get("/api/v1/pyqs/?exam_name=TNPSC Group 4")
    assert res.status_code == 200
    returned_ids = [item["id"] for item in res.json()]
    assert valid_q.id in returned_ids
    assert invalid_q.id not in returned_ids


def test_question_type_categorization_and_filtering(client: TestClient, db_session: Session):
    """Requirement 7: Clear distinction between official PYQ and syllabus practice."""
    pyq = PYQ(
        exam_name="TNPSC Group 4",
        year=2022,
        question_text="Official 2022 PYQ Question?",
        options=["Option 1", "Option 2", "Option 3", "Option 4"],
        correct_answer="Option 1",
        is_verified=True,
        quality_status="valid",
        question_type="verified_pyq",
    )
    practice = PYQ(
        exam_name="TNPSC Group 4",
        year=2024,
        question_text="Curated Syllabus Practice Question?",
        options=["Choice A", "Choice B", "Choice C", "Choice D"],
        correct_answer="Choice A",
        is_verified=True,
        quality_status="valid",
        question_type="syllabus_practice",
    )
    db_session.add(pyq)
    db_session.add(practice)
    db_session.commit()

    # Filter by verified_pyq
    res_pyq = client.get("/api/v1/pyqs/?type=verified_pyq")
    assert res_pyq.status_code == 200
    data_pyq = res_pyq.json()
    assert all(item["question_type"] == "verified_pyq" for item in data_pyq)
    assert any(item["id"] == pyq.id for item in data_pyq)
    assert not any(item["id"] == practice.id for item in data_pyq)

    # Filter by syllabus_practice
    res_prac = client.get("/api/v1/pyqs/?type=syllabus_practice")
    assert res_prac.status_code == 200
    data_prac = res_prac.json()
    assert all(item["question_type"] == "syllabus_practice" for item in data_prac)
    assert any(item["id"] == practice.id for item in data_prac)
    assert not any(item["id"] == pyq.id for item in data_prac)


def test_mock_tests_never_include_invalid_questions(db_session: Session):
    """Requirement 9: Mock tests strictly exclude invalid or unverified questions."""
    service = MockTestService(db_session)

    # Insert 2 valid questions
    for i in range(2):
        valid = PYQ(
            exam_name="TNPSC Group 4",
            year=2024,
            question_text=f"Valid Question #{i+1}?",
            options=[f"Choice {j}" for j in range(4)],
            correct_answer="Choice 0",
            is_verified=True,
            quality_status="valid",
            question_type="syllabus_practice",
        )
        db_session.add(valid)

    # Insert an invalid question with a fake title
    invalid_q = PYQ(
        exam_name="TNPSC Group 4",
        year=2024,
        question_text="Invalid question that should never appear in test",
        options=["Wrong 1", "Wrong 2", "Wrong 3", "Wrong 4"],
        correct_answer="Wrong 1",
        is_verified=False,
        quality_status="invalid",
        question_type="invalid",
        rejection_reason="Unverified",
    )
    db_session.add(invalid_q)
    db_session.commit()

    # Create mock test requesting 2 questions
    test = service.create_mock_test(
        exam_name="TNPSC Group 4",
        total_questions=2,
    )
    test_pyq_ids = [q.pyq_id for q in test.questions if q.pyq_id]
    assert invalid_q.id not in test_pyq_ids
    assert len(test_pyq_ids) == 2


def test_user_attempt_history_and_scoring_intact(db_session: Session):
    """Requirement 10: Mock test submission and scoring work properly with valid MCQs."""
    service = MockTestService(db_session)

    # Insert 2 valid questions
    q1_db = PYQ(
        exam_name="TNPSC Group 4",
        year=2024,
        question_text="What is the state flower of Tamil Nadu?",
        options=["Gloriosa Lily", "Lotus", "Rose", "Jasmine"],
        correct_answer="Gloriosa Lily",
        is_verified=True,
        quality_status="valid",
        question_type="verified_pyq",
    )
    q2_db = PYQ(
        exam_name="TNPSC Group 4",
        year=2024,
        question_text="What is the state animal of Tamil Nadu?",
        options=["Nilgiri Tahr", "Tiger", "Elephant", "Leopard"],
        correct_answer="Nilgiri Tahr",
        is_verified=True,
        quality_status="valid",
        question_type="verified_pyq",
    )
    db_session.add(q1_db)
    db_session.add(q2_db)
    db_session.commit()

    test = service.create_mock_test(
        exam_name="TNPSC Group 4",
        total_questions=2,
    )

    q1 = test.questions[0]
    q2 = test.questions[1]

    # Find the correct letter for q1
    corr_letter_q1 = service._answer_letter(q1.correct_answer, q1.options)

    # Intentionally answer q1 correctly and q2 incorrectly
    wrong_letter_q2 = "B" if service._answer_letter(q2.correct_answer, q2.options) == "A" else "A"

    attempt = service.submit_attempt(
        test_id=test.id,
        answers={
            str(q1.id): corr_letter_q1,
            str(q2.id): wrong_letter_q2,
        },
        time_taken_seconds=60,
    )

    assert attempt.is_submitted is True
    assert attempt.total_answered == 2
    assert attempt.incorrect_count == 1
    # TNPSC negative marking is 0.0, so score is 1.0
    assert attempt.score == 1.0
    assert attempt.accuracy == 50
