import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import feedparser
import httpx
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
from app.services.ai_provider import FallbackAIProvider
from app.schemas.enrichment import EventEnrichment
from app.utils.hashing import compute_content_hash
from app.core.config import settings

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

    def parse_datetime(self, entry: Dict[str, Any]) -> Optional[datetime]:
        dt_raw = entry.get("published") or entry.get("updated") or entry.get("pubDate")
        if dt_raw:
            try:
                dt = date_parser.parse(dt_raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
        return None

    def fetch_feed(self, feed_url: str) -> Tuple[Optional[feedparser.FeedParserDict], Optional[int], Optional[str]]:
        """
        Fetch a feed URL with error handling.

        Returns:
            Tuple of (parsed_feed, http_status, error_message)
        """
        retryable_statuses = {429, 500, 502, 503, 504}
        attempts = max(1, settings.INGESTION_MAX_RETRIES + 1)
        last_error = None

        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(
                    timeout=settings.INGESTION_REQUEST_TIMEOUT,
                    follow_redirects=True,
                ) as client:
                    response = client.get(
                        feed_url,
                        headers={"User-Agent": settings.INGESTION_USER_AGENT},
                    )
                if response.status_code == 200:
                    parsed = feedparser.parse(response.content)
                    if getattr(parsed, "bozo", False) and not getattr(parsed, "entries", None):
                        return None, response.status_code, "Malformed or empty feed"
                    return parsed, response.status_code, None

                last_error = f"HTTP {response.status_code} fetching feed {feed_url}"
                if response.status_code not in retryable_statuses:
                    break
            except httpx.TimeoutException as exc:
                last_error = f"Timeout fetching feed {feed_url}: {exc}"
            except httpx.RequestError as exc:
                last_error = f"Request error fetching feed {feed_url}: {exc}"
            except Exception as exc:
                last_error = f"Error fetching feed {feed_url}: {exc}"
                break

            if attempt < attempts:
                delay = settings.INGESTION_RETRY_BACKOFF * (2 ** (attempt - 1))
                logger.warning("Feed fetch retry: url=%s attempt=%s delay=%.2fs error=%s", feed_url, attempt, delay, last_error)
                time.sleep(delay)

        logger.warning("Feed fetch failed: url=%s attempts=%s error=%s", feed_url, attempts, last_error)
        status = None
        if last_error and last_error.startswith("HTTP "):
            status = int(last_error.split()[1])
        return None, status, last_error or "Unknown feed fetch error"

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
            source.last_attempted_at = datetime.now(timezone.utc)
            source.last_error = None
            self.db.commit()
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
                source.last_error = metric.error_message
                self.db.commit()
                return metric

            metric.documents_discovered = len(feed.entries)

            # 2. Process each entry in the feed
            for entry in feed.entries:
                try:
                    url = entry.get("link") or entry.get("id") or ""
                    title = entry.get("title") or ""
                    source_guid = entry.get("guid") or entry.get("id") or None

                    # Content extraction
                    content = entry.get("summary") or ""
                    if not content and "content" in entry and len(entry.get("content", [])) > 0:
                        content = entry.get("content")[0].get("value", "")

                    title = self.extractor.clean_text(title)
                    content = self.extractor.clean_text(content)

                    # Validate entry
                    if not title and not content:
                        continue
                    if not url:
                        logger.debug("Skipping entry without URL")
                        continue

                    pub_dt = self.parse_datetime(entry)
                    content_hash = compute_content_hash(url, title, content)

                    # Check for duplicate document
                    existing_doc = self.doc_repo.get_by_content_hash(content_hash)
                    if not existing_doc:
                        existing_doc = self.doc_repo.get_by_source_url(source.id, url)
                    if not existing_doc and source_guid:
                        existing_doc = self.db.query(Document).filter(
                            Document.source_id == source.id,
                            Document.source_guid == source_guid,
                        ).first()
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
                        content_hash=content_hash,
                        source_guid=source_guid,
                    )
                    doc = self.doc_repo.create(doc_in)
                    metric.documents_accepted += 1

                    if pub_dt is None:
                        self.doc_repo.mark_processed(doc.id)
                        logger.info("Stored document without event date: source=%s url=%s", source.name, url)
                        continue

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

                        try:
                            validated_enrichment = EventEnrichment.model_validate({
                                **enrichment,
                                "classification": enrichment.get("classification", event_candidate["domain"]),
                            })
                        except Exception as exc:
                            logger.warning("AI output validation failed; using fallback: %s", exc)
                            fallback = FallbackAIProvider().enrich_event(
                                event_candidate["title"], doc.content,
                                event_candidate["domain"], source.reliability_score,
                            )
                            validated_enrichment = EventEnrichment.model_validate({
                                **fallback,
                                "provider": "fallback",
                                "used_fallback": True,
                            })
                        event_candidate["summary"] = validated_enrichment.summary or event_candidate["summary"]
                        event_candidate["domain"] = validated_enrichment.classification
                        event_candidate["event_type"] = validated_enrichment.event_type
                        event_candidate["why_it_matters"] = validated_enrichment.why_it_matters
                        event_candidate["importance_score"] = validated_enrichment.importance_score
                        event_candidate["classification_confidence"] = validated_enrichment.classification_confidence
                        event_candidate["ai_processed_at"] = datetime.now(timezone.utc)
                        event_candidate["processing_status"] = "completed"

                        event_in, _ = self.dedup.prepare_event_candidate(event_candidate)
                        new_event = self.event_repo.create(event_in, document_id=doc.id)

                        # Attach Entities if extracted
                        entities_data = [entity.model_dump() for entity in validated_enrichment.entities]
                        if entities_data:
                            self.event_repo.attach_entities(new_event.id, entities_data)

                        metric.events_created += 1
                        logger.debug(f"Created & enriched new event ID {new_event.id}: '{new_event.title}'")

                    # Mark document processed
                    self.doc_repo.mark_processed(doc.id)

                except Exception as e:
                    self.db.rollback()
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
            self.db.rollback()
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
