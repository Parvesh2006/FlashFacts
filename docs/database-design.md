# FlashFacts — Database Design (Phase 1)

## 1. Schema Overview

The database is built on PostgreSQL with SQLAlchemy 2.0 ORM and Alembic migrations.

---

## 2. Table Definitions

### 2.1 `sources`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto Increment | Unique Source Identifier |
| `name` | String(255) | NOT NULL | Human readable source name |
| `url` | String(512) | NOT NULL | Source main URL |
| `feed_url` | String(512) | NOT NULL, UNIQUE | RSS/Atom feed endpoint URL |
| `source_type` | String(50) | NOT NULL, Default 'rss' | Feed type (rss, api, official) |
| `domain` | String(100) | NOT NULL, Default 'General' | Primary domain category |
| `reliability_score` | Float | NOT NULL, Default 1.0 | Score between 0.0 and 1.0 |
| `enabled` | Boolean | NOT NULL, Default True | Whether source is active |
| `created_at` | DateTime(tz) | NOT NULL, Default UTC | Registration timestamp |
| `updated_at` | DateTime(tz) | NOT NULL, Default UTC | Last update timestamp |

**Indexes**: `ix_sources_domain`, `ix_sources_enabled`

---

### 2.2 `documents`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto Increment | Unique Document Identifier |
| `source_id` | Integer | FK -> sources.id | Parent source reference |
| `title` | String(512) | NOT NULL | Raw/normalized document title |
| `content` | Text | NOT NULL | Cleaned text body/summary |
| `url` | String(1024) | NOT NULL | Canonical document web URL |
| `content_hash` | String(64) | NOT NULL, UNIQUE | SHA-256 hash of content |
| `published_at` | DateTime(tz) | NOT NULL | Source publication time |
| `crawled_at` | DateTime(tz) | NOT NULL, Default UTC | System ingestion timestamp |
| `processed` | Boolean | NOT NULL, Default False | Extraction pipeline status |

**Indexes**: `ix_documents_source_id`, `ix_documents_content_hash`, `ix_documents_published_at`

---

### 2.3 `events`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto Increment | Unique Event Identifier |
| `title` | String(512) | NOT NULL | Event title |
| `summary` | Text | NOT NULL | Concise event summary |
| `domain` | String(100) | NOT NULL | Classified domain name |
| `event_date` | Date | NOT NULL | Date event occurred / reported |
| `published_at` | DateTime(tz) | NOT NULL | Publication timestamp |
| `source_id` | Integer | FK -> sources.id | Primary source reference |
| `source_url` | String(1024) | NOT NULL | Source URL link |
| `confidence_score` | Float | NOT NULL, Default 1.0 | Classification/extraction score |
| `dedup_hash` | String(64) | NOT NULL, UNIQUE | SHA-256 hash for title+date dedup |
| `created_at` | DateTime(tz) | NOT NULL, Default UTC | Creation timestamp |
| `updated_at` | DateTime(tz) | NOT NULL, Default UTC | Update timestamp |

**Indexes**: `ix_events_event_date`, `ix_events_domain`, `ix_events_published_at`, `ix_events_source_id`, `ix_events_dedup_hash`

---

### 2.4 `event_sources`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto Increment | Unique relation record |
| `event_id` | Integer | FK -> events.id | Target event |
| `document_id` | Integer | FK -> documents.id | Linked document |
| `source_id` | Integer | FK -> sources.id | Source entity |
| `created_at` | DateTime(tz) | NOT NULL, Default UTC | Relationship timestamp |

**Indexes**: `ix_event_sources_event_id`, `ix_event_sources_document_id`

---

### 2.5 `processing_jobs`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto Increment | Processing Job Identifier |
| `job_type` | String(50) | NOT NULL | Job type ('ingestion', 'extraction') |
| `status` | String(50) | NOT NULL | Status ('pending', 'running', 'completed', 'failed') |
| `items_processed` | Integer | NOT NULL, Default 0 | Count of items processed |
| `error_message` | Text | Nullable | Error trace details |
| `started_at` | DateTime(tz) | NOT NULL, Default UTC | Job start time |
| `completed_at` | DateTime(tz) | Nullable | Job completion time |
