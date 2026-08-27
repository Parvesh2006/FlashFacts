# FlashFacts — Product Requirements Document (Phase 1)

## 1. Overview
FlashFacts is a real-time event aggregation and intelligence platform designed to ingest news, updates, and official announcements across multiple domains, organize them chronologically, and make them accessible via high-performance APIs and interactive interfaces.

Phase 1 focuses exclusively on establishing a resilient foundation:
- Backend infrastructure (FastAPI, SQLAlchemy, Alembic, PostgreSQL).
- Real-time RSS/source ingestion pipeline with document content hashing and duplicate avoidance.
- Deterministic rule-based event extraction and modular domain classification.
- Baseline event deduplication layer.
- Query APIs supporting domain, date range, calendar aggregation, and source management.

---

## 2. Core Functional Requirements

### 2.1 Source Registry
- Support configurable news feeds, RSS channels, and official API sources.
- Track source properties: name, URL, feed URL, source type, default domain, reliability score, and enablement flag.
- Dynamic source resolution without hardcoded source configurations.

### 2.2 Document Ingestion
- Concurrent fetching of RSS feeds and XML/JSON endpoints.
- Content normalization (stripping HTML, normalizing whitespace, title clean-up).
- SHA-256 content hashing to ensure idempotent ingestion.
- Rejection of duplicate documents based on content hash and source URL.

### 2.3 Event Extraction & Classification (Phase 1 Baseline)
- Extraction of event title, summary, event date, published timestamp, domain, source ID, and source URL from normalized documents.
- Baseline keyword/rule-based domain classifier covering 13 core domains:
  1. AI
  2. Technology
  3. Politics
  4. Government
  5. Education
  6. Medical
  7. Engineering
  8. Science
  9. Economy
  10. Sports
  11. Environment
  12. International
  13. Defence
- Modular architecture allowing Phase 2 LLM/vector-based classifier to override/extend the baseline classifier without interface changes.

### 2.4 Event Deduplication
- Multi-tier duplicate detection:
  1. Content hash matching against existing stored documents.
  2. Normalized title hash matching.
  3. Source URL matching.
  4. Exact date + title similarity matching.

### 2.5 API Specifications
- `GET /health` & `GET /ready`: System and DB readiness indicators.
- `GET /api/v1/events`: Filtered list of events (domain, date, start_date, end_date, pagination).
- `GET /api/v1/events/{id}`: Specific event detail.
- `GET /api/v1/domains`: Active domains with event counts.
- `GET /api/v1/calendar`: Monthly event counts broken down by date and domain map.
- `GET /api/v1/sources`: Source registry listing and stats.
- `POST /api/v1/sources`: Register new ingestion sources.
- `POST /api/v1/sources/ingest`: Trigger immediate feed ingestion run.

---

## 3. Non-Functional Requirements
- **Idempotency**: Ingestion jobs can run repeatedly without creating duplicate documents or events.
- **Modularity**: Services separated into crisp API, domain logic, repository, and ingestion worker boundaries.
- **Observability**: Structured JSON logging across ingestion cycles, event generation, and error conditions.
- **Extensibility**: Prepared interfaces for pgvector and LLM pipelines in Phase 2.
