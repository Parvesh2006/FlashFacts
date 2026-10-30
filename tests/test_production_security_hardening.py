import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User


# =========================================================================
# 1. JWT Secret Validation Tests (Production vs Development)
# =========================================================================

def test_production_rejects_missing_jwt_secret():
    """Production must reject an empty or missing SECRET_KEY."""
    with pytest.raises(ValueError, match="SECRET_KEY is missing"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="",
            CORS_ORIGINS=["https://flashfacts.in"],
        )


def test_production_rejects_default_insecure_jwt_secret():
    """Production must reject known default or weak development secrets."""
    with pytest.raises(ValueError, match="Insecure or default SECRET_KEY detected"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="flashfacts_secure_exam_portal_key_2026",
            CORS_ORIGINS=["https://flashfacts.in"],
        )

    with pytest.raises(ValueError, match="Insecure or default SECRET_KEY detected"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="replace-with-a-strong-random-secret-before-deployment",
            CORS_ORIGINS=["https://flashfacts.in"],
        )


def test_production_rejects_short_jwt_secret():
    """Production must reject secrets shorter than 32 characters."""
    with pytest.raises(ValueError, match="Insecure or default SECRET_KEY detected"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="too_short_secret_under_32_ch",
            CORS_ORIGINS=["https://flashfacts.in"],
        )


def test_valid_production_configuration_accepted():
    """Production accepts a custom, strong 32+ char secret and explicit trusted domains."""
    valid_key = "a_super_strong_cryptographic_random_key_64_bytes_for_production_env"
    cfg = Settings(
        APP_ENV="production",
        SECRET_KEY=valid_key,
        CORS_ORIGINS=["https://flashfacts.in", "https://app.flashfacts.in"],
    )
    assert cfg.APP_ENV == "production"
    assert cfg.SECRET_KEY == valid_key
    assert cfg.CORS_ORIGINS == ["https://flashfacts.in", "https://app.flashfacts.in"]


# =========================================================================
# 2. CORS Configuration Tests (Wildcard Rejection vs Local Dev)
# =========================================================================

def test_production_rejects_cors_wildcard():
    """Production must reject wildcard origins ['*'] when credentials are enabled."""
    valid_key = "a_super_strong_cryptographic_random_key_64_bytes_for_production_env"
    with pytest.raises(ValueError, match="Wildcard CORS origin .* is rejected in production"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=valid_key,
            CORS_ORIGINS=["*"],
        )


def test_production_rejects_empty_cors_origins():
    """Production must reject an empty CORS origin list."""
    valid_key = "a_super_strong_cryptographic_random_key_64_bytes_for_production_env"
    with pytest.raises(ValueError, match="CORS_ORIGINS cannot be empty in production"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=valid_key,
            CORS_ORIGINS=[],
        )


def test_production_rejects_blank_and_whitespace_cors_origins():
    """Production rejects blank or whitespace-only entries in CORS_ORIGINS."""
    valid_key = "a_super_strong_cryptographic_random_key_64_bytes_for_production_env"
    with pytest.raises(ValueError, match="Empty or whitespace-only CORS origin"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=valid_key,
            CORS_ORIGINS=["https://flashfacts.in", "   "],
        )


def test_production_rejects_non_http_schemes():
    """Production rejects FTP, javascript, or other non-HTTP(S) CORS schemes."""
    valid_key = "a_super_strong_cryptographic_random_key_64_bytes_for_production_env"
    with pytest.raises(ValueError, match="Origin must start with an absolute 'http://' or 'https://' scheme"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=valid_key,
            CORS_ORIGINS=["ftp://flashfacts.in"],
        )


def test_production_rejects_malformed_urls_and_credentials():
    """Production rejects malformed URLs, missing hostnames, and credentials."""
    valid_key = "a_super_strong_cryptographic_random_key_64_bytes_for_production_env"
    with pytest.raises(ValueError, match="Origin must start with an absolute 'http://' or 'https://' scheme"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=valid_key,
            CORS_ORIGINS=["flashfacts.in"],
        )

    with pytest.raises(ValueError, match="User credentials in origin are not permitted"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=valid_key,
            CORS_ORIGINS=["https://admin:pass@flashfacts.in"],
        )


def test_production_rejects_paths_queries_and_fragments():
    """Production rejects paths, query strings, and fragments in CORS origins."""
    valid_key = "a_super_strong_cryptographic_random_key_64_bytes_for_production_env"
    with pytest.raises(ValueError, match="must not include a path component"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=valid_key,
            CORS_ORIGINS=["https://flashfacts.in/api"],
        )

    with pytest.raises(ValueError, match="must not include query parameters"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=valid_key,
            CORS_ORIGINS=["https://flashfacts.in?env=prod"],
        )

    with pytest.raises(ValueError, match="must not include a fragment identifier"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=valid_key,
            CORS_ORIGINS=["https://flashfacts.in#home"],
        )


