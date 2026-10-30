import pytest
from fastapi.testclient import TestClient


def test_register_and_login_flow(client: TestClient):
    # 1. Register a new user
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "student_tnpsc_01",
            "password": "SecretPassword123!",
            "email": "student_01@example.com",
            "target_exam": "TNPSC Group 4",
        },
    )
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "student_tnpsc_01"
    assert data["user"]["email"] == "student_01@example.com"
    assert not data["user"]["is_guest"]

    # 2. Duplicate registration fails
    dup_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "student_tnpsc_01",
            "password": "AnotherPassword",
        },
    )
    assert dup_res.status_code == 400

    # 3. Login with correct credentials
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "username": "student_tnpsc_01",
            "password": "SecretPassword123!",
        },
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 4. Login with incorrect password
    bad_login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "student_tnpsc_01",
            "password": "WrongPassword",
        },
    )
    assert bad_login.status_code == 401


def test_google_auth_flow(client: TestClient, monkeypatch):
    """Test Google auth with a mocked, verified tokeninfo response."""
    import httpx
    from app.api.v1 import auth

    monkeypatch.setattr(auth.settings, "GOOGLE_CLIENT_ID", "test-client-id")

    def fake_google_tokeninfo(*args, **kwargs):
        assert kwargs["params"]["id_token"] == "valid-test-token"
        return httpx.Response(
            200,
            json={
                "aud": "test-client-id",
                "email": "tamil_aspirant@gmail.com",
                "email_verified": True,
                "name": "Tamil Aspirant",
                "sub": "google-test-subject-001",
            },
            request=httpx.Request(
                "GET", "https://oauth2.googleapis.com/tokeninfo"
            ),
        )

    monkeypatch.setattr(httpx, "get", fake_google_tokeninfo)

    res = client.post(
        "/api/v1/auth/google",
        json={
            "credential": "valid-test-token",
            "target_exam": "TNPSC Group 2",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    user = data["user"]
    assert user["email"] == "tamil_aspirant@gmail.com"
    assert not user["is_guest"]
    assert user["target_exam"] == "TNPSC Group 2"

    # Re-authenticating returns the existing user.
    res2 = client.post(
        "/api/v1/auth/google",
        json={"credential": "valid-test-token"},
    )
    assert res2.status_code == 200, res2.text
    assert res2.json()["user"]["id"] == user["id"]


def test_guest_data_merge_on_registration(client: TestClient):
    # 1. Create a guest session
    guest_res = client.post("/api/v1/auth/guest?target_exam=TNPSC Group 4")
    assert guest_res.status_code == 200
    guest_token = guest_res.json()["access_token"]
    guest_id = guest_res.json()["user"]["id"]
    guest_headers = {"Authorization": f"Bearer {guest_token}"}

    # 2. Create a test PYQ and bookmark it as guest
    pyq_res = client.post(
        "/api/v1/pyqs/",
        json={
            "exam_name": "TNPSC Group 4",
            "year": 2024,
            "subject": "General Tamil",
            "question_text": "Guest Merge Test Question தமிழ்",
            "options": ["A. à®µà®¿à®Ÿà¯ˆ 1", "B. à®µà®¿à®Ÿà¯ˆ 2", "C. à®µà®¿à®Ÿà¯ˆ 3", "D. à®µà®¿à®Ÿà¯ˆ 4"],
            "correct_answer": "A. à®µà®¿à®Ÿà¯ˆ 1",
        },
    )
    assert pyq_res.status_code == 201
    pyq_id = pyq_res.json()["id"]

    bm_res = client.post(f"/api/v1/pyqs/{pyq_id}/bookmark", headers=guest_headers)
    assert bm_res.status_code == 200
    assert bm_res.json()["bookmarked"] is True

    # 3. Register a new student account, providing guest_user_id
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "merged_student_01",
            "password": "Password123!",
            "email": "merged_01@example.com",
            "guest_user_id": guest_id,
        },
    )
    assert reg_res.status_code == 201
    auth_token = reg_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # 4. Verify bookmarked PYQ is now owned by the registered student!
    auth_bookmarks = client.get("/api/v1/pyqs/bookmarks", headers=auth_headers).json()
    assert any(b["id"] == pyq_id for b in auth_bookmarks)


def test_explicit_merge_endpoint(client: TestClient):
    # 1. Create Guest session
    guest_res = client.post("/api/v1/auth/guest?target_exam=UPSC CSE")
    guest_token = guest_res.json()["access_token"]
    guest_headers = {"Authorization": f"Bearer {guest_token}"}

    # 2. Add a bookmark to guest
    pyq_res = client.post(
        "/api/v1/pyqs/",
        json={
            "exam_name": "UPSC CSE",
            "year": 2023,
            "subject": "Polity",
            "question_text": "Constitutional Amendment Merge Question",
            "options": ["A. Art 368", "B. Art 356", "C. Art 352", "D. Art 360"],
            "correct_answer": "A. Art 368",
        },
    )
    pyq_id = pyq_res.json()["id"]
    client.post(f"/api/v1/pyqs/{pyq_id}/bookmark", headers=guest_headers)

    # 3. Create a registered student
    student_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "student_explicit_merge",
            "password": "Password123!",
            "email": "explicit_merge@example.com",
        },
    )
    student_token = student_res.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 4. Explicitly call /api/v1/auth/merge
    merge_res = client.post(
        "/api/v1/auth/merge",
        json={"guest_token": guest_token},
        headers=student_headers,
    )
    assert merge_res.status_code == 200
    merge_data = merge_res.json()
    assert merge_data["merged"] is True
    assert merge_data["bookmarks_merged"] >= 1

    # 5. Verify bookmarks transferred
    student_bms = client.get("/api/v1/pyqs/bookmarks", headers=student_headers).json()
    assert any(b["id"] == pyq_id for b in student_bms)
