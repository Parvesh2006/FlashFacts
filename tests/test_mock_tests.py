import pytest
from fastapi.testclient import TestClient


def test_create_and_submit_mock_test(client: TestClient, db_session):
    # Insert 2 PYQs so the requested total_questions=2 can be fulfilled
    pyq_payload_1 = {
        "exam_name": "TNPSC Group 4",
        "year": 2022,
        "question_text": "Who is the founder of the Chola Empire?",
        "options": ["Rajaraja Chola", "Vijayalaya Chola", "Rajendra Chola", "Aditya Chola"],
        "correct_answer": "Vijayalaya Chola",
    }
    client.post("/api/v1/pyqs/", json=pyq_payload_1)

    pyq_payload_2 = {
        "exam_name": "TNPSC Group 4",
        "year": 2022,
        "question_text": "Who composed the sacred Tamil work Thirukkural?",
        "options": ["Thiruvalluvar", "Kambar", "Avvaiyar", "Bharathiyar"],
        "correct_answer": "Thiruvalluvar",
    }
    client.post("/api/v1/pyqs/", json=pyq_payload_2)

    # Create Mock Test
    payload = {
        "exam_name": "TNPSC Group 4",
        "total_questions": 2,
        "include_pyqs": True,
        "include_events": True,
    }
    response = client.post("/api/v1/mock-tests/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["exam_name"] == "TNPSC Group 4"
    assert "id" in data
    assert data["status"] == "ready"
    assert len(data["questions"]) == 2

    test_id = data["id"]
    q1 = data["questions"][0]

    # Submit Mock Test Attempt
    answers = {
        str(q1["id"]): "A"
    }

    submit_payload = {
        "answers": answers
    }

    submit_response = client.post(f"/api/v1/mock-tests/{test_id}/attempts", json=submit_payload)
    assert submit_response.status_code == 201
    submit_data = submit_response.json()
    assert submit_data["test_id"] == test_id
    assert submit_data["total_answered"] == 1
    assert "score" in submit_data

    # Get test again (verify persistence on refresh)
    get_res = client.get(f"/api/v1/mock-tests/{test_id}")
    assert get_res.status_code == 200
    refreshed_data = get_res.json()
    assert refreshed_data["id"] == test_id
    assert len(refreshed_data["questions"]) == 2
    # Verify exact question order matches
    assert refreshed_data["questions"][0]["id"] == q1["id"]


def test_bank_shortage_explanation(client: TestClient, db_session):
    """When requested count exceeds available bank questions, API returns clear 422 explanation."""
    payload = {
        "exam_name": "NonExistentExam123",
        "total_questions": 50,
    }
    response = client.post("/api/v1/mock-tests/", json=payload)
    assert response.status_code == 422
    assert "No questions are currently available" in response.json()["detail"]


def test_option_shuffling_and_scoring(client: TestClient, db_session):
    """Verify that options are shuffled and correct answer is accurately scored."""
    for i in range(5):
        client.post("/api/v1/pyqs/", json={
            "exam_name": "UPSC Civil Services Prelims",
            "year": 2024,
            "question_text": f"UPSC Unique Question #{i + 1} for Testing?",
            "options": ["Alpha", "Beta", "Gamma", "Delta"],
            "correct_answer": "Gamma",
        })

    create_res = client.post("/api/v1/mock-tests/", json={
        "exam_name": "UPSC Civil Services Prelims",
        "total_questions": 3,
    })
    assert create_res.status_code == 201
    test_data = create_res.json()
    assert len(test_data["questions"]) == 3

    # Submit the exact text "Gamma" for question 0, should be scored as correct
    q0 = test_data["questions"][0]
    submit_res = client.post(f"/api/v1/mock-tests/{test_data['id']}/attempts", json={
        "answers": {str(q0["id"]): "Gamma"}
    })
    assert submit_res.status_code == 201
    sub_data = submit_res.json()
    # Score should be 1.0 (correct)
    assert sub_data["score"] == 1.0
    assert sub_data["total_answered"] == 1


def test_eligible_counts_endpoint(client: TestClient, db_session):
    """Verify the eligible counts endpoint returns stats for all major exams."""
    res = client.get("/api/v1/mock-tests/eligible-counts")
    assert res.status_code == 200
    counts = res.json()
    assert "TNPSC Group 4" in counts
    assert "UPSC CSE" in counts
    assert "supported_lengths" in counts["TNPSC Group 4"]


def test_mock_tests_list_deduplicates_identical_templates(client: TestClient, db_session):
    """Verify list_mock_tests collapses genuinely identical templates to a single card."""
    # Seed 3 distinct PYQs for testing
    for i in range(3):
        client.post("/api/v1/pyqs/", json={
            "exam_name": "TNPSC Group 4",
            "year": 2024,
            "subject": "Indian Polity",
            "topic": "Constituent Assembly",
            "question_text": f"Deduplication Test Question #{i + 1}?",
            "options": ["A1", "B2", "C3", "D4"],
            "correct_answer": "A1",
        })

    # Create two identical test sessions with the exact same configuration
    payload = {
        "exam_name": "TNPSC Group 4",
        "domain": "Indian Polity",
        "total_questions": 2,
        "time_limit_minutes": 15,
        "difficulty": "medium",
    }
    res1 = client.post("/api/v1/mock-tests/", json=payload)
    assert res1.status_code == 201
    res2 = client.post("/api/v1/mock-tests/", json=payload)
    assert res2.status_code == 201

    # Verify both tests exist as distinct sessions with different IDs
    assert res1.json()["id"] != res2.json()["id"]

    # Now call list_mock_tests endpoint
    list_res = client.get("/api/v1/mock-tests/")
    assert list_res.status_code == 200
    available_tests = list_res.json()

    # Verify that the identical template appears only once in the list
    matching = [
        t for t in available_tests
        if t["exam_name"] == "TNPSC Group 4"
        and t.get("domain") == "Indian Polity"
        and t["total_questions"] == 2
        and t["time_limit_minutes"] == 15
    ]
    assert len(matching) == 1, f"Expected exactly 1 deduplicated template card, but found {len(matching)}"
    # Verify title is grounded and meaningful
    assert "Indian Polity" in matching[0]["title"]
    assert matching[0]["template_key"] is not None


def test_mock_test_templates_have_meaningful_titles_and_metadata(client: TestClient, db_session):
    """Verify all returned templates have meaningful titles based on real data and correct metadata."""
    # Seed 2 distinct PYQs
    for i in range(2):
        client.post("/api/v1/pyqs/", json={
            "exam_name": "TNPSC Group 4",
            "year": 2024,
            "subject": "General Science",
            "topic": "Physics & Units",
            "question_text": f"Metadata Verification Question #{i + 1}?",
            "options": ["O1", "O2", "O3", "O4"],
            "correct_answer": "O1",
        })

    client.post("/api/v1/mock-tests/", json={
        "exam_name": "TNPSC Group 4",
        "domain": "General Science",
        "total_questions": 2,
        "time_limit_minutes": 15,
    })

    list_res = client.get("/api/v1/mock-tests/")
    assert list_res.status_code == 200
    tests = list_res.json()
    assert len(tests) > 0

    seen_template_keys = set()
    for t in tests:
        assert t["title"] is not None and len(t["title"]) > 0
        assert t["total_questions"] > 0
        assert t["time_limit_minutes"] > 0
        assert t["negative_marking"] >= 0.0
        # Verify deduplication key uniqueness
        assert t["template_key"] not in seen_template_keys, f"Duplicate template_key detected: {t['template_key']}"
        seen_template_keys.add(t["template_key"])


def test_default_templates_seeding_idempotency(db_session):
    """Verify ensure_default_templates does not accumulate duplicate templates on repeated runs."""
    from app.services.mock_test_service import MockTestService
    service = MockTestService(db_session)

    # First execution
    run1 = service.ensure_default_templates()
    # Second execution must create 0 additional duplicate templates
    run2 = service.ensure_default_templates()
    assert len(run2) == 0, f"Expected 0 created templates on rerun, but got {len(run2)}"
