#!/usr/bin/env python3
"""
End-to-End Ingestion Test Script

This script performs a complete ingestion cycle using the configured sources
and captures all metrics for research and validation.

This is NOT a production script - it's for testing and validation.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
import time

# Add apps/api to path
apps_api_path = Path(__file__).parent.parent / "apps" / "api"
sys.path.insert(0, str(apps_api_path))
os.chdir(str(apps_api_path))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.source import Source
from app.models.ingestion_run import IngestionRun
from app.repositories.ingestion_run_repository import IngestionRunRepository
from app.services.ingestion import IngestionService


def main():
    """Run a complete ingestion cycle."""
    print("\n" + "=" * 70)
    print("FLASHFACTS END-TO-END INGESTION TEST")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Check enabled sources
        sources = db.query(Source).filter(Source.enabled == True).all()
        print(f"\nFound {len(sources)} enabled sources:")
        for source in sources:
            print(f"  - {source.name}")
        
        if not sources:
            print("\nNo enabled sources found. Please enable sources first.")
            return
        
        # Run ingestion
        print("\n" + "-" * 70)
        print("Starting ingestion run...")
        print("-" * 70)
        
        start_time = time.time()
        ingestion_service = IngestionService(db)
        result = ingestion_service.ingest_all_enabled_sources()
        elapsed = time.time() - start_time
        
        print(f"\nIngestion completed in {elapsed:.2f} seconds")
        print(f"\nResults:")
        print(f"  Run ID: {result['ingestion_run_id']}")
        print(f"  Status: {result['status'].upper()}")
        print(f"  Sources attempted: {result['sources_attempted']}")
        print(f"  Sources succeeded: {result['sources_succeeded']}")
        print(f"  Sources failed: {result['sources_failed']}")
        print(f"  Documents discovered: {result['documents_discovered']}")
        print(f"  Documents accepted: {result['documents_ingested']}")
        print(f"  Documents duplicate: {result['documents_duplicate']}")
        print(f"  Events created: {result['events_created']}")
        print(f"  Events deduplicated: {result['events_deduplicated']}")
        print(f"  Processing time: {result['processing_time_ms']:.2f}ms")
        print(f"  Errors: {result['error_count']}")
        
        # Save results to JSON
        output_file = Path(__file__).parent / "data" / "experiments" / "ingestion_run_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            # Make it JSON serializable
            result['completed_at'] = datetime.now().isoformat()
            json.dump(result, f, indent=2)
        
        print(f"\nResults saved to {output_file}")
        
        return result
        
    except Exception as e:
        print(f"\nError during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
