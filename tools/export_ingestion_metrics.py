#!/usr/bin/env python3
"""
FlashFacts Experiment Data Export Tool

Exports ingestion metrics to CSV files for research and analysis.

Generated files:
  - data/experiments/ingestion_runs.csv
  - data/experiments/source_metrics.csv
  - data/experiments/event_metrics.csv

Usage:
    python tools/export_ingestion_metrics.py
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ingestion_run import IngestionRun
from app.models.source_ingestion_metric import SourceIngestionMetric
from app.repositories.ingestion_run_repository import IngestionRunRepository
from app.repositories.source_ingestion_metric_repository import SourceIngestionMetricRepository
from app.repositories.source_repository import SourceRepository


def export_ingestion_runs(db: Session, output_dir: Path):
    """Export all ingestion runs to CSV."""
    repo = IngestionRunRepository(db)
    runs = repo.list_runs(limit=10000)  # Large limit to get all

    output_file = output_dir / "ingestion_runs.csv"

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "run_id",
            "status",
            "started_at",
            "completed_at",
            "processing_time_ms",
            "sources_attempted",
            "sources_succeeded",
            "sources_failed",
            "documents_discovered",
            "documents_accepted",
            "documents_duplicate",
            "events_created",
            "events_deduplicated",
            "error_count"
        ])

        for run in runs:
            writer.writerow([
                run.id,
                run.status,
                run.started_at.isoformat() if run.started_at else "",
                run.completed_at.isoformat() if run.completed_at else "",
                run.processing_time_ms,
                run.sources_attempted,
                run.sources_succeeded,
                run.sources_failed,
                run.documents_discovered,
                run.documents_accepted,
                run.documents_duplicate,
                run.events_created,
                run.events_deduplicated,
                run.error_count
            ])

    print(f"Exported {len(runs)} ingestion runs to {output_file}")
    return len(runs)


def export_source_metrics(db: Session, output_dir: Path):
    """Export all source ingestion metrics to CSV."""
    repo = IngestionRunRepository(db)
    metric_repo = SourceIngestionMetricRepository(db)
    source_repo = SourceRepository(db)

    runs = repo.list_runs(limit=10000)
    metrics = []

    for run in runs:
        metrics.extend(metric_repo.list_by_ingestion_run(run.id))

    output_file = output_dir / "source_metrics.csv"

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "metric_id",
            "ingestion_run_id",
            "source_id",
            "source_name",
            "status",
            "started_at",
            "completed_at",
            "processing_time_ms",
            "http_status",
            "documents_discovered",
            "documents_accepted",
            "documents_duplicate",
            "events_created",
            "events_deduplicated",
            "error_message"
        ])

        for metric in metrics:
            source = source_repo.get_by_id(metric.source_id)
            source_name = source.name if source else f"Source {metric.source_id}"

            writer.writerow([
                metric.id,
                metric.ingestion_run_id,
                metric.source_id,
                source_name,
                metric.status,
                metric.started_at.isoformat() if metric.started_at else "",
                metric.completed_at.isoformat() if metric.completed_at else "",
                metric.processing_time_ms,
                metric.http_status or "",
                metric.documents_discovered,
                metric.documents_accepted,
                metric.documents_duplicate,
                metric.events_created,
                metric.events_deduplicated,
                metric.error_message or ""
            ])

    print(f"Exported {len(metrics)} source metrics to {output_file}")
    return len(metrics)


def export_event_metrics(db: Session, output_dir: Path):
    """
    Export event-level metrics aggregated by event.

    Computed metrics:
    - events_per_source: how many sources reported each event
    - domains: domain distribution
    - importance: importance score distribution
    """
    from app.models.event import Event
    from app.models.source import Source

    events = db.query(Event).all()

    output_file = output_dir / "event_metrics.csv"

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "event_id",
            "title",
            "domain",
            "event_date",
            "importance_score",
            "classification_confidence",
            "sources_count",
            "published_at",
            "processing_status"
        ])

        for event in events:
            sources_count = len(event.event_sources) if event.event_sources else 0

            writer.writerow([
                event.id,
                event.title,
                event.domain,
                event.event_date.isoformat() if event.event_date else "",
                event.importance_score,
                event.classification_confidence,
                sources_count,
                event.published_at.isoformat() if event.published_at else "",
                event.processing_status
            ])

    print(f"Exported {len(events)} event metrics to {output_file}")
    return len(events)


def main():
    """Export all metrics to CSV."""
    output_dir = Path(__file__).parent.parent / "data" / "experiments"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nExporting ingestion metrics to {output_dir}\n")

    db = SessionLocal()

    try:
        runs_count = export_ingestion_runs(db, output_dir)
        metrics_count = export_source_metrics(db, output_dir)
        events_count = export_event_metrics(db, output_dir)

        print(f"\nExport completed successfully!")
        print(f"  {runs_count} ingestion runs")
        print(f"  {metrics_count} source metrics")
        print(f"  {events_count} events")
        print(f"\nOutput directory: {output_dir}")

    except Exception as e:
        print(f"Error exporting metrics: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
