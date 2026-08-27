import os
import sys
from pathlib import Path

# Set test DB location (file in workspace)
sqlite_path = Path(os.getcwd()) / "flashfacts_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{sqlite_path.as_posix()}"
os.environ["APP_ENV"] = "testing"

# Ensure app package is importable
sys.path.insert(0, str(Path(os.getcwd()) / "apps" / "api"))

from app.core.database import engine, Base, SessionLocal
from app.main import seed_default_sources
from app.workers.ingestion_worker import run_once

# Create schema and seed sources
Base.metadata.create_all(bind=engine)
seed_default_sources()

# Run one ingestion cycle
result = run_once()
print("INGESTION RESULT:", result)
