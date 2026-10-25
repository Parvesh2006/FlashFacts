import asyncio
import os
import sys

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.source import Source

SOURCES = [
    # PIB / Central Govt
    {"name": "PIB National", "url": "https://pib.gov.in", "feed_url": "https://pib.gov.in/rss/National.xml", "source_type": "rss", "domain": "National", "reliability_score": 1.0, "enabled": True},
    {"name": "PIB Tamil Nadu", "url": "https://pib.gov.in", "feed_url": "https://pib.gov.in/rss/TamilNadu.xml", "source_type": "rss", "domain": "Tamil Nadu", "reliability_score": 1.0, "enabled": True},
    # RBI / Finance
    {"name": "RBI Press Releases", "url": "https://www.rbi.org.in", "feed_url": "https://www.rbi.org.in/rss/PressReleases.xml", "source_type": "rss", "domain": "Economy", "reliability_score": 1.0, "enabled": True},
    {"name": "Ministry of Finance", "url": "https://finmin.nic.in", "feed_url": "https://finmin.nic.in/rss/news.xml", "source_type": "rss", "domain": "Economy", "reliability_score": 1.0, "enabled": True},
    # Science & Tech
    {"name": "ISRO Updates", "url": "https://www.isro.gov.in", "feed_url": "https://www.isro.gov.in/rss.xml", "source_type": "rss", "domain": "Science & Technology", "reliability_score": 1.0, "enabled": True},
    {"name": "IMD Weather", "url": "https://mausam.imd.gov.in", "feed_url": "https://mausam.imd.gov.in/rss.xml", "source_type": "rss", "domain": "Geography", "reliability_score": 1.0, "enabled": True},
    {"name": "NASA", "url": "https://www.nasa.gov", "feed_url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "source_type": "rss", "domain": "Science & Technology", "reliability_score": 1.0, "enabled": True},
    {"name": "MoEFCC", "url": "https://moef.gov.in", "feed_url": "https://moef.gov.in/rss.xml", "source_type": "rss", "domain": "Environment", "reliability_score": 1.0, "enabled": True},
    # Tamil Nadu / Govt
    {"name": "Tamil Nadu Govt", "url": "https://www.tn.gov.in", "feed_url": "https://www.tn.gov.in/rss.xml", "source_type": "rss", "domain": "Tamil Nadu", "reliability_score": 1.0, "enabled": True},
    {"name": "TNPSC Notifications", "url": "https://tnpsc.gov.in", "feed_url": "https://tnpsc.gov.in/rss.xml", "source_type": "rss", "domain": "Education", "reliability_score": 1.0, "enabled": True},
    # International
    {"name": "UN News", "url": "https://news.un.org", "feed_url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml", "source_type": "rss", "domain": "International", "reliability_score": 1.0, "enabled": True},
    {"name": "WHO News", "url": "https://www.who.int", "feed_url": "https://www.who.int/rss/news.xml", "source_type": "rss", "domain": "Science & Technology", "reliability_score": 1.0, "enabled": True},
    {"name": "World Bank", "url": "https://www.worldbank.org", "feed_url": "https://www.worldbank.org/en/news/rss", "source_type": "rss", "domain": "Economy", "reliability_score": 1.0, "enabled": True},
    {"name": "UNESCO", "url": "https://www.unesco.org", "feed_url": "https://www.unesco.org/en/rss", "source_type": "rss", "domain": "International", "reliability_score": 1.0, "enabled": True},
    # National News
    {"name": "The Hindu National", "url": "https://www.thehindu.com", "feed_url": "https://www.thehindu.com/news/national/feeder/default.rss", "source_type": "rss", "domain": "National", "reliability_score": 0.9, "enabled": True},
    {"name": "The Hindu Tamil Nadu", "url": "https://www.thehindu.com", "feed_url": "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss", "source_type": "rss", "domain": "Tamil Nadu", "reliability_score": 0.9, "enabled": True},
    {"name": "The Hindu Science", "url": "https://www.thehindu.com", "feed_url": "https://www.thehindu.com/sci-tech/science/feeder/default.rss", "source_type": "rss", "domain": "Science & Technology", "reliability_score": 0.9, "enabled": True},
    {"name": "Indian Express National", "url": "https://indianexpress.com", "feed_url": "https://indianexpress.com/section/india/feed/", "source_type": "rss", "domain": "National", "reliability_score": 0.9, "enabled": True},
    {"name": "Times of India India", "url": "https://timesofindia.indiatimes.com", "feed_url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms", "source_type": "rss", "domain": "National", "reliability_score": 0.8, "enabled": True},
    # Tamil News
    {"name": "Dinamani TN", "url": "https://www.dinamani.com", "feed_url": "https://www.dinamani.com/tamilnadu/rss", "source_type": "rss", "domain": "Tamil Nadu", "reliability_score": 0.9, "enabled": True},
    {"name": "Hindu Tamil Thisai", "url": "https://www.hindutamil.in", "feed_url": "https://www.hindutamil.in/rss/tamilnadu", "source_type": "rss", "domain": "Tamil Nadu", "reliability_score": 0.9, "enabled": True},
    {"name": "Puthiya Thalaimurai", "url": "https://www.puthiyathalaimurai.com", "feed_url": "https://www.puthiyathalaimurai.com/rss/tamilnadu", "source_type": "rss", "domain": "Tamil Nadu", "reliability_score": 0.8, "enabled": True},
    {"name": "Polimer News", "url": "https://www.polimernews.com", "feed_url": "https://www.polimernews.com/rss", "source_type": "rss", "domain": "Tamil Nadu", "reliability_score": 0.8, "enabled": True},
    {"name": "News18 Tamil", "url": "https://tamil.news18.com", "feed_url": "https://tamil.news18.com/rss", "source_type": "rss", "domain": "Tamil Nadu", "reliability_score": 0.8, "enabled": True},
    {"name": "BBC Tamil", "url": "https://www.bbc.com/tamil", "feed_url": "https://www.bbc.com/tamil/index.xml", "source_type": "rss", "domain": "Tamil Nadu", "reliability_score": 0.95, "enabled": True},
    {"name": "Dinakaran", "url": "https://www.dinakaran.com", "feed_url": "https://www.dinakaran.com/rss", "source_type": "rss", "domain": "Tamil Nadu", "reliability_score": 0.8, "enabled": True}
]

def main():
    db = SessionLocal()
    try:
        added = 0
        for src_data in SOURCES:
            existing = db.execute(select(Source).where(Source.feed_url == src_data["feed_url"])).scalar_one_or_none()
            if not existing:
                src = Source(**src_data)
                db.add(src)
                added += 1
            else:
                for k, v in src_data.items():
                    setattr(existing, k, v)
        db.commit()
        print(f"Successfully added/updated {added} sources. Total in db: {db.execute(select(Source)).scalar()}")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
