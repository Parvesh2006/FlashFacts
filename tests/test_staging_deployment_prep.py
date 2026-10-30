import asyncio
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import Settings, DEV_DEFAULT_CORS
from app.core.database import verify_database_head, get_expected_alembic_head
from app.workers.ingestion_worker import IngestionWorkerLock


# =========================================================================
# 1. Strict CORS Validation Tests (Production and Staging)
# =========================================================================

VALID_SECRET = "a_super_strong_cryptographic_random_key_64_bytes_for_staging_env"


def test_staging_env_enforces_secret_key():
    """Staging environment must enforce the same strict SECRET_KEY validation as production."""
    with pytest.raises(ValueError, match="SECRET_KEY is missing"):
        Settings(
            APP_ENV="staging",
            SECRET_KEY="",
            CORS_ORIGINS=["https://staging.flashfacts.app"],
        )

    with pytest.raises(ValueError, match="Insecure or default SECRET_KEY detected"):
        Settings(
            APP_ENV="staging",
            SECRET_KEY="flashfacts_secure_exam_portal_key_2026",
            CORS_ORIGINS=["https://staging.flashfacts.app"],
        )

    with pytest.raises(ValueError, match="Insecure or default SECRET_KEY detected"):
        Settings(
            APP_ENV="staging",
            SECRET_KEY="too_short_secret",
            CORS_ORIGINS=["https://staging.flashfacts.app"],
        )


def test_cors_rejects_wildcard_in_production_and_staging():
    """Production and staging must reject wildcard '*' origins."""
    with pytest.raises(ValueError, match="Wildcard CORS origin"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=["*"],
        )

    with pytest.raises(ValueError, match="Wildcard CORS origin"):
        Settings(
            APP_ENV="staging",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS="*",
        )


def test_cors_rejects_empty_and_whitespace_only():
    """Production and staging must reject empty lists, whitespace-only, or empty origin entries."""
    # Empty list
    with pytest.raises(ValueError, match="CORS_ORIGINS cannot be empty"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=[],
        )

    # Whitespace-only string
    with pytest.raises(ValueError, match="CORS_ORIGINS cannot be empty"):
        Settings(
            APP_ENV="staging",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS="   ",
        )

    # Whitespace entry in list
    with pytest.raises(ValueError, match="Empty or whitespace-only CORS origin"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=["https://staging.flashfacts.app", "   "],
        )

    # Comma-separated with trailing comma (empty entry)
    with pytest.raises(ValueError, match="Empty or whitespace-only CORS origin"):
        Settings(
            APP_ENV="staging",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS="https://staging.flashfacts.app, ",
        )


def test_cors_rejects_ftp_and_non_http_schemes():
    """CORS origins must reject non-http/https schemes such as ftp:// or file://."""
    with pytest.raises(ValueError, match="Origin must start with an absolute 'http://' or 'https://' scheme"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=["ftp://example.com"],
        )

    with pytest.raises(ValueError, match="Origin must start with an absolute 'http://' or 'https://' scheme"):
        Settings(
            APP_ENV="staging",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS="javascript:void(0)",
        )


def test_cors_rejects_malformed_urls_and_missing_host():
    """CORS origins must reject raw domains without scheme or missing hostnames."""
    with pytest.raises(ValueError, match="Origin must start with an absolute 'http://' or 'https://' scheme"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=["staging.flashfacts.app"],
        )

    with pytest.raises(ValueError, match="Missing valid hostname"):
        Settings(
            APP_ENV="staging",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=["https://"],
        )


def test_cors_rejects_paths_query_strings_fragments_and_credentials():
    """CORS origins must be origin-only and reject paths, queries, fragments, and credentials."""
    # Path
    with pytest.raises(ValueError, match="must not include a path component"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=["https://staging.flashfacts.app/api"],
        )

    with pytest.raises(ValueError, match="must not include a path component"):
        Settings(
            APP_ENV="staging",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=["https://staging.flashfacts.app/"],
        )

    # Query string
    with pytest.raises(ValueError, match="must not include query parameters"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=["https://staging.flashfacts.app?ref=web"],
        )

    # Fragment
    with pytest.raises(ValueError, match="must not include a fragment identifier"):
        Settings(
            APP_ENV="staging",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=["https://staging.flashfacts.app#home"],
        )

    # Credentials
    with pytest.raises(ValueError, match="User credentials in origin are not permitted"):
        Settings(
            APP_ENV="production",
            SECRET_KEY=VALID_SECRET,
            CORS_ORIGINS=["https://user:pass@staging.flashfacts.app"],
        )


