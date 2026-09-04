import asyncio
import logging

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.ingestion import IngestionService

logger = logging.getLogger("app")


async def ingestion_scheduler(stop_event: asyncio.Event) -> None:
    """Run ingestion periodically until the application requests shutdown."""
    interval_seconds = max(1, settings.INGESTION_INTERVAL_MINUTES * 60)
    logger.info("Ingestion scheduler started: interval_minutes=%s", settings.INGESTION_INTERVAL_MINUTES)
    try:
        while not stop_event.is_set():
            try:
                db = SessionLocal()
                try:
                    await asyncio.to_thread(IngestionService(db).ingest_all_enabled_sources)
                finally:
                    db.close()
            except Exception:
                logger.exception("Scheduled ingestion run failed")

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                continue
    finally:
        logger.info("Ingestion scheduler stopped")
