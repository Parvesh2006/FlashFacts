# FlashFacts — API Design Documentation (Phase 1)

## 1. System Endpoints Overview

All REST API endpoints are prefixed with `/api/v1` except root health probes.

---

## 2. Endpoint Specifications

### Health & Readiness

#### `GET /health`
- **Description**: Basic health probe.
- **Response**: `200 OK`
  ```json
  {
    "status": "ok",
    "timestamp": "2026-08-18T21:34:00Z",
    "version": "1.0.0"
  }
  ```

#### `GET /ready`
- **Description**: Database connectivity probe.
- **Response**: `200 OK`
  ```json
  {
    "status": "ready",
    "database": "connected"
  }
  ```

---

### Sources Management

#### `GET /api/v1/sources`
- **Description**: List registered ingestion sources.
- **Query Params**:
  - `enabled`: `boolean` (optional)
- **Response**: `200 OK`
  ```json
  [
    {
      "id": 1,
      "name": "TechCrunch",
      "url": "https://techcrunch.com",
      "feed_url": "https://techcrunch.com/feed/",
      "source_type": "rss",
      "domain": "Technology",
      "reliability_score": 0.95,
      "enabled": true,
      "created_at": "2026-08-18T10:00:00Z"
    }
  ]
  ```

#### `POST /api/v1/sources`
- **Description**: Register a new news/RSS source.
- **Request Body**:
  ```json
  {
    "name": "MIT News",
    "url": "https://news.mit.edu",
    "feed_url": "https://news.mit.edu/rss/feed",
    "source_type": "rss",
    "domain": "Science",
    "reliability_score": 0.98,
    "enabled": true
  }
  ```
- **Response**: `201 Created`

#### `POST /api/v1/sources/ingest`
- **Description**: Trigger ingestion cycle on enabled sources.
- **Response**: `200 OK`
  ```json
  {
    "status": "completed",
    "sources_processed": 5,
    "documents_ingested": 42,
    "documents_skipped": 12,
    "events_created": 35
  }
  ```

---

### Events API

#### `GET /api/v1/events`
- **Description**: Query stored events with filtering and pagination.
- **Query Params**:
  - `domain` (string, optional): e.g. "AI", "Technology"
  - `date` (string YYYY-MM-DD, optional): Exact date query
  - `start_date` (string YYYY-MM-DD, optional): Range filter start
  - `end_date` (string YYYY-MM-DD, optional): Range filter end
  - `limit` (int, default 50, max 200)
  - `offset` (int, default 0)
- **Response**: `200 OK`
  ```json
  {
    "total": 120,
    "limit": 50,
    "offset": 0,
    "events": [
      {
        "id": 101,
        "title": "New Breakthrough in Quantum Computing Efficiency",
        "summary": "Researchers demonstrate 99.9% gate fidelity using superconducting qubits.",
        "domain": "Technology",
        "event_date": "2026-08-18",
        "published_at": "2026-08-18T14:30:00Z",
        "source_id": 1,
        "source_url": "https://example.com/article",
        "confidence_score": 1.0,
        "created_at": "2026-08-18T15:00:00Z"
      }
    ]
  }
  ```

#### `GET /api/v1/events/{id}`
- **Description**: Retrieve detailed event record by ID.
- **Response**: `200 OK` or `404 Not Found`

---

### Domains API

#### `GET /api/v1/domains`
- **Description**: Retrieve available domain taxonomy and event counts per domain.
- **Response**: `200 OK`
  ```json
  [
    { "domain": "AI", "count": 42 },
    { "domain": "Technology", "count": 88 },
    { "domain": "Politics", "count": 15 },
    { "domain": "Government", "count": 12 },
    { "domain": "Education", "count": 7 },
    { "domain": "Medical", "count": 23 },
    { "domain": "Engineering", "count": 19 },
    { "domain": "Science", "count": 54 },
    { "domain": "Economy", "count": 31 },
    { "domain": "Sports", "count": 9 },
    { "domain": "Environment", "count": 18 },
    { "domain": "International", "count": 27 },
    { "domain": "Defence", "count": 11 }
  ]
  ```

---

### Calendar API

#### `GET /api/v1/calendar`
- **Description**: Aggregate event counts per day and per domain for a given month.
- **Query Params**:
  - `month` (string YYYY-MM, required): Target month.
- **Response**: `200 OK`
  ```json
  {
    "month": "2026-08",
    "days": [
      {
        "date": "2026-08-18",
        "total": 25,
        "domains": {
          "AI": 4,
          "Politics": 3,
          "Sports": 7
        }
      }
    ]
  }
  ```
