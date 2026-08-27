# FlashFacts — Architecture Documentation (Phase 1)

## 1. System Topology

```
                         FLASHFACTS
                             │
              ┌──────────────┼──────────────┐
              │              │              │
          CURRENT          CALENDAR       ASK AI
          AFFAIRS           TIMELINE        RAG
          (Phase 2)        (Phase 1 API)  (Phase 2)
              │              │              │
              └──────────────┼──────────────┘
                             │
                          FASTAPI (apps/api)
                             │
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
          PostgreSQL      pgvector       Redis
          (Phase 1 DB)   (Phase 2)     (Phase 1 Cache/Opt)
              ↑
              │
       INGESTION WORKER
              │
      ┌───────┼────────┐
      ↓       ↓        ↓
     RSS    APIs   Official Sources
              │
              ↓
          AI PROCESSOR (Phase 1 Rule Baseline -> Phase 2 LLM)
              │
       ┌──────┼───────┐
       ↓      ↓       ↓
    Classify  NER   Summary
       │      │       │
       └──────┼───────┘
              ↓
          EVENT STORE
```

---

## 2. Directory Structure

```
apps/api/
  app/
    main.py                   # FastAPI Application Entrypoint & Middleware
    core/
      config.py               # Application Settings & Env Vars via Pydantic
      database.py             # SQLAlchemy Session & Engine Management
      logging.py              # Structured JSON/Console Logging Configuration
    api/
      router.py               # Main API Router
      v1/                     # Version 1 API Endpoints
        health.py             # Health check & Readiness probes
        events.py             # Event listing & detail endpoints
        domains.py            # Domain list & domain metrics
        calendar.py           # Monthly date/domain event count matrix
        sources.py            # Source registry CRUD & triggering ingestion
    models/                   # SQLAlchemy ORM Database Models
      source.py
      document.py
      event.py
      processing_job.py
    schemas/                  # Pydantic Request/Response Models
      source.py
      document.py
      event.py
      calendar.py
    services/                 # Business Logic & Pipeline Services
      ingestion.py            # RSS/Feed parsing & document normalization
      extraction.py           # Document -> Event Candidate conversion
      classification.py       # Baseline Rule-based Domain Classifier
      deduplication.py        # Hash & title/URL deduplication engine
      calendar.py             # Calendar aggregation builder
    repositories/             # Database Access Objects
      source_repository.py
      document_repository.py
      event_repository.py
    workers/                  # Async Ingestion Task Workers
      ingestion_worker.py     # Background / CLI Ingestion runner
    utils/                    # Utility Functions
      hashing.py              # SHA256 & text normalization helpers
```

---

## 3. Data Processing Flow

1. **Trigger**: Ingestion worker runs periodically or via API trigger.
2. **Fetch**: `IngestionService` queries enabled sources from `SourceRepository`. Fetch feed via `httpx` and `feedparser`.
3. **Normalize & Hash**: For each item, normalize title/content, generate `content_hash = SHA256(url + title + content)`.
4. **Deduplicate Document**: Query `DocumentRepository` for existing `content_hash`. Skip if duplicate.
5. **Extract Event**: `EventExtractorService` parses date, title, summary, domain candidates.
6. **Classify Domain**: `DomainClassifierService` maps content keywords to one of 13 primary domains.
7. **Deduplicate Event**: `DeduplicationService` generates `dedup_hash` and checks `EventRepository`. If match found, links existing event via `event_sources` table.
8. **Store**: Persist event to `EventStore` in PostgreSQL. Log processing stats to `ProcessingJob`.
