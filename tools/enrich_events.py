#!/usr/bin/env python3
"""Enrich eligible FlashFacts events using the configured AI provider."""
import argparse
import os
import sys
from pathlib import Path

apps_api_path = Path(__file__).parent.parent / "apps" / "api"
sys.path.insert(0, str(apps_api_path))
os.chdir(str(apps_api_path))

from app.core.database import SessionLocal
from app.services.enrichment import EventEnrichmentService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        result = EventEnrichmentService(db).enrich_batch(args.limit, args.force)
        print("========== FLASHFACTS EVENT ENRICHMENT ==========")
        for key, value in result.items():
            print(f"{key.replace('_', ' ').title():24}: {value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()