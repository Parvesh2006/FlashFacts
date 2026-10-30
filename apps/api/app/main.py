import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.database import engine, Base, SessionLocal, verify_database_head
from app.api.router import api_router
from app.models.source import Source
from app.services.scheduler import ingestion_scheduler


def seed_default_sources(db: Session = None):
    close_db = False
    if db is None:
        try:
            db = SessionLocal()
            close_db = True
        except Exception as e:
            logger.warning(f"Database session creation failed in seed_default_sources: {e}")
            return

    try:
        # Curated permitted sources covering national governance, Tamil Nadu, science, and core domains
        default_sources = [
            # ── National & Tamil Nadu Governance (UPSC & TNPSC Gold Standard) ──
            {
                "name": "The Hindu - Tamil Nadu",
                "url": "https://www.thehindu.com/news/national/tamil-nadu/",
                "feed_url": "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss",
                "source_type": "rss",
                "domain": "Governance",
                "reliability_score": 0.99,
                "enabled": True,
            },
            {
                "name": "The Hindu - National",
                "url": "https://www.thehindu.com/news/national/",
                "feed_url": "https://www.thehindu.com/news/national/feeder/default.rss",
                "source_type": "rss",
                "domain": "National",
                "reliability_score": 0.99,
                "enabled": True,
            },
            {
                "name": "PIB India National",
                "url": "https://pib.gov.in",
                "feed_url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1",
                "source_type": "rss",
                "domain": "Governance",
                "reliability_score": 1.0,
                "enabled": True,
            },
            {
                "name": "PIB Tamil Nadu & National (Tamil)",
                "url": "https://pib.gov.in",
                "feed_url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=2",
                "source_type": "rss",
                "domain": "Governance",
                "reliability_score": 1.0,
                "enabled": True,
            },
            {
                "name": "BBC News Tamil",
                "url": "https://www.bbc.com/tamil",
                "feed_url": "https://feeds.bbci.co.uk/tamil/rss.xml",
                "source_type": "rss",
                "domain": "International",
                "reliability_score": 0.98,
                "enabled": True,
            },
            {
                "name": "The Hindu - Science & Space",
                "url": "https://www.thehindu.com/sci-tech/science/",
                "feed_url": "https://www.thehindu.com/sci-tech/science/feeder/default.rss",
                "source_type": "rss",
                "domain": "Science",
                "reliability_score": 0.99,
                "enabled": True,
            },
            {
                "name": "The Hindu - Business & Economy",
                "url": "https://www.thehindu.com/business/",
                "feed_url": "https://www.thehindu.com/business/feeder/default.rss",
                "source_type": "rss",
                "domain": "Economy",
                "reliability_score": 0.99,
                "enabled": True,
            },
            # ── Established Core Feeds ──
            {
                "name": "BBC Technology",
                "url": "https://www.bbc.com/news/technology",
                "feed_url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
                "source_type": "rss",
                "domain": "Technology",
                "reliability_score": 0.98,
                "enabled": True,
            },
            {
                "name": "BBC Business",
                "url": "https://www.bbc.com/news/business",
                "feed_url": "https://feeds.bbci.co.uk/news/business/rss.xml",
                "source_type": "rss",
                "domain": "Economy",
                "reliability_score": 0.98,
                "enabled": True,
            },
            {
                "name": "BBC World News",
                "url": "https://www.bbc.com/news",
                "feed_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
                "source_type": "rss",
                "domain": "International",
                "reliability_score": 0.98,
                "enabled": True,
            },
            {
                "name": "BBC India",
                "url": "https://www.bbc.com/news/world/asia/india",
                "feed_url": "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
                "source_type": "rss",
                "domain": "International",
                "reliability_score": 0.98,
                "enabled": True,
            },
            {
                "name": "NASA Breaking News",
                "url": "https://www.nasa.gov/news/",
                "feed_url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
                "source_type": "rss",
                "domain": "Science",
                "reliability_score": 0.99,
                "enabled": True,
            },
            {
                "name": "World Health Organization",
                "url": "https://www.who.int",
                "feed_url": "https://www.who.int/rss-feeds/news-english.xml",
                "source_type": "rss",
                "domain": "Medical",
                "reliability_score": 0.99,
                "enabled": True,
            },
            {
                "name": "BBC Sport",
                "url": "https://www.bbc.com/sport",
                "feed_url": "https://feeds.bbci.co.uk/sport/rss.xml",
                "source_type": "rss",
                "domain": "Sports",
                "reliability_score": 0.98,
                "enabled": True,
            }
        ]
        added_count = 0
        for src_data in default_sources:
            existing = db.query(Source).filter(Source.feed_url == src_data["feed_url"]).first()
            if not existing:
                db.add(Source(**src_data))
                added_count += 1
        if added_count > 0:
            db.commit()
            logger.info(f"{added_count} new permitted RSS sources successfully seeded into database.")
    except Exception as e:
        logger.warning(f"Could not seed default sources: {e}")
    finally:
        if close_db and db:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting FlashFacts API Server... (env=%s)", settings.APP_ENV)

    is_prod_or_staging = settings.APP_ENV in ("production", "prod", "staging")

    if is_prod_or_staging:
        # In production and staging, schema must be initialized via 'alembic upgrade head'.
        # Base.metadata.create_all() is strictly bypassed to guarantee migration integrity.
        # Verify that the database is at the actual Alembic HEAD revision.
        logger.info("Verifying production/staging database readiness and migration status...")
        try:
            current_rev = verify_database_head(engine)
            logger.info("Database migration check passed: revision '%s' matches expected HEAD.", current_rev)
            seed_default_sources()
        except Exception as e:
            logger.critical("Database readiness check failed in %s: %s", settings.APP_ENV, e)
            raise e
    elif settings.APP_ENV != "testing":
        # In local development, create_all maintains rapid onboarding
        try:
            Base.metadata.create_all(bind=engine)
            seed_default_sources()
        except Exception as e:
            logger.warning(f"Database initialization during lifespan skipped or failed: {e}")

    scheduler_task = None
    stop_event = asyncio.Event()
    if settings.INGESTION_ENABLED and settings.APP_ENV != "testing":
        logger.info("Ingestion scheduler is enabled. Starting background ingestion loop...")
        scheduler_task = asyncio.create_task(ingestion_scheduler(stop_event))
    else:
        logger.info(
            "Ingestion scheduler is disabled on this instance (INGESTION_ENABLED=%s).",
            settings.INGESTION_ENABLED
        )

    yield

    if scheduler_task:
        stop_event.set()
        await scheduler_task
    logger.info("Shutting down FlashFacts API Server...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
