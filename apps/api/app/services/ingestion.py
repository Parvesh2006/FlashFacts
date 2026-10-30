import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import feedparser
import httpx
from app.core.config import settings
from dateutil import parser as date_parser
from sqlalchemy.orm import Session

from app.models.source import Source
from app.models.document import Document
from app.models.event import Event
from app.models.processing_job import ProcessingJob
from app.models.ingestion_run import IngestionRun
from app.models.source_ingestion_metric import SourceIngestionMetric
from app.schemas.document import DocumentCreate
from app.repositories.source_repository import SourceRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.event_repository import EventRepository
from app.services.extraction import EventExtractorService
from app.services.deduplication import DeduplicationService
from app.services.ai_provider import get_ai_provider
from app.services.location_service import LocationService
from app.utils.hashing import compute_content_hash

logger = logging.getLogger("app")

DEFAULT_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 (FlashFacts/1.0)"
)


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.source_repo = SourceRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.event_repo = EventRepository(db)
        self.extractor = EventExtractorService()
        self.dedup = DeduplicationService(self.event_repo)
        self.ai_provider = get_ai_provider()
        self.location_service = LocationService(db)

    def parse_datetime(self, entry: Dict[str, Any]) -> datetime:
        dt_raw = entry.get("published") or entry.get("updated") or entry.get("pubDate")
        if dt_raw:
            try:
                dt = date_parser.parse(dt_raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
        return datetime.now(timezone.utc)

    def fetch_feed(self, feed_url: str) -> Tuple[Optional[feedparser.FeedParserDict], Optional[int], Optional[str]]:
        """
        Fetch a feed URL with error handling, browser-compatible User-Agent, and retry mechanism.

        Returns:
            Tuple of (parsed_feed, http_status, error_message)
        """
        retryable_statuses = {429, 500, 502, 503, 504}
        max_retries = max(1, getattr(settings, "INGESTION_MAX_RETRIES", 1))
        attempts = max_retries + 1
        last_error = None
        last_status = None

        user_agent = getattr(settings, "INGESTION_USER_AGENT", "")
        if not user_agent or "FlashFacts/0.1" in user_agent or "(+https://example.com)" in user_agent:
            user_agent = DEFAULT_BROWSER_UA

        timeout = getattr(settings, "INGESTION_REQUEST_TIMEOUT", 10.0)

        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(
                    timeout=timeout,
                    follow_redirects=True,
                ) as client:
                    headers = {
                        "User-Agent": user_agent,
                        "Accept": "application/rss+xml, application/xml, text/xml, */*",
                        "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
                    }
                    resp = client.get(feed_url, headers=headers)
                    last_status = resp.status_code

                if resp.status_code == 200:
                    raw_content = getattr(resp, "content", getattr(resp, "text", ""))
                    parsed = feedparser.parse(raw_content)
                    if getattr(parsed, "bozo", False) and not getattr(parsed, "entries", None):
                        return None, resp.status_code, "Malformed or empty feed"
                    return parsed, resp.status_code, None

                last_error = f"HTTP {resp.status_code} fetching feed {feed_url}"
                if resp.status_code not in retryable_statuses:
                    return None, resp.status_code, last_error

            except httpx.TimeoutException as e:
                last_error = f"Timeout fetching feed {feed_url}: {e}"
                logger.warning(last_error)
            except httpx.RequestError as e:
                last_error = f"Request error fetching feed {feed_url}: {e}"
                logger.warning(last_error)
            except Exception as e:
                last_error = f"Error fetching feed {feed_url}: {e}"
                logger.warning(last_error)

            if attempt < attempts:
                backoff = getattr(settings, "INGESTION_RETRY_BACKOFF", 0.5) * (2 ** (attempt - 1))
                time.sleep(backoff)

        logger.warning("Feed fetch failed: url=%s attempts=%s error=%s", feed_url, attempts, last_error)
        return None, last_status, last_error or "Feed fetch failed"

    def ingest_source(self, source: Source, ingestion_run: IngestionRun) -> SourceIngestionMetric:
        """
        Ingest a single source with comprehensive error handling, PostgreSQL commit persistence,
        and structured logging. One source failure MUST NOT stop the entire ingestion run.

        Returns:
            SourceIngestionMetric tracking the results for this source
        """
        metric = SourceIngestionMetric(
            ingestion_run_id=ingestion_run.id,
            source_id=source.id,
            started_at=datetime.now(timezone.utc)
        )
        metric._source_name = source.name

        start_time = time.time()

        logger.info(
            "SOURCE_INGESTION_STARTED source_id=%s source_name='%s' feed_url='%s'",
            source.id,
            source.name,
            source.feed_url
        )

        # 1. Immediately record and commit attempt timestamp to PostgreSQL
        source.last_attempted_at = datetime.now(timezone.utc)
        try:
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        except Exception as e:
            logger.warning("Could not persist source attempt timestamp for '%s': %s", source.name, e)
            self.db.rollback()

        try:
            # 2. Fetch Feed
            feed, http_status, error_msg = self.fetch_feed(source.feed_url)
            metric.http_status = http_status

            if not feed or not hasattr(feed, "entries"):
                if error_msg:
                    metric.error_message = error_msg
                    metric.status = "http_error" if http_status else "failed"
                else:
                    metric.error_message = f"Empty or invalid feed for source '{source.name}'"
                    metric.status = "invalid_feed"

                logger.warning(
                    "SOURCE_INGESTION_FAILED source_id=%s source_name='%s' http_status=%s error='%s'",
                    source.id,
                    source.name,
                    metric.http_status,
                    metric.error_message
                )
                return metric

            metric.documents_discovered = len(feed.entries)

            # 3. Process each entry in the feed with transaction isolation
            for entry in feed.entries:
                try:
                    url = entry.get("link") or entry.get("id") or ""
                    title = entry.get("title") or ""

                    # Content extraction
                    content = entry.get("summary") or ""
                    if not content and "content" in entry and len(entry.get("content", [])) > 0:
                        content = entry.get("content")[0].get("value", "")

                    # Validate entry
                    if not title and not content:
                        continue
                    if not url:
                        continue

                    pub_dt = self.parse_datetime(entry)
                    freshness_hours = getattr(settings, "INGESTION_FRESHNESS_HOURS", 0)
                    if freshness_hours and freshness_hours > 0 and pub_dt:
                        cutoff = datetime.now(timezone.utc) - timedelta(hours=freshness_hours)
                        if pub_dt < cutoff:
                            continue

                    content_hash = compute_content_hash(url, title, content)

                    # Check for duplicate document
                    existing_doc = self.doc_repo.get_by_content_hash(content_hash)
                    if existing_doc:
                        metric.documents_duplicate += 1
                        continue

                    # Store Document
                    doc_in = DocumentCreate(
                        source_id=source.id,
                        title=title,
                        content=content,
                        url=url,
                        published_at=pub_dt,
                        content_hash=content_hash
                    )
                    doc = self.doc_repo.create(doc_in)
                    metric.documents_accepted += 1

                    # Extract Event Candidate
                    event_candidate = self.extractor.extract_event_candidate(doc, source)

                    # Check Event Deduplication
                    existing_event = self.dedup.check_duplicate(event_candidate)
                    if existing_event:
                        # Link document to existing event
                        self.event_repo.add_event_source(
                            event_id=existing_event.id,
                            document_id=doc.id,
                            source_id=source.id
                        )
                        metric.events_deduplicated += 1
                    else:
                        # AI Enrichment for New Event Candidate
                        try:
                            enrichment = self.ai_provider.enrich_event(
                                title=event_candidate["title"],
                                content=doc.content,
                                domain=event_candidate["domain"],
                                reliability_score=source.reliability_score
                            )
                        except Exception as e:
                            logger.warning("AI enrichment failed for event, using fallback: %s", e)
                            enrichment = {
                                "summary": event_candidate["summary"],
                                "classification": event_candidate["domain"],
                                "classification_confidence": 0.5,
                                "importance_score": event_candidate.get("importance_score", 50),
                                "why_it_matters": "Verified current affairs development for competitive examination preparation",
                                "entities": []
                            }

                        event_candidate["summary"] = enrichment.get("summary", event_candidate["summary"])
                        event_candidate["domain"] = enrichment.get("classification", event_candidate["domain"])
                        event_candidate["why_it_matters"] = (
                            enrichment.get("why_it_matters")
                            or "Verified current affairs development for competitive examination preparation"
                        )
                        ai_score = enrichment.get("importance_score", 50)
                        rel_score = event_candidate.get("importance_score", 50)
                        event_candidate["importance_score"] = max(ai_score, rel_score)
                        event_candidate["classification_confidence"] = enrichment.get("classification_confidence", 0.5)
                        event_candidate["ai_processed_at"] = datetime.now(timezone.utc)
                        event_candidate["processing_status"] = "completed"

                        event_in, _ = self.dedup.prepare_event_candidate(event_candidate)
                        new_event = self.event_repo.create(event_in, document_id=doc.id)
                        self.location_service.attach_locations_to_event(new_event)

                        # Attach Entities if extracted
                        entities_data = enrichment.get("entities", [])
                        if entities_data:
                            self.event_repo.attach_entities(new_event.id, entities_data)

                        metric.events_created += 1

                    # Mark document processed
                    self.doc_repo.mark_processed(doc.id)

                except Exception as e:
                    logger.error("Error processing entry from source '%s': %s", source.name, e, exc_info=True)
                    self.db.rollback()
                    continue

            metric.status = "success"

        except Exception as e:
            logger.error("Unexpected error ingesting source '%s': %s", source.name, e, exc_info=True)
            self.db.rollback()
            metric.status = "failed"
            metric.error_message = str(e)

        finally:
            # Always finalize the metric and commit source status to PostgreSQL
            metric.completed_at = datetime.now(timezone.utc)
            metric.processing_time_ms = (time.time() - start_time) * 1000

            try:
                self.db.add(metric)

                if metric.status == "success":
                    source.last_ingested_at = datetime.now(timezone.utc)
                    source.last_error = None
                    logger.info(
                        "SOURCE_INGESTION_COMPLETED source_id=%s source_name='%s' fetched=%s accepted=%s duplicates=%s events_created=%s events_deduped=%s duration_ms=%.2f",
                        source.id,
                        source.name,
                        metric.documents_discovered,
                        metric.documents_accepted,
                        metric.documents_duplicate,
                        metric.events_created,
                        metric.events_deduplicated,
                        metric.processing_time_ms
                    )
                else:
                    if not metric.error_message:
                        metric.error_message = f"Ingestion failed with status {metric.status}"
                    source.last_error = metric.error_message
                    logger.warning(
                        "SOURCE_INGESTION_FAILED source_id=%s source_name='%s' error='%s' duration_ms=%.2f",
                        source.id,
                        source.name,
                        metric.error_message,
                        metric.processing_time_ms
                    )

                self.db.add(source)
                self.db.commit()
                self.db.refresh(source)
            except Exception as e:
                logger.error("Failed to commit final metric and source status for '%s': %s", source.name, e, exc_info=True)
                self.db.rollback()

        return metric

    def ingest_all_enabled_sources(self, source_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Ingest all enabled sources (or a specific source if source_id is specified)
        with comprehensive metrics tracking and structured logging.

        If one source fails, continue with the next source.
        Track all metrics per source and aggregate them.
        """
        run_start_time = time.time()

        # Create ingestion run tracker
        ingestion_run = IngestionRun(
            started_at=datetime.now(timezone.utc),
            status="running"
        )
        self.db.add(ingestion_run)
        self.db.commit()
        self.db.refresh(ingestion_run)

        # Also create a ProcessingJob for backwards compatibility
        job = ProcessingJob(job_type="ingestion", status="running", items_processed=0)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        if source_id is not None:
            source = self.source_repo.get_by_id(source_id)
            sources = [source] if source else []
        else:
            sources = self.source_repo.list_sources(enabled_only=True)

        ingestion_run.sources_attempted = len(sources)

        logger.info(
            "INGESTION_RUN_STARTED run_id=%s total_sources=%s",
            ingestion_run.id,
            len(sources)
        )

        source_metrics: List[SourceIngestionMetric] = []

        for source in sources:
            try:
                metric = self.ingest_source(source, ingestion_run)
                source_metrics.append(metric)

                if metric.status == "success":
                    ingestion_run.sources_succeeded += 1
                else:
                    ingestion_run.sources_failed += 1
                    ingestion_run.error_count += 1

            except Exception as e:
                logger.error(
                    "SOURCE_INGESTION_FAILED source_id=%s source_name='%s' unhandled_exception='%s'",
                    source.id,
                    source.name,
                    e,
                    exc_info=True
                )
                self.db.rollback()
                ingestion_run.sources_failed += 1
                ingestion_run.error_count += 1

        # Aggregate metrics from all sources
        for metric in source_metrics:
            ingestion_run.documents_discovered += metric.documents_discovered
            ingestion_run.documents_accepted += metric.documents_accepted
            ingestion_run.documents_duplicate += metric.documents_duplicate
            ingestion_run.events_created += metric.events_created
            ingestion_run.events_deduplicated += metric.events_deduplicated

        # Finalize ingestion run
        ingestion_run.completed_at = datetime.now(timezone.utc)
        ingestion_run.status = "completed"
        ingestion_run.processing_time_ms = (time.time() - run_start_time) * 1000
        self.db.commit()

        # Update ProcessingJob for backwards compatibility
        job.status = "completed"
        job.items_processed = ingestion_run.documents_accepted
        job.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(
            "INGESTION_RUN_COMPLETED run_id=%s status=%s attempted=%s succeeded=%s failed=%s fetched=%s accepted=%s duplicates=%s events_created=%s events_deduped=%s duration_ms=%.2f errors=%s",
            ingestion_run.id,
            ingestion_run.status,
            ingestion_run.sources_attempted,
            ingestion_run.sources_succeeded,
            ingestion_run.sources_failed,
            ingestion_run.documents_discovered,
            ingestion_run.documents_accepted,
            ingestion_run.documents_duplicate,
            ingestion_run.events_created,
            ingestion_run.events_deduplicated,
            ingestion_run.processing_time_ms,
            ingestion_run.error_count
        )

        errors_summary = [
            {
                "source_id": m.source_id,
                "source_name": getattr(m, "_source_name", f"Source {m.source_id}"),
                "status": m.status,
                "error": m.error_message
            }
            for m in source_metrics if m.status != "success" or m.error_message
        ]

        return {
            "ingestion_run_id": ingestion_run.id,
            "job_id": job.id,
            "status": ingestion_run.status,
            "sources_attempted": ingestion_run.sources_attempted,
            "sources_succeeded": ingestion_run.sources_succeeded,
            "sources_failed": ingestion_run.sources_failed,
            "articles_fetched": ingestion_run.documents_discovered,
            "articles_accepted": ingestion_run.documents_accepted,
            "articles_stored": ingestion_run.events_created,
            "duplicates_skipped": ingestion_run.documents_duplicate,
            "events_created": ingestion_run.events_created,
            "events_deduplicated": ingestion_run.events_deduplicated,
            "documents_discovered": ingestion_run.documents_discovered,
            "documents_ingested": ingestion_run.documents_accepted,
            "documents_duplicate": ingestion_run.documents_duplicate,
            "processing_time_ms": ingestion_run.processing_time_ms,
            "error_count": ingestion_run.error_count,
            "errors": errors_summary
        }
