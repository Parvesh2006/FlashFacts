import sys
import time
import signal
import argparse
import logging
from sqlalchemy import text
from app.core.database import SessionLocal, engine, Base, verify_database_head
from app.core.logging import setup_logging, logger
from app.core.config import settings
from app.services.ingestion import IngestionService
from app.main import seed_default_sources

# Graceful termination handling
_shutdown_requested = False


def _signal_handler(signum, frame):
    global _shutdown_requested
    logger.info("Received termination signal (%s). Preparing to stop ingestion worker...", signum)
    _shutdown_requested = True


class IngestionWorkerLock:
    """Session-level PostgreSQL advisory lock ensuring singleton worker execution."""
    LOCK_ID = 5065495285741695300  # 0x464C415348464143 ('FLASHFAC')

    def __init__(self, db_engine):
        self.engine = db_engine
        self._conn = None
        self._locked = False

    def acquire(self) -> bool:
        if self.engine.dialect.name != "postgresql":
            logger.info("Non-PostgreSQL dialect (%s); advisory lock bypassed.", self.engine.dialect.name)
            self._locked = True
            return True

        try:
            self._conn = self.engine.connect()
            result = self._conn.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": self.LOCK_ID}
            ).scalar()

            if result:
                self._locked = True
                logger.info("Acquired PostgreSQL advisory lock for ingestion worker (lock_id=%s).", self.LOCK_ID)
                return True
            else:
                logger.warning(
                    "Another ingestion worker currently holds the PostgreSQL advisory lock (lock_id=%s). "
                    "Exiting to prevent duplicate ingestion runs.",
                    self.LOCK_ID
                )
                if self._conn:
                    self._conn.close()
                    self._conn = None
                return False
        except Exception as e:
            logger.error("Failed to acquire PostgreSQL advisory lock: %s", e)
            if self._conn:
                self._conn.close()
                self._conn = None
            return False

    def is_active(self) -> bool:
        """Check if lock connection is still alive and actively holding the lock."""
        if not self._locked:
            return False
        if self.engine.dialect.name != "postgresql":
            return True
        if not self._conn or getattr(self._conn, "closed", False) is True:
            return False
        try:
            self._conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def release(self):
        if self._locked and self._conn and not self._conn.closed:
            try:
                if self.engine.dialect.name == "postgresql":
                    self._conn.execute(
                        text("SELECT pg_advisory_unlock(:lock_id)"),
                        {"lock_id": self.LOCK_ID}
                    )
                    logger.info("Released PostgreSQL advisory lock (lock_id=%s).", self.LOCK_ID)
            except Exception as e:
                logger.warning("Error releasing advisory lock: %s", e)
            finally:
                self._conn.close()
                self._conn = None
                self._locked = False


def run_once():
    db = SessionLocal()
    try:
        service = IngestionService(db)
        result = service.ingest_all_enabled_sources()
        logger.info("Ingestion Worker Completed Cycle: %s", result)
        return result
    except Exception as e:
        logger.error("Ingestion Worker Failed Cycle: %s", e, exc_info=True)
        return None
    finally:
        db.close()


def run_ingestion_worker(loop: bool = False, interval_minutes: int = 15):
    setup_logging()
    logger.info("Initializing FlashFacts Scheduled Ingestion Worker... (env=%s)", settings.APP_ENV)

    # Register signal handlers for clean container shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    is_prod_or_staging = settings.APP_ENV in ("production", "prod", "staging")

    if is_prod_or_staging:
        # Schema managed via Alembic; verify connection and HEAD revision without create_all
        try:
            current_rev = verify_database_head(engine)
            logger.info("Worker database readiness check passed: revision '%s' matches expected HEAD.", current_rev)
        except Exception as e:
            logger.critical("Worker database setup check failed: %s", e)
            sys.exit(1)
    else:
        # Ensure database schema & default sources are present in dev
        try:
            Base.metadata.create_all(bind=engine)
            seed_default_sources()
        except Exception as e:
            logger.warning("Database setup check in worker: %s", e)

    if not getattr(settings, "INGESTION_ENABLED", True):
        logger.info("INGESTION_ENABLED is set to false. Exiting worker.")
        return

    # Acquire PostgreSQL singleton advisory lock
    worker_lock = IngestionWorkerLock(engine)
    if not worker_lock.acquire():
        logger.warning("Could not acquire worker singleton lock (lock held by another instance). Terminating.")
        return

    try:
        if loop:
            logger.info("Starting continuous ingestion loop every %s minutes...", interval_minutes)
            while not _shutdown_requested:
                if not worker_lock.is_active():
                    logger.critical("Database lock connection lost. Terminating worker to prevent split-brain.")
                    break
                run_once()
                logger.info("Sleeping for %s minutes until next cycle...", interval_minutes)
                total_seconds = interval_minutes * 60
                elapsed = 0
                while elapsed < total_seconds and not _shutdown_requested:
                    time.sleep(1)
                    elapsed += 1
            logger.info("Ingestion worker shut down gracefully.")
        else:
            return run_once()
    finally:
        worker_lock.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FlashFacts Ingestion Worker")
    parser.add_argument("--loop", action="store_true", help="Run continuously in scheduled loop mode")
    parser.add_argument("--interval", type=int, default=getattr(settings, "INGESTION_INTERVAL_MINUTES", 15), help="Ingestion interval in minutes")
    args = parser.parse_args()

    run_ingestion_worker(loop=args.loop, interval_minutes=args.interval)
