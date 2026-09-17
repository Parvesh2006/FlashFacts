import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.database import engine, Base, SessionLocal
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
        if db.query(Source).count() == 0:
            # Curated MVP permitted sources covering key domains
            default_sources = [
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
            for src_data in default_sources:
                db.add(Source(**src_data))
            db.commit()
            logger.info("Default permitted RSS sources successfully seeded into database.")
    except Exception as e:
        logger.warning(f"Could not seed default sources: {e}")
    finally:
        if close_db and db:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting FlashFacts API Server...")
    try:
        Base.metadata.create_all(bind=engine)
        seed_default_sources()
    except Exception as e:
        logger.warning(f"Database initialization during lifespan skipped or failed: {e}")
    scheduler_task = None
    stop_event = asyncio.Event()
    if settings.INGESTION_ENABLED and settings.APP_ENV != "testing":
        scheduler_task = asyncio.create_task(ingestion_scheduler(stop_event))
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
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
