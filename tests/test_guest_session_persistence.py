import pytest
from fastapi.testclient import TestClient


def test_fresh_guest_starts_with_empty_mistake_book_and_performance(client: TestClient):
    # 1. Initialize fresh guest session
    guest_res = client.post("/api/v1/auth/guest?target_exam=TNPSC Group 4")
    assert guest_res.status_code == 200
    guest_data = guest_res.json()
    token = guest_data["access_token"]
    user = guest_data["user"]
    assert user["is_guest"] is True
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Verify Mistake Book is empty
    rev_res = client.get("/api/v1/revision/", headers=headers)
    assert rev_res.status_code == 200
    assert rev_res.json() == []

    summary_res = client.get("/api/v1/revision/summary", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_count"] == 0
    assert summary["pending_count"] == 0
    assert summary["revised_count"] == 0

    # 3. Verify Performance Analytics is empty
    perf_res = client.get("/api/v1/analytics/performance", headers=headers)
    assert perf_res.status_code == 200
    perf = perf_res.json()
    assert perf["total_tests_completed"] == 0
    assert perf["total_questions_attempted"] == 0


def test_guest_mock_test_creates_attempt_and_records_mistakes(client: TestClient):
    # 1. Create a guest session
    guest_res = client.post("/api/v1/auth/guest?target_exam=TNPSC Group 4")
    assert guest_res.status_code == 200
    token = guest_res.json()["access_token"]
    guest_headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed a PYQ for TNPSC Group 4
    pyq_res = client.post(
        "/api/v1/pyqs/",
        json={
            "exam_name": "TNPSC Group 4",
            "year": 2024,
            "subject": "General Studies",
            "question_text": "Which fundamental right is guaranteed under Article 21 of the Indian Constitution?",
            "options": [
                "Right to Equality",
                "Right to Life and Personal Liberty",
                "Right to Freedom of Religion",
                "Right to Constitutional Remedies",
            ],
            "correct_answer": "Right to Life and Personal Liberty",
        },
    )
    assert pyq_res.status_code == 201

    # 3. Generate a mock test
    test_res = client.post(
        "/api/v1/mock-tests/",
        json={"exam_name": "TNPSC Group 4", "total_questions": 1, "include_pyqs": True},
        headers=guest_headers,
    )
    assert test_res.status_code == 201
    test_data = test_res.json()
    test_id = test_data["id"]
    q1 = test_data["questions"][0]

    # 4. Submit test attempt with wrong answer as guest
    submit_res = client.post(
        f"/api/v1/mock-tests/{test_id}/attempts",
        json={"answers": {str(q1["id"]): "Right to Equality"}},
        headers=guest_headers,
    )
    assert submit_res.status_code == 201
    submit_data = submit_res.json()
    assert submit_data["total_answered"] == 1

    # 5. Verify Mistake Book now has this question logged for the guest!
    rev_items_res = client.get("/api/v1/revision/", headers=guest_headers)
    assert rev_items_res.status_code == 200
    items = rev_items_res.json()
    assert len(items) == 1
    assert items[0]["question_text"] == "Which fundamental right is guaranteed under Article 21 of the Indian Constitution?"
    assert items[0]["is_revised"] is False
    assert items[0]["mistake_count"] >= 1
    item_id = items[0]["id"]

    # 6. Verify Summary counts
    summary = client.get("/api/v1/revision/summary", headers=guest_headers).json()
    assert summary["total_count"] == 1
    assert summary["pending_count"] == 1
    assert summary["revised_count"] == 0

    # 7. Verify Performance Analytics updated
    perf = client.get("/api/v1/analytics/performance", headers=guest_headers).json()
    assert perf["total_tests_completed"] == 1
    assert perf["total_questions_attempted"] == 1

    # 8. Mark item as revised/mastered
    patch_res = client.patch(f"/api/v1/revision/{item_id}/status", json={"is_revised": True}, headers=guest_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["is_revised"] is True

    summary2 = client.get("/api/v1/revision/summary", headers=guest_headers).json()
    assert summary2["total_count"] == 1
    assert summary2["pending_count"] == 0
    assert summary2["revised_count"] == 1


def test_session_isolation_between_distinct_guests(client: TestClient):
    # Guest A
    guest_a = client.post("/api/v1/auth/guest?target_exam=TNPSC Group 4").json()
    headers_a = {"Authorization": f"Bearer {guest_a['access_token']}"}

    # Seed PYQ
    client.post(
        "/api/v1/pyqs/",
        json={
            "exam_name": "UPSC CSE",
            "year": 2023,
            "question_text": "What is the capital of Tamil Nadu?",
            "options": ["Chennai", "Madurai", "Coimbatore", "Trichy"],
            "correct_answer": "Chennai",
        },
    )

    # Guest A creates a test & makes mistake
    test = client.post("/api/v1/mock-tests/", json={"exam_name": "UPSC CSE", "total_questions": 1}, headers=headers_a).json()
    q = test["questions"][0]

    client.post(f"/api/v1/mock-tests/{test['id']}/attempts", json={"answers": {str(q['id']): "Madurai"}}, headers=headers_a)

    # Guest A has 1 mistake
    assert len(client.get("/api/v1/revision/", headers=headers_a).json()) == 1

    # Guest B (fresh anonymous session)
    guest_b = client.post("/api/v1/auth/guest?target_exam=UPSC CSE").json()
    headers_b = {"Authorization": f"Bearer {guest_b['access_token']}"}

    # Guest B MUST have 0 mistakes and 0 attempts
    assert len(client.get("/api/v1/revision/", headers=headers_b).json()) == 0
    sum_b = client.get("/api/v1/revision/summary", headers=headers_b).json()
    assert sum_b["total_count"] == 0
    assert sum_b["pending_count"] == 0
    assert sum_b["revised_count"] == 0

    perf_b = client.get("/api/v1/analytics/performance", headers=headers_b).json()
    assert perf_b["total_tests_completed"] == 0


def test_guest_data_merges_into_student_account_on_register(client: TestClient):
    # 1. Guest creates mistake
    guest = client.post("/api/v1/auth/guest").json()
    guest_id = guest["user"]["id"]
    guest_headers = {"Authorization": f"Bearer {guest['access_token']}"}

    # Add PYQ
    client.post(
        "/api/v1/pyqs/",
        json={
            "exam_name": "TNPSC Group 4",
            "year": 2024,
            "question_text": "Merge Revision Test Question",
            "options": ["Opt A", "Opt B", "Opt C", "Opt D"],
            "correct_answer": "Opt A",
        },
    )

    test = client.post("/api/v1/mock-tests/", json={"exam_name": "TNPSC Group 4", "total_questions": 1}, headers=guest_headers).json()
    q = test["questions"][0]
    client.post(f"/api/v1/mock-tests/{test['id']}/attempts", json={"answers": {str(q['id']): "Opt B"}}, headers=guest_headers)

    # 2. Register new student account with guest_user_id
    student = client.post(
        "/api/v1/auth/register",
        json={
            "username": "student_with_merged_mistakes",
            "password": "Password123!",
            "email": "student_mistakes@example.com",
            "guest_user_id": guest_id,
        },
    ).json()
    student_headers = {"Authorization": f"Bearer {student['access_token']}"}

    # 3. Student has the mistake in Mistake Book
    student_rev = client.get("/api/v1/revision/", headers=student_headers).json()
    assert len(student_rev) == 1
    assert student_rev[0]["question_text"] == "Merge Revision Test Question"

    # 4. Student has the test attempt in Performance Analytics
    student_perf = client.get("/api/v1/analytics/performance", headers=student_headers).json()
    assert student_perf["total_tests_completed"] == 1


def test_authenticated_user_history_persistence_and_isolation(client: TestClient):
    """
    Verify:
    - User A logs in and has their own saved records.
    - User B logs in and has their own saved records.
    - Neither user sees the other's mistake book records.
    """
    # 1. Register User A
    user_a_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "user_alpha_reviser",
            "password": "Password123!",
            "email": "alpha_rev@example.com",
            "target_exam": "TNPSC Group 4",
        },
    )
    assert user_a_res.status_code == 201
    headers_a = {"Authorization": f"Bearer {user_a_res.json()['access_token']}"}

    # User A saves a custom revision item
    save_a = client.post(
        "/api/v1/revision/save",
        json={
            "question_text": "Alpha Specific Article 14 Question",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "selected_answer": "B",
            "exam_name": "TNPSC Group 4",
            "subject": "Polity",
        },
        headers=headers_a,
    )
    assert save_a.status_code == 201

    # 2. Register User B
    user_b_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "user_beta_reviser",
            "password": "Password123!",
            "email": "beta_rev@example.com",
            "target_exam": "UPSC CSE",
        },
    )
    assert user_b_res.status_code == 201
    headers_b = {"Authorization": f"Bearer {user_b_res.json()['access_token']}"}

    # User B saves a different revision item
    save_b = client.post(
        "/api/v1/revision/save",
        json={
            "question_text": "Beta Specific Monsoon Question",
            "options": ["SW Monsoon", "NE Monsoon", "Retreating", "Western Disturbances"],
            "correct_answer": "SW Monsoon",
            "selected_answer": "NE Monsoon",
            "exam_name": "UPSC CSE",
            "subject": "Geography",
        },
        headers=headers_b,
    )
    assert save_b.status_code == 201

    # 3. Check User A only sees Alpha question
    rev_a = client.get("/api/v1/revision/", headers=headers_a).json()
    assert len(rev_a) == 1
    assert rev_a[0]["question_text"] == "Alpha Specific Article 14 Question"

    # 4. Check User B only sees Beta question
    rev_b = client.get("/api/v1/revision/", headers=headers_b).json()
    assert len(rev_b) == 1
    assert rev_b[0]["question_text"] == "Beta Specific Monsoon Question"


