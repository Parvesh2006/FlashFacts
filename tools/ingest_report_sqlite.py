import sys
from pathlib import Path
import os

# Use sqlite test DB created by the ingestion run
sqlite_path = Path.cwd() / "flashfacts_test.db"
if not sqlite_path.exists():
    print("No sqlite ingest DB found at", sqlite_path)
    sys.exit(1)

# Ensure app reads the sqlite DB rather than default Postgres
os.environ["DATABASE_URL"] = f"sqlite:///{sqlite_path.as_posix()}"
os.environ["APP_ENV"] = "testing"

sys.path.insert(0, str(Path.cwd() / "apps" / "api"))
from app.core.database import SessionLocal
from app.models.source import Source
from app.models.document import Document
from app.models.event import Event
from sqlalchemy import func

# Use same sqlite file as ingestion run
sqlite_path = Path.cwd() / "flashfacts_test.db"
if not sqlite_path.exists():
    print("No sqlite ingest DB found at", sqlite_path)
    sys.exit(1)

session = SessionLocal()
try:
    sources = session.query(Source).all()
    report = []
    for s in sources:
        docs = session.query(func.count(Document.id)).filter(Document.source_id == s.id).scalar()
        # events that have event_sources pointing to documents from this source
        # fallback: count events where event.source_id equals s.id
        events = session.query(func.count(Event.id)).filter(Event.source_id == s.id).scalar()
        report.append((s.id, s.name, s.feed_url, docs or 0, events or 0, s.last_ingested_at))

    for r in report:
        print(r)
finally:
    session.close()