def test_cors_accepts_valid_https_and_localhost_origins():
    """Valid absolute HTTPS origins and localhost with ports are accepted."""
    cfg = Settings(
        APP_ENV="staging",
        SECRET_KEY=VALID_SECRET,
        CORS_ORIGINS="https://staging.flashfacts.app, http://localhost:3000, https://flashfacts-staging.vercel.app",
    )
    assert len(cfg.CORS_ORIGINS) == 3
    assert "https://staging.flashfacts.app" in cfg.CORS_ORIGINS
    assert "http://localhost:3000" in cfg.CORS_ORIGINS
    assert "https://flashfacts-staging.vercel.app" in cfg.CORS_ORIGINS


def test_cors_development_workflow_preserves_defaults():
    """Development environment safely falls back to DEV_DEFAULT_CORS when empty or wildcard."""
    cfg_wildcard = Settings(
        APP_ENV="development",
        SECRET_KEY="",
        CORS_ORIGINS=["*"],
    )
    assert cfg_wildcard.CORS_ORIGINS == list(DEV_DEFAULT_CORS)

    cfg_explicit = Settings(
        APP_ENV="development",
        SECRET_KEY="",
        CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"],
    )
    assert cfg_explicit.CORS_ORIGINS == ["http://localhost:3000", "http://127.0.0.1:3000"]


# =========================================================================
# 2. Database Alembic HEAD Verification Tests
# =========================================================================

def test_verify_database_head_matches_expected_head():
    """When DB version matches the expected head, verification succeeds and returns the head revision."""
    expected_head = get_expected_alembic_head()
    assert expected_head is not None
    assert len(expected_head) > 0

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    mock_inspector = MagicMock()
    mock_inspector.has_table.return_value = True

    mock_conn.execute.return_value.fetchone.return_value = (expected_head,)

    with patch("app.core.database.inspect", return_value=mock_inspector):
        verified_rev = verify_database_head(mock_engine)
        assert verified_rev == expected_head


def test_verify_database_head_fails_if_table_missing():
    """If alembic_version table is missing, verify_database_head raises RuntimeError."""
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    mock_inspector = MagicMock()
    mock_inspector.has_table.return_value = False

    with patch("app.core.database.inspect", return_value=mock_inspector):
        with pytest.raises(RuntimeError, match=r"table 'alembic_version' is missing"):
            verify_database_head(mock_engine)


def test_verify_database_head_fails_if_revision_record_missing():
    """If alembic_version table exists but has no rows, raises RuntimeError."""
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    mock_inspector = MagicMock()
    mock_inspector.has_table.return_value = True

    # No rows returned from SELECT version_num FROM alembic_version
    mock_conn.execute.return_value.fetchone.return_value = None

    with patch("app.core.database.inspect", return_value=mock_inspector):
        with pytest.raises(RuntimeError, match="missing migration revision record"):
            verify_database_head(mock_engine)


def test_verify_database_head_fails_if_outdated():
    """If the current DB revision is older than expected HEAD, raises RuntimeError."""
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    mock_inspector = MagicMock()
    mock_inspector.has_table.return_value = True

    # Outdated revision
    mock_conn.execute.return_value.fetchone.return_value = ("001_initial_schema",)

    with patch("app.core.database.inspect", return_value=mock_inspector):
        with pytest.raises(RuntimeError, match="Database schema is outdated .* expected HEAD"):
            verify_database_head(mock_engine)


def test_lifespan_staging_fails_on_outdated_database():
    """Lifespan in staging/prod aborts startup if database revision is outdated."""
    from app.main import lifespan

    mock_app = FastAPI()
    with patch("app.main.settings") as mock_settings, \
         patch("app.main.verify_database_head") as mock_verify:
        mock_settings.APP_ENV = "staging"
        mock_settings.INGESTION_ENABLED = False
        mock_verify.side_effect = RuntimeError("Database schema is outdated")

        with pytest.raises(RuntimeError, match="Database schema is outdated"):
            async def run():
                async with lifespan(mock_app):
                    pass
            asyncio.run(run())


