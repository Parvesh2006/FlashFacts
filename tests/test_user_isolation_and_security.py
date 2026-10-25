import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token


def test_invalid_token_returns_401(client: TestClient):
    # Requesting with invalid token must return 401 Unauthorized
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer totally_bogus_token"})
    assert res.status_code == 401
    assert "Invalid or expired token" in res.json().get("detail", "")

    # Requesting with expired token must return 401 Unauthorized
    expired_token = create_access_token({"sub": "some_user"}, expires_in=-100)
    res2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res2.status_code == 401


def test_user_data_isolation_between_two_users(client: TestClient, db_session):
    # 1. Create User 1 (Guest A)
    u1_res = client.post("/api/v1/auth/guest?target_exam=TNPSC Group 4")
    assert u1_res.status_code == 200
    u1_token = u1_res.json()["access_token"]
    u1_headers = {"Authorization": f"Bearer {u1_token}"}
    u1_id = u1_res.json()["user"]["id"]

    # 2. Create User 2 (Guest B)
    u2_res = client.post("/api/v1/auth/guest?target_exam=UPSC CSE")
    assert u2_res.status_code == 200
    u2_token = u2_res.json()["access_token"]
    u2_headers = {"Authorization": f"Bearer {u2_token}"}
    u2_id = u2_res.json()["user"]["id"]

    assert u1_id != u2_id

    # 3. Test PYQ Bookmarking Isolation
    # Create test PYQ
    pyq_res = client.post("/api/v1/pyqs/", json={
        "exam_name": "TNPSC Group 4",
        "year": 2024,
        "subject": "Indian Polity",
        "question_text": "Security Isolation Test Question",
        "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
        "correct_answer": "A. Option 1",
    })
    pyq_id = pyq_res.json()["id"]

    # User 1 bookmarks it
    client.post(f"/api/v1/pyqs/{pyq_id}/bookmark", headers=u1_headers)

    # User 1 sees it in bookmarks
    u1_bms = client.get("/api/v1/pyqs/bookmarks", headers=u1_headers).json()
    assert any(b["id"] == pyq_id for b in u1_bms)

    # User 2 MUST NOT see it in their bookmarks
    u2_bms = client.get("/api/v1/pyqs/bookmarks", headers=u2_headers).json()
    assert not any(b["id"] == pyq_id for b in u2_bms)

    # 4. Test Mock Test Attempt Ownership & Isolation
    test_res = client.post("/api/v1/mock-tests/", json={
        "exam_name": "TNPSC Group 4",
        "total_questions": 1,
        "include_pyqs": True,
        "include_events": False,
    })
    test_id = test_res.json()["id"]
    test_q = test_res.json()["questions"][0]

    # User 1 attempts the test
    attempt_res = client.post(
        f"/api/v1/mock-tests/{test_id}/attempts",
        json={"answers": {str(test_q["id"]): "B"}},
        headers=u1_headers,
    )
    assert attempt_res.status_code == 201
    attempt_id = attempt_res.json()["id"]

    # User 1 can access attempt review
    u1_review = client.get(f"/api/v1/mock-tests/{test_id}/attempts/{attempt_id}", headers=u1_headers)
    assert u1_review.status_code == 200

    # User 2 attempting to access User 1's attempt review MUST be denied with 403 Forbidden
    u2_review = client.get(f"/api/v1/mock-tests/{test_id}/attempts/{attempt_id}", headers=u2_headers)
    assert u2_review.status_code == 403
    assert "Not authorized" in u2_review.json().get("detail", "")

    # 5. Test Mistake Book Isolation
    # User 1's mistake from the failed attempt should appear in User 1's revision items
    u1_rev = client.get("/api/v1/revision/", headers=u1_headers).json()
    assert len(u1_rev) >= 1
    u1_mistake_id = u1_rev[0]["id"]

    # User 2 MUST NOT see User 1's mistakes
    u2_rev = client.get("/api/v1/revision/", headers=u2_headers).json()
    assert not any(it["id"] == u1_mistake_id for it in u2_rev)

    # User 2 attempting to retry or delete User 1's mistake MUST fail
    retry_res = client.post(
        f"/api/v1/revision/{u1_mistake_id}/retry",
        json={"selected_answer": "A"},
        headers=u2_headers,
    )
    assert retry_res.status_code == 404

    del_res = client.delete(f"/api/v1/revision/{u1_mistake_id}", headers=u2_headers)
    assert del_res.status_code == 404

    # 6. Test Syllabus Progress Isolation
    syl = client.get("/api/v1/syllabus/TNPSC Group 4", headers=u1_headers).json()
    topic = syl["subjects"][0]["units"][0]["topics"][0]

    # User 1 marks topic as completed
    client.post(
        "/api/v1/syllabus/progress",
        json={"topic_id": topic["id"], "status": "completed", "notes": "Private User 1 Notes"},
        headers=u1_headers,
    )

    # User 1 sees topic as completed with notes
    u1_syl = client.get("/api/v1/syllabus/TNPSC Group 4", headers=u1_headers).json()
    u1_topic = u1_syl["subjects"][0]["units"][0]["topics"][0]
    assert u1_topic["status"] == "completed"
    assert u1_topic["notes"] == "Private User 1 Notes"

    # User 2 MUST see topic as not_started without User 1's notes
    u2_syl = client.get("/api/v1/syllabus/TNPSC Group 4", headers=u2_headers).json()
    u2_topic = u2_syl["subjects"][0]["units"][0]["topics"][0]
    assert u2_topic["status"] == "not_started"
    assert u2_topic["notes"] is None or u2_topic["notes"] == ""
