#!/usr/bin/env python3
"""
Initialize the database with schema and seed data.
"""

import sys
import os
from pathlib import Path

# Add apps/api to path
apps_api_path = Path(__file__).parent.parent / "apps" / "api"
sys.path.insert(0, str(apps_api_path))
os.chdir(str(apps_api_path))

from app.core.database import engine, Base, SessionLocal
from app.models import *
from app.models.source import Source

def init_db():
    """Create all tables and seed default sources."""
    print("Creating database schema...")
    Base.metadata.create_all(bind=engine)
    print("✓ Schema created")

    # Seed sources
    db = SessionLocal()
    try:
        existing = db.query(Source).count()
        if existing > 0:
            print(f"✓ Database already has {existing} sources")
            return

        print("\nSeeding default sources...")
        sources = [
            {
                "name": "TechCrunch",
                "url": "https://techcrunch.com",
                "feed_url": "https://techcrunch.com/feed/",
                "source_type": "rss",
                "domain": "Technology",
                "reliability_score": 0.95,
                "enabled": True,
            },
            {
                "name": "MIT Technology Review",
                "url": "https://www.technologyreview.com",
                "feed_url": "https://www.technologyreview.com/feed/",
                "source_type": "rss",
                "domain": "AI",
                "reliability_score": 0.97,
                "enabled": True,
            },
            {
                "name": "BBC World News",
                "url": "https://www.bbc.com/news",
                "feed_url": "http://feeds.bbci.co.uk/news/world/rss.xml",
                "source_type": "rss",
                "domain": "International",
                "reliability_score": 0.98,
                "enabled": True,
            },
        ]

        for source_data in sources:
            source = Source(**source_data)
            db.add(source)
            print(f"  + {source_data['name']}")

        db.commit()
        print("\n✓ Sources seeded successfully")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