def test_alembic_all_revision_ids_fit_version_column():
    """Verify all migration revision IDs in the project fit within VARCHAR(255) and document >32 char IDs."""
    import re
    from pathlib import Path

    versions_dir = Path(__file__).resolve().parent.parent / "apps" / "api" / "alembic" / "versions"
    assert versions_dir.exists()

    revisions = []
    for py_file in versions_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        match = re.search(r"revision(?:\s*:\s*str)?\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            rev_id = match.group(1)
            revisions.append(rev_id)
            assert len(rev_id) <= 255, f"Revision {rev_id} exceeds VARCHAR(255)"

    assert len(revisions) >= 14
    # 002_event_enrichment_and_entities has 33 chars and caused Render DataError with VARCHAR(32)
    long_revisions = [r for r in revisions if len(r) > 32]
    assert "002_event_enrichment_and_entities" in long_revisions
    assert len("002_event_enrichment_and_entities") == 33


def test_alembic_version_table_impl_generates_255_length():
    """Verify that alembic DefaultImpl.version_table_impl generates VARCHAR(255) for alembic_version."""
    import alembic.ddl.impl
    from alembic import util
    from sqlalchemy import String
    from pathlib import Path

    apps_api = str(Path(__file__).resolve().parent.parent / "apps" / "api")
    # Load env.py to ensure the hook is installed
    util.load_python_file(str(Path(apps_api) / "alembic"), "env.py")

    mock_dialect = MagicMock()
    mock_dialect.name = "postgresql"
    impl_cls = alembic.ddl.impl.DefaultImpl.get_by_dialect(mock_dialect)
    impl = impl_cls(mock_dialect, MagicMock(), False, False, None, {})
    vt = impl.version_table_impl(
        version_table="alembic_version",
        version_table_schema=None,
        version_table_pk=True,
    )
    version_col = vt.c.version_num
    assert isinstance(version_col.type, String)
    assert version_col.type.length == 255


def test_alembic_ensure_version_column_length_widens_existing_column():
    """Verify _ensure_version_column_length alters VARCHAR(32) to VARCHAR(255) on PostgreSQL."""
    from sqlalchemy import String
    from alembic import util
    from pathlib import Path

    apps_api = str(Path(__file__).resolve().parent.parent / "apps" / "api")
    env_module = util.load_python_file(str(Path(apps_api) / "alembic"), "env.py")

    mock_conn = MagicMock()
    mock_conn.dialect.name = "postgresql"

    mock_inspector = MagicMock()
    mock_inspector.has_table.return_value = True
    mock_inspector.get_columns.return_value = [
        {"name": "version_num", "type": String(32)}
    ]

    with patch.object(env_module, "inspect", return_value=mock_inspector):
        env_module._ensure_version_column_length(mock_conn, version_table="alembic_version")
        # Check that ALTER TABLE was executed
        mock_conn.execute.assert_called_once()
        stmt = str(mock_conn.execute.call_args[0][0])
        assert 'ALTER TABLE "alembic_version" ALTER COLUMN "version_num" TYPE VARCHAR(255)' in stmt


# =========================================================================
# 3. Worker Singleton Advisory Lock Tests
# =========================================================================

def test_ingestion_worker_lock_acquisition_and_release():
    """Tests advisory lock acquisition and release on database engine."""
    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_engine.connect.return_value = mock_conn

    # First attempt: lock granted
    mock_conn.execute.return_value.scalar.return_value = True

    lock = IngestionWorkerLock(mock_engine)
    acquired = lock.acquire()
    assert acquired is True
    assert lock.is_active() is True

    # Release lock
    lock.release()
    assert lock.is_active() is False  # Lock is no longer active
    calls = [str(c[0][0]) for c in mock_conn.execute.call_args_list]
    assert any("pg_advisory_unlock" in c for c in calls)


def test_ingestion_worker_lock_contention():
    """When another instance holds the advisory lock, acquire returns False."""
    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_conn = MagicMock()
    mock_engine.connect.return_value = mock_conn

    # Another worker holds lock -> pg_try_advisory_lock returns False
    mock_conn.execute.return_value.scalar.return_value = False

    lock = IngestionWorkerLock(mock_engine)
    acquired = lock.acquire()
    assert acquired is False


def test_ingestion_worker_lock_detects_connection_loss():
    """If lock database connection is closed or raises an error, is_active returns False."""
    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_engine.connect.return_value = mock_conn
    mock_conn.execute.return_value.scalar.return_value = True

    lock = IngestionWorkerLock(mock_engine)
    assert lock.acquire() is True

    # Simulate connection closed
    mock_conn.closed = True
    assert lock.is_active() is False

    # Simulate connection ping failure
    mock_conn.closed = False
    mock_conn.execute.side_effect = Exception("DB connection reset by peer")
    assert lock.is_active() is False


# =========================================================================
# 4. Readiness and Optional Cache Tests
# =========================================================================

def test_readiness_endpoint_with_redis_fallback(client: TestClient):
    """The /ready endpoint must report database: connected and redis status without failing if redis is absent."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "redis" in data
    assert data["redis"] in ("connected", "unavailable (operating without cache)")