def test_mock_test_scoring_with_negative_marking_for_guest(client: TestClient):
    """
    Verify server-side scoring calculation:
    - Correct answer: +1.0
    - Incorrect answer: -0.25 (negative marking)
    - Unanswered question: 0.0
    - Missed/skipped questions automatically logged to Mistake Book
    """
    guest = client.post("/api/v1/auth/guest?target_exam=TNPSC Group 4").json()
    guest_headers = {"Authorization": f"Bearer {guest['access_token']}"}

    # Create 3 PYQs with valid, non-fragment 4-option MCQs
    for i in range(1, 4):
        p_res = client.post(
            "/api/v1/pyqs/",
            json={
                "exam_name": "TNPSC Group 4",
                "year": 2024,
                "question_text": f"Negative Marking Test Q{i} on Constitutional Law",
                "options": [
                    f"Correct Option A for item {i}",
                    f"Wrong Option B for item {i}",
                    f"Wrong Option C for item {i}",
                    f"Wrong Option D for item {i}",
                ],
                "correct_answer": f"Correct Option A for item {i}",
            },
        )
        assert p_res.status_code == 201

    # Create mock test with 3 questions and 0.25 negative marking
    test_res = client.post(
        "/api/v1/mock-tests/",
        json={
            "exam_name": "TNPSC Group 4",
            "total_questions": 3,
            "negative_marking": 0.25,
            "include_pyqs": True,
        },
        headers=guest_headers,
    )
    assert test_res.status_code == 201
    test = test_res.json()

    q_list = test["questions"]
    assert len(q_list) >= 3

    # Submit: Q1 correct, Q2 wrong, Q3 skipped
    q1 = q_list[0]
    q2 = q_list[1]

    # Dynamically find the correct option from shuffled list
    correct_opt = next(opt for opt in q1["options"] if "Correct Option A" in opt)
    wrong_opt = next(opt for opt in q2["options"] if "Wrong Option B" in opt)

    answers = {
        str(q1["id"]): correct_opt,  # Guaranteed correct
        str(q2["id"]): wrong_opt,    # Guaranteed wrong
    }

    submit_res = client.post(
        f"/api/v1/mock-tests/{test['id']}/attempts",
        json={"answers": answers, "time_taken_seconds": 60},
        headers=guest_headers,
    )
    assert submit_res.status_code == 201
    result = submit_res.json()

    # Score: 1.0 - 0.25 = 0.75
    assert result["score"] == 0.75
    assert result["total_answered"] == 2
    assert result["incorrect_count"] == 1
    assert result["unanswered_count"] == 1

    # Verify Mistake Book logged both missed and skipped questions
    summary = client.get("/api/v1/revision/summary", headers=guest_headers).json()
    assert summary["total_count"] == 2
    assert summary["pending_count"] == 2
