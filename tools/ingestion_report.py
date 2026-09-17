#!/usr/bin/env python3
"""
FlashFacts Ingestion Report Tool

Generates a detailed ingestion report from the database.
Reads actual measurements from IngestionRun and SourceIngestionMetric tables.

Usage:
    python tools/ingestion_report.py [--run-id RUN_ID] [--latest]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add apps/api to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ingestion_run import IngestionRun
from app.models.source_ingestion_metric import SourceIngestionMetric
from app.repositories.ingestion_run_repository import IngestionRunRepository
from app.repositories.source_ingestion_metric_repository import SourceIngestionMetricRepository
from app.repositories.source_repository import SourceRepository


def format_duration_ms(ms: float) -> str:
    """Format milliseconds as readable duration."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:
        return f"{ms / 1000:.2f}s"
    else:
        minutes = ms / 60000
        return f"{minutes:.2f}m"


def format_timestamp(dt) -> str:
    """Format datetime for display."""
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def generate_report(run_id: int = None, latest: bool = False, db: Session = None):
    """Generate and display ingestion report."""
    
    if db is None:
        db = SessionLocal()
    
    run_repo = IngestionRunRepository(db)
    metric_repo = SourceIngestionMetricRepository(db)
    source_repo = SourceRepository(db)
    
    # Get the ingestion run
    if latest:
        ingestion_run = run_repo.get_latest_run()
        if not ingestion_run:
            print("No ingestion runs found in database.")
            return
    elif run_id:
        ingestion_run = run_repo.get_by_id(run_id)
        if not ingestion_run:
            print(f"Ingestion run {run_id} not found.")
            return
    else:
        print("Please specify --run-id or --latest")
        return
    
    # Get source metrics
    source_metrics = metric_repo.list_by_ingestion_run(ingestion_run.id)
    
    # Generate report
    print("\n" + "=" * 70)
    print("FLASHFACTS INGESTION REPORT")
    print("=" * 70)
    
    print(f"\nRun ID: {ingestion_run.id}")
    print(f"Status: {ingestion_run.status.upper()}")
    print(f"Started: {format_timestamp(ingestion_run.started_at)}")
    print(f"Completed: {format_timestamp(ingestion_run.completed_at)}")
    print(f"Duration: {format_duration_ms(ingestion_run.processing_time_ms)}")
    
    print("\n" + "-" * 70)
    print("AGGREGATE STATISTICS")
    print("-" * 70)
    
    print(f"\nSources:")
    print(f"  Attempted: {ingestion_run.sources_attempted}")
    print(f"  Succeeded: {ingestion_run.sources_succeeded}")
    print(f"  Failed: {ingestion_run.sources_failed}")
    
    print(f"\nDocuments:")
    print(f"  Discovered: {ingestion_run.documents_discovered}")
    print(f"  Accepted: {ingestion_run.documents_accepted}")
    print(f"  Duplicates: {ingestion_run.documents_duplicate}")
    
    print(f"\nEvents:")
    print(f"  Created: {ingestion_run.events_created}")
    print(f"  Deduplicated: {ingestion_run.events_deduplicated}")
    
    print(f"\nErrors: {ingestion_run.error_count}")
    
    if source_metrics:
        print("\n" + "-" * 70)
        print("SOURCE BREAKDOWN")
        print("-" * 70)
        
        for metric in source_metrics:
            source = source_repo.get_by_id(metric.source_id)
            source_name = source.name if source else f"Source {metric.source_id}"
            
            print(f"\n{source_name}")
            print(f"  Status: {metric.status}")
            print(f"  Started: {format_timestamp(metric.started_at)}")
            print(f"  Completed: {format_timestamp(metric.completed_at)}")
            print(f"  Duration: {format_duration_ms(metric.processing_time_ms)}")
            
            if metric.http_status:
                print(f"  HTTP Status: {metric.http_status}")
            
            print(f"  Documents:")
            print(f"    Discovered: {metric.documents_discovered}")
            print(f"    Accepted: {metric.documents_accepted}")
            print(f"    Duplicates: {metric.documents_duplicate}")
            
            print(f"  Events:")
            print(f"    Created: {metric.events_created}")
            print(f"    Deduplicated: {metric.events_deduplicated}")
            
            if metric.error_message:
                print(f"  Error: {metric.error_message}")
    
    print("\n" + "=" * 70)
    print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate FlashFacts ingestion report from database"
    )
    parser.add_argument(
        "--run-id",
        type=int,
        help="Specific ingestion run ID to report on"
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Report on the most recent ingestion run"
    )
    
    args = parser.parse_args()
    
    if not args.run_id and not args.latest:
        parser.print_help()
        sys.exit(1)
    
    try:
        generate_report(run_id=args.run_id, latest=args.latest)
    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
