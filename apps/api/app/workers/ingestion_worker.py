import sys
import time
import argparse
import logging
from app.core.database import SessionLocal, engine, Base
from app.core.logging import setup_logging, logger
from app.core.config import settings
from app.services.ingestion import IngestionService
from app.main import seed_default_sources


def run_once():
    db = SessionLocal()
    try:
        service = IngestionService(db)
        result = service.ingest_all_enabled_sources()
        logger.info(f"Ingestion Worker Completed Cycle: {result}")
        return result
    except Exception as e:
        logger.error(f"Ingestion Worker Failed Cycle: {e}", exc_info=True)
        return None
    finally:
        db.close()


def run_ingestion_worker(loop: bool = False, interval_minutes: int = 15):
    setup_logging()
    logger.info("Initializing FlashFacts Scheduled Ingestion Worker...")
    
    # Ensure database schema & default sources are present
    try:
        Base.metadata.create_all(bind=engine)
        seed_default_sources()
    except Exception as e:
        logger.warning(f"Database setup check in worker: {e}")

    if not getattr(settings, "INGESTION_ENABLED", True):
        logger.info("INGESTION_ENABLED is set to false. Exiting worker.")
        return

    if loop:
        logger.info(f"Starting continuous ingestion loop every {interval_minutes} minutes...")
        while True:
            run_once()
            logger.info(f"Sleeping for {interval_minutes} minutes until next cycle...")
            time.sleep(interval_minutes * 60)
    else:
        return run_once()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FlashFacts Ingestion Worker")
    parser.add_argument("--loop", action="store_true", help="Run continuously in scheduled loop mode")
    parser.add_argument("--interval", type=int, default=getattr(settings, "INGESTION_INTERVAL_MINUTES", 15), help="Ingestion interval in minutes")
    args = parser.parse_args()

    run_ingestion_worker(loop=args.loop, interval_minutes=args.interval)
