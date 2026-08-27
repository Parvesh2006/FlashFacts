import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import feedparser
import httpx
from dateutil import parser as date_parser
from sqlalchemy.orm import Session

from app.models.source import Source
from app.models.document import Document
from app.models.event import Event
from app.models.processing_job import ProcessingJob
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

    def fetch_feed(self, feed_url: str) -> Optional[feedparser.FeedParserDict]:
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                headers = {"User-Agent": "FlashFactsIngestionWorker/1.0"}
                resp = client.get(feed_url, headers=headers)
                if resp.status_code == 200:
                    return feedparser.parse(resp.text)
                else:
                    logger.warning(f"HTTP {resp.status_code} fetching feed {feed_url}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            return None

    def ingest_source(self, source: Source) -> Dict[str, int]:
        stats = {
            "discovered": 0,
            "skipped": 0,
            "documents_stored": 0,
            "events_created": 0,
            "events_deduplicated": 0
        }

        logger.info(f"Ingestion started for source: '{source.name}' (ID: {source.id})")
        feed = self.fetch_feed(source.feed_url)
        if not feed or not hasattr(feed, "entries"):
            logger.warning(f"Failed or empty feed for source '{source.name}'")
            source.last_ingested_at = datetime.now(timezone.utc)
            self.db.commit()
            return stats

        stats["discovered"] = len(feed.entries)

        for entry in feed.entries:
            url = entry.get("link") or entry.get("id") or ""
            title = entry.get("title") or ""
            
            # Content extraction
            content = entry.get("summary") or ""
            if not content and "content" in entry and len(entry.get("content", [])) > 0:
                content = entry.get("content")[0].get("value", "")
            
            if not title and not content:
                continue

            pub_dt = self.parse_datetime(entry)
            content_hash = compute_content_hash(url, title, content)

            # 1. Check for duplicate document
            existing_doc = self.doc_repo.get_by_content_hash(content_hash)
            if existing_doc:
                stats["skipped"] += 1
                logger.debug(f"Skipping duplicate document content hash {content_hash}")
                continue

            # 2. Store Document
            doc_in = DocumentCreate(
                source_id=source.id,
                title=title,
                content=content,
                url=url,
                published_at=pub_dt,
                content_hash=content_hash
            )
            doc = self.doc_repo.create(doc_in)
            stats["documents_stored"] += 1

            # 3. Extract Event Candidate
            event_candidate = self.extractor.extract_event_candidate(doc, source)

            # 4. Check Event Deduplication
            existing_event = self.dedup.check_duplicate(event_candidate)
            if existing_event:
                # Link document to existing event
                self.event_repo.add_event_source(
                    event_id=existing_event.id,
                    document_id=doc.id,
                    source_id=source.id
                )
                stats["events_deduplicated"] += 1
                logger.debug(f"Event deduplicated and linked to event ID {existing_event.id}")
            else:
                # 5. AI Enrichment for New Event Candidate
                enrichment = self.ai_provider.enrich_event(
                    title=event_candidate["title"],
                    content=doc.content,
                    domain=event_candidate["domain"],
                    reliability_score=source.reliability_score
                )

                event_candidate["summary"] = enrichment.get("summary", event_candidate["summary"])
                event_candidate["domain"] = enrichment.get("classification", event_candidate["domain"])
                event_candidate["why_it_matters"] = enrichment.get("why_it_matters")
                event_candidate["importance_score"] = enrichment.get("importance_score", 50)
                event_candidate["classification_confidence"] = enrichment.get("classification_confidence", 1.0)
                event_candidate["ai_processed_at"] = datetime.now(timezone.utc)
                event_candidate["processing_status"] = "completed"

                event_in, _ = self.dedup.prepare_event_candidate(event_candidate)
                new_event = self.event_repo.create(event_in, document_id=doc.id)

                # Attach Entities if extracted
                entities_data = enrichment.get("entities", [])
                if entities_data:
                    self.event_repo.attach_entities(new_event.id, entities_data)

                stats["events_created"] += 1
                logger.debug(f"Created & AI-enriched new event ID {new_event.id}: '{new_event.title}'")

            # Mark document processed
            self.doc_repo.mark_processed(doc.id)

        # Update last_ingested_at on Source
        source.last_ingested_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(
            f"Ingestion completed for source '{source.name}': "
            f"Discovered={stats['discovered']}, StoredDocs={stats['documents_stored']}, "
            f"Skipped={stats['skipped']}, EventsCreated={stats['events_created']}, "
            f"EventsDeduped={stats['events_deduplicated']}"
        )
        return stats

    def ingest_all_enabled_sources(self) -> Dict[str, Any]:
        job = ProcessingJob(job_type="ingestion", status="running", items_processed=0)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        sources = self.source_repo.list_sources(enabled_only=True)
        total_discovered = 0
        total_stored = 0
        total_skipped = 0
        total_events = 0
        total_deduped = 0

        try:
            for source in sources:
                stats = self.ingest_source(source)
                total_discovered += stats["discovered"]
                total_stored += stats["documents_stored"]
                total_skipped += stats["skipped"]
                total_events += stats["events_created"]
                total_deduped += stats["events_deduplicated"]

            job.status = "completed"
            job.items_processed = total_stored
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()

        except Exception as e:
            logger.error(f"Ingestion job failed: {e}", exc_info=True)
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise e

        return {
            "job_id": job.id,
            "status": job.status,
            "sources_processed": len(sources),
            "documents_discovered": total_discovered,
            "documents_ingested": total_stored,
            "documents_skipped": total_skipped,
            "events_created": total_events,
            "events_deduplicated": total_deduped
        }
