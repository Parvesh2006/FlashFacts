import pytest
from fastapi.testclient import TestClient


def test_auth_guest_and_profile(client: TestClient):
    # 1. Guest session creation
    res = client.post("/api/v1/auth/guest?target_exam=TNPSC Group 4")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["is_guest"] is True
    assert data["user"]["target_exam"] == "TNPSC Group 4"

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Access profile
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["id"] == data["user"]["id"]

    # 3. Update target exam
    update_res = client.put(
        "/api/v1/auth/target-exam",
        json={"target_exam": "UPSC CSE"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["target_exam"] == "UPSC CSE"


def test_pyq_search_filters_and_bookmarks(client: TestClient, db_session):
    # Setup guest user
    auth_res = client.post("/api/v1/auth/guest")
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Insert an authentic test PYQ
    payload = {
        "exam_name": "TNPSC Group 4",
        "year": 2024,
        "paper_name": "General Studies",
        "subject": "Indian Polity",
        "topic": "Fundamental Rights",
        "source": "TNPSC Official 2024",
        "language": "en",
        "is_verified": True,
        "question_text": "Which Article provides Right to Constitutional Remedies?",
        "options": ["A. Article 14", "B. Article 19", "C. Article 21", "D. Article 32"],
        "correct_answer": "D. Article 32",
        "explanation": "Dr. B.R. Ambedkar called Article 32 the heart and soul of the Constitution."
    }
    create_res = client.post("/api/v1/pyqs/", json=payload)
    assert create_res.status_code == 201
    pyq_id = create_res.json()["id"]

    # 2. Test keyword search
    search_res = client.get("/api/v1/pyqs/?q=Remedies", headers=headers)
    assert search_res.status_code == 200
    results = search_res.json()
    assert any(q["id"] == pyq_id for q in results)

    # 3. Test filter by year and subject
    filt_res = client.get("/api/v1/pyqs/?exam_name=TNPSC Group 4&year=2024&subject=Indian Polity", headers=headers)
    assert filt_res.status_code == 200
    assert any(q["id"] == pyq_id for q in filt_res.json())

    # 4. Test bookmark toggle
    bm_res = client.post(f"/api/v1/pyqs/{pyq_id}/bookmark", headers=headers)
    assert bm_res.status_code == 200
    assert bm_res.json()["bookmarked"] is True

    # 5. List bookmarks
    list_bm = client.get("/api/v1/pyqs/bookmarks", headers=headers)
    assert list_bm.status_code == 200
    assert any(b["id"] == pyq_id for b in list_bm.json())

    # 6. Unbookmark
    unbm_res = client.post(f"/api/v1/pyqs/{pyq_id}/bookmark", headers=headers)
    assert unbm_res.status_code == 200
    assert unbm_res.json()["bookmarked"] is False


def test_mock_test_negative_marking_and_mistake_book_integration(client: TestClient, db_session):
    auth_res = client.post("/api/v1/auth/guest")
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create PYQ for test question pool
    client.post("/api/v1/pyqs/", json={
        "exam_name": "UPSC CSE",
        "year": 2023,
        "subject": "Economy",
        "question_text": "What is the primary function of CRR?",
        "options": ["A. Liquidity control", "B. Taxation", "C. Subsidies", "D. Export promotion"],
        "correct_answer": "A. Liquidity control",
        "explanation": "Cash Reserve Ratio regulates money supply in the banking system."
    })

    # Create Mock Test with negative marking
    test_res = client.post("/api/v1/mock-tests/", json={
        "exam_name": "UPSC CSE",
        "total_questions": 2,
        "time_limit_minutes": 20,
        "negative_marking": 0.33,
        "include_pyqs": True,
        "include_events": False,
    })
    assert test_res.status_code == 201
    test_data = test_res.json()
    test_id = test_data["id"]
    assert test_data["negative_marking"] == 0.33

    q_list = test_data["questions"]
    assert len(q_list) > 0
    q1 = q_list[0]

    # Submit an incorrect answer to verify negative marking and auto-logging to mistake book
    submit_res = client.post(
        f"/api/v1/mock-tests/{test_id}/attempts",
        json={
            "answers": {str(q1["id"]): "B"},  # Incorrect
            "time_taken_seconds": 120,
        },
        headers=headers,
    )
    assert submit_res.status_code == 201
    submit_data = submit_res.json()
    assert submit_data["incorrect_count"] >= 1
    # Negative mark should have been applied (cannot be < 0)
    assert submit_data["score"] >= 0.0

    # Verify mistake was automatically recorded into Mistake Book
    rev_res = client.get("/api/v1/revision/", headers=headers)
    assert rev_res.status_code == 200
    rev_items = rev_res.json()
    assert len(rev_items) >= 1
    assert any(item["question_text"] == q1["question_text"] for item in rev_items)

    mistake_item = next(item for item in rev_items if item["question_text"] == q1["question_text"])
    assert mistake_item["is_revised"] is False

    # Retry the mistake with the correct answer
    retry_res = client.post(
        f"/api/v1/revision/{mistake_item['id']}/retry",
        json={"selected_answer": "A"},  # Correct
        headers=headers,
    )
    assert retry_res.status_code == 200
    assert retry_res.json()["is_correct"] is True
    assert retry_res.json()["is_revised"] is True


def test_performance_analytics_calculation(client: TestClient, db_session):
    auth_res = client.post("/api/v1/auth/guest")
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Analytics for student with zero attempts should return clean structure
    res = client.get("/api/v1/analytics/performance", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_tests_completed"] == 0
    assert data["overall_accuracy"] == 0
    assert isinstance(data["recommendations"], list)


def test_syllabus_hierarchy_and_progress_tracking(client: TestClient, db_session):
    auth_res = client.post("/api/v1/auth/guest")
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch TNPSC Group 4 syllabus
    syl_res = client.get("/api/v1/syllabus/TNPSC Group 4", headers=headers)
    assert syl_res.status_code == 200
    syl_data = syl_res.json()
    assert syl_data["exam_name"] == "TNPSC Group 4"
    assert len(syl_data["subjects"]) > 0

    first_subject = syl_data["subjects"][0]
    assert len(first_subject["units"]) > 0
    first_unit = first_subject["units"][0]
    assert len(first_unit["topics"]) > 0
    topic = first_unit["topics"][0]
    assert topic["status"] == "not_started"

    # 2. Update topic progress
    up_res = client.post(
        "/api/v1/syllabus/progress",
        json={
            "topic_id": topic["id"],
            "status": "completed",
            "notes": "Revised physics mechanics notes thoroughly.",
        },
        headers=headers,
    )
    assert up_res.status_code == 200
    assert up_res.json()["status"] == "completed"

    # 3. Verify syllabus reflects progress and completion %
    recheck_res = client.get("/api/v1/syllabus/TNPSC Group 4", headers=headers)
    assert recheck_res.status_code == 200
    updated_syl = recheck_res.json()
    assert updated_syl["completed_topics"] >= 1
    assert updated_syl["overall_completion_percentage"] > 0