def test_local_development_configuration_safe_fallback():
    """Development environment safely normalizes missing secrets and wildcard origins to localhost."""
    cfg = Settings(
        APP_ENV="development",
        SECRET_KEY="",
        CORS_ORIGINS=["*"],
    )
    assert cfg.APP_ENV == "development"
    assert len(cfg.SECRET_KEY) >= 32
    assert "http://localhost:3000" in cfg.CORS_ORIGINS
    assert "*" not in cfg.CORS_ORIGINS


# =========================================================================
# 3. Guest Session Creation & Accidental Row Prevention Tests
# =========================================================================

def test_unauthenticated_requests_do_not_create_guest_rows(client: TestClient, db_session: Session):
    """
    Public or protected requests lacking authentication must NOT accidentally insert
    orphan guest rows into the PostgreSQL users table.
    """
    initial_count = db_session.query(User).count()

    # 1. Access syllabus without token: public view should succeed (200) without creating a user row
    syl_res = client.get("/api/v1/syllabus/TNPSC Group 4")
    assert syl_res.status_code == 200
    assert db_session.query(User).count() == initial_count, "Viewing syllabus must not create a guest row"

    # 2. Access /api/v1/auth/me without token: must return 401 without creating a user row
    me_res = client.get("/api/v1/auth/me")
    assert me_res.status_code == 401
    assert "Authentication required" in me_res.json().get("detail", "")
    assert db_session.query(User).count() == initial_count, "Unauthenticated /auth/me must not create a guest row"

    # 3. Access /api/v1/revision/ without token: must return 401 without creating a user row
    rev_res = client.get("/api/v1/revision/")
    assert rev_res.status_code == 401
    assert db_session.query(User).count() == initial_count, "Unauthenticated /revision/ must not create a guest row"


def test_guest_session_initialization_and_persistence(client: TestClient, db_session: Session):
    """
    Explicit guest session initialization via POST /api/v1/auth/guest must create
    a persistent session that allows authenticated access.
    """
    initial_count = db_session.query(User).count()

    # Explicit guest session creation
    res = client.post("/api/v1/auth/guest?target_exam=TNPSC Group 4")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    token = data["access_token"]
    user_data = data["user"]
    assert user_data["is_guest"] is True
    assert db_session.query(User).count() == initial_count + 1

    # Accessing /auth/me with the guest token succeeds
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["id"] == user_data["id"]
    assert me_res.json()["is_guest"] is True


def test_guest_data_merging_into_registered_student(client: TestClient, db_session: Session):
    """
    Guest bookmarks and progress must merge cleanly into registered account upon registration.
    """
    # 1. Initialize guest session
    guest = client.post("/api/v1/auth/guest?target_exam=TNPSC Group 4").json()
    guest_id = guest["user"]["id"]
    guest_headers = {"Authorization": f"Bearer {guest['access_token']}"}

    # 2. Bookmark a PYQ as guest
    pyq = client.post("/api/v1/pyqs/", json={
        "exam_name": "TNPSC Group 4",
        "year": 2024,
        "question_text": "Security Phase 1 Verification PYQ?",
        "options": ["A1", "B2", "C3", "D4"],
        "correct_answer": "A1",
    }).json()
    pyq_id = pyq["id"]

    bm_res = client.post(f"/api/v1/pyqs/{pyq_id}/bookmark", headers=guest_headers)
    assert bm_res.status_code == 200

    # 3. Register permanent account with guest_user_id
    reg_res = client.post("/api/v1/auth/register", json={
        "username": "hardened_student_phase1",
        "password": "StrongPassword123!",
        "email": "hardened_phase1@example.com",
        "guest_user_id": guest_id,
    })
    assert reg_res.status_code == 201
    auth_headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    # 4. Registered user inherits the bookmark
    bms = client.get("/api/v1/pyqs/bookmarks", headers=auth_headers).json()
    assert any(b["id"] == pyq_id for b in bms)

    # 5. Temporary guest user record is cleaned up
    assert db_session.query(User).filter(User.id == guest_id).first() is None


# =========================================================================
# 4. Alembic Readiness and Zero Silent Migration Tests
# =========================================================================

def test_readiness_fails_if_alembic_head_outdated_in_staging(client: TestClient):
    """In staging, readiness endpoint must fail with 503 if database revision is outdated or missing."""
    with patch("app.api.v1.health.settings") as mock_settings, \
         patch("app.api.v1.health.verify_database_head") as mock_verify:
        mock_settings.APP_ENV = "staging"
        mock_verify.side_effect = RuntimeError("Database schema is outdated (current revision: '001', expected HEAD: '014')")

        res = client.get("/ready")
        assert res.status_code == 503
        assert "Database migration readiness check failed" in res.json().get("detail", "")


def test_readiness_succeeds_in_staging_when_head_matches(client: TestClient):
    """In staging, readiness endpoint returns 200 and verified migration status when HEAD matches."""
    with patch("app.api.v1.health.settings") as mock_settings, \
         patch("app.api.v1.health.verify_database_head", return_value="014_pyq_quality_and_type_fields"):
        mock_settings.APP_ENV = "staging"

        res = client.get("/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ready"
        assert "verified (HEAD: 014_pyq_quality_and_type_fields)" in data.get("migration", "")
