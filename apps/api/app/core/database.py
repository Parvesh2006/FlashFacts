from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import settings

engine_kwargs = {}
database_url = settings.DATABASE_URL

if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Liveness pre-ping prevents stale connection drops in hosted PostgreSQL
    engine_kwargs["pool_pre_ping"] = True

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_expected_alembic_head() -> str:
    """Read the latest expected revision head from the project's Alembic migrations."""
    base_dir = Path(__file__).resolve().parent.parent.parent  # apps/api
    ini_path = base_dir / "alembic.ini"
    alembic_dir = base_dir / "alembic"

    config = Config(str(ini_path))
    config.set_main_option("script_location", str(alembic_dir))
    script = ScriptDirectory.from_config(config)
    head = script.get_current_head()
    return head


def verify_database_head(db_engine) -> str:
    """
    Verifies that the database has been migrated to the expected Alembic HEAD revision.
    Raises RuntimeError if alembic_version table is missing, empty, or outdated.
    Returns the verified revision string.
    """
    with db_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        inspector = inspect(db_engine)
        if not inspector.has_table("alembic_version"):
            raise RuntimeError(
                "Database schema not initialized (table 'alembic_version' is missing). "
                "In production/staging, you must run 'alembic upgrade head' before starting the application."
            )
        row = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
        current_rev = row[0] if row else None
        if not current_rev:
            raise RuntimeError(
                "Database schema missing migration revision record in 'alembic_version'. "
                "In production/staging, you must run 'alembic upgrade head' before starting the application."
            )

        expected_head = get_expected_alembic_head()
        if current_rev != expected_head:
            raise RuntimeError(
                f"Database schema is outdated (current revision: '{current_rev}', expected HEAD: '{expected_head}'). "
                "In production/staging, you must run 'alembic upgrade head' before starting the application."
            )
        return current_rev
