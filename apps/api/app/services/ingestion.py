import logging
import time
from datetime import datetime, timezone
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
from app.utils.hashing import compute_content_hash

logger = logging.getLogger("app")


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.source_repo = SourceRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.event_repo = EventRepository(db)
        self.extractor = EventExtractorService()
        self.dedup = DeduplicationService(self.event_repo)
        self.ai_provider = get_ai_provider()

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
        Fetch a feed URL with error handling.
        Fetch a feed URL with error handling and retry mechanism.
        
        Returns:
            Tuple of (parsed_feed, http_status, error_message)
        """
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                headers = {"User-Agent": "FlashFactsIngestionWorker/1.0"}
                resp = client.get(feed_url, headers=headers)
        retryable_statuses = {429, 500, 502, 503, 504}
        max_retries = getattr(settings, "INGESTION_MAX_RETRIES", 3)
        attempts = max(1, max_retries + 1)
        last_error = None
        last_status = None

        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(
                    timeout=getattr(settings, "INGESTION_REQUEST_TIMEOUT", 10.0),
                    follow_redirects=True,
                ) as client:
                    headers = {"User-Agent": getattr(settings, "INGESTION_USER_AGENT", "FlashFactsIngestionWorker/1.0")}
                    resp = client.get(feed_url, headers=headers)
                    last_status = resp.status_code

                if resp.status_code == 200:
                    return feedparser.parse(resp.text), resp.status_code, None
                else:
                    error_msg = f"HTTP {resp.status_code} fetching feed {feed_url}"
                    logger.warning(error_msg)
                    return None, resp.status_code, error_msg
        except httpx.TimeoutException as e:
            error_msg = f"Timeout fetching feed {feed_url}: {e}"
            logger.error(error_msg)
            return None, None, error_msg
        except httpx.RequestError as e:
            error_msg = f"Request error fetching feed {feed_url}: {e}"
            logger.error(error_msg)
            return None, None, error_msg
        except Exception as e:
            error_msg = f"Error fetching feed {feed_url}: {e}"
            logger.error(error_msg)
            return None, None, error_msg
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
                logger.error(last_error)
            except httpx.RequestError as e:
                last_error = f"Request error fetching feed {feed_url}: {e}"
                logger.error(last_error)
            except Exception as e:
                last_error = f"Error fetching feed {feed_url}: {e}"
                logger.error(last_error)
                break

            if attempt < attempts:
                backoff = getattr(settings, "INGESTION_RETRY_BACKOFF", 1.0) * (2 ** (attempt - 1))
                time.sleep(backoff)

        return None, last_status, last_error


        logger.warning(f"Feed fetch failed: url={feed_url} attempts={attempts} error={last_error}")
        status = None
        if last_error and last_error.startswith("HTTP "):
            try:
                status = int(last_error.split()[1])
            except Exception:
                pass
        return None, status, last_error or "Malformed or empty feed"

    def ingest_source(self, source: Source, ingestion_run: IngestionRun) -> SourceIngestionMetric:
        """
        Ingest a single source with comprehensive error handling and metrics tracking.
        One source failure MUST NOT stop the entire ingestion run.
        
        Returns:
            SourceIngestionMetric tracking the results for this source
        """
        metric = SourceIngestionMetric(
            ingestion_run_id=ingestion_run.id,
            source_id=source.id,
            started_at=datetime.now(timezone.utc)
        )
        
        start_time = time.time()
        
        try:
            logger.info(f"Ingestion started for source: '{source.name}' (ID: {source.id})")
            
            # 1. Fetch Feed
            feed, http_status, error_msg = self.fetch_feed(source.feed_url)
            metric.http_status = http_status
            
            if not feed or not hasattr(feed, "entries"):
                if error_msg:
                    metric.error_message = error_msg
                    metric.status = "http_error" if http_status else "failed"
                else:
                    metric.error_message = f"Empty or invalid feed for source '{source.name}'"
                    metric.status = "invalid_feed"
                
                metric.completed_at = datetime.now(timezone.utc)
                metric.processing_time_ms = (time.time() - start_time) * 1000
                self.db.add(metric)
                self.db.commit()
                logger.warning(f"Failed to ingest source '{source.name}': {metric.error_message}")
                
                # Still update source.last_ingested_at
                source.last_ingested_at = datetime.now(timezone.utc)
                self.db.commit()
                return metric

            metric.documents_discovered = len(feed.entries)
            
            # 2. Process each entry in the feed
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
                        logger.debug("Skipping entry without URL")
                        continue

                    pub_dt = self.parse_datetime(entry)
                    freshness_hours = getattr(settings, "INGESTION_FRESHNESS_HOURS", 0)
                    if freshness_hours and freshness_hours > 0 and pub_dt:
                        cutoff = datetime.now(timezone.utc) - timedelta(hours=freshness_hours)
                        if pub_dt < cutoff:
                            logger.debug(f"Skipping stale entry '{title}' published at {pub_dt}")
                            continue

                    content_hash = compute_content_hash(url, title, content)

                    # Check for duplicate document
                    existing_doc = self.doc_repo.get_by_content_hash(content_hash)
                    if existing_doc:
                        metric.documents_duplicate += 1
                        logger.debug(f"Skipping duplicate document content hash {content_hash}")
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
                        logger.debug(f"Event deduplicated and linked to event ID {existing_event.id}")
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
                            logger.warning(f"AI enrichment failed for event, using fallback: {e}")
                            # Fallback: create minimal enrichment
                            enrichment = {
                                "summary": event_candidate["summary"],
                                "classification": event_candidate["domain"],
                                "classification_confidence": 0.5,
                                "importance_score": 50,
                                "why_it_matters": "Processing status: AI enrichment unavailable",
                                "entities": []
                            }

                        event_candidate["summary"] = enrichment.get("summary", event_candidate["summary"])
                        event_candidate["domain"] = enrichment.get("classification", event_candidate["domain"])
                        event_candidate["why_it_matters"] = enrichment.get("why_it_matters")
                        event_candidate["importance_score"] = enrichment.get("importance_score", 50)
                        event_candidate["classification_confidence"] = enrichment.get("classification_confidence", 0.5)
                        event_candidate["ai_processed_at"] = datetime.now(timezone.utc)
                        event_candidate["processing_status"] = "completed"

                        event_in, _ = self.dedup.prepare_event_candidate(event_candidate)
                        new_event = self.event_repo.create(event_in, document_id=doc.id)

                        # Attach Entities if extracted
                        entities_data = enrichment.get("entities", [])
                        if entities_data:
                            self.event_repo.attach_entities(new_event.id, entities_data)

                        metric.events_created += 1
                        logger.debug(f"Created & enriched new event ID {new_event.id}: '{new_event.title}'")

                    # Mark document processed
                    self.doc_repo.mark_processed(doc.id)

                except Exception as e:
                    logger.error(f"Error processing entry from source '{source.name}': {e}", exc_info=True)
                    continue

            metric.status = "success"
            logger.info(
                f"Ingestion completed for source '{source.name}': "
                f"Discovered={metric.documents_discovered}, Accepted={metric.documents_accepted}, "
                f"Duplicates={metric.documents_duplicate}, "
                f"EventsCreated={metric.events_created}, EventsDeduped={metric.events_deduplicated}"
            )

        except Exception as e:
            logger.error(f"Unexpected error ingesting source '{source.name}': {e}", exc_info=True)
            metric.status = "failed"
            metric.error_message = str(e)

        finally:
            # Always finalize the metric
            metric.completed_at = datetime.now(timezone.utc)
            metric.processing_time_ms = (time.time() - start_time) * 1000
            self.db.add(metric)
            
            # Update source.last_ingested_at
            source.last_ingested_at = datetime.now(timezone.utc)
            if metric.status == "success":
                source.last_error = None
            elif metric.error_message:
                source.last_error = metric.error_message
            self.db.commit()

        return metric

    def ingest_all_enabled_sources(self) -> Dict[str, Any]:
        """
        Ingest all enabled sources with comprehensive tracking.
        
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
        
        logger.info(f"Ingestion run {ingestion_run.id} started")
        
        # Also create a ProcessingJob for backwards compatibility
        job = ProcessingJob(job_type="ingestion", status="running", items_processed=0)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        sources = self.source_repo.list_sources(enabled_only=True)
        ingestion_run.sources_attempted = len(sources)
        
        source_metrics = []

        for source in sources:
            try:
                # Ingest this source (source failure will NOT stop the run)
                metric = self.ingest_source(source, ingestion_run)
                source_metrics.append(metric)
                
                # Update run counters
                if metric.status == "success":
                    ingestion_run.sources_succeeded += 1
                else:
                    ingestion_run.sources_failed += 1
                    ingestion_run.error_count += 1
                    
            except Exception as e:
                # Even if ingest_source raises, we continue
                logger.error(f"Exception handling source '{source.name}': {e}", exc_info=True)
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
            f"Ingestion run {ingestion_run.id} completed: "
            f"Sources attempted={ingestion_run.sources_attempted}, "
            f"succeeded={ingestion_run.sources_succeeded}, "
            f"failed={ingestion_run.sources_failed}, "
            f"Documents discovered={ingestion_run.documents_discovered}, "
            f"accepted={ingestion_run.documents_accepted}, "
            f"duplicates={ingestion_run.documents_duplicate}, "
            f"Events created={ingestion_run.events_created}, "
            f"deduplicated={ingestion_run.events_deduplicated}, "
            f"Processing time: {ingestion_run.processing_time_ms:.2f}ms"
        )

        return {
            "ingestion_run_id": ingestion_run.id,
            "job_id": job.id,
            "status": ingestion_run.status,
            "sources_attempted": ingestion_run.sources_attempted,
            "sources_succeeded": ingestion_run.sources_succeeded,
            "sources_failed": ingestion_run.sources_failed,
            "documents_discovered": ingestion_run.documents_discovered,
            "documents_ingested": ingestion_run.documents_accepted,
            "documents_duplicate": ingestion_run.documents_duplicate,
            "events_created": ingestion_run.events_created,
            "events_deduplicated": ingestion_run.events_deduplicated,
            "processing_time_ms": ingestion_run.processing_time_ms,
            "error_count": ingestion_run.error_count
        }
