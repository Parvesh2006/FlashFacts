# FLASHFACTS — Real-Time Current Affairs Intelligence Platform

## Overview
FlashFacts is a current-affairs intelligence platform. It features a production FastAPI backend service coupled with a modern Next.js TypeScript web application. The platform ingests news feeds date-by-date, normalizes content, classifies events into core domains, deduplicates records, and provides interactive analytics, calendar tracking, and explorer interfaces.

---

## 🏗️ Architecture & Directory Structure

```
c:\FlashFacts\
├── apps/
│   ├── api/                          # Phase 1 FastAPI Backend Engine
│   │   ├── app/
│   │   │   ├── main.py               # FastAPI entrypoint & CORS middleware
│   │   │   ├── core/                 # Config, DB connection, logging
│   │   │   ├── api/                  # V1 REST API Routers
│   │   │   ├── models/               # SQLAlchemy ORM Data Models
│   │   │   ├── schemas/              # Pydantic V2 Request/Response Schemas
│   │   │   ├── services/             # Ingestion, Extraction, Classification, Dedup, Calendar
│   │   │   ├── repositories/         # Database access layer
│   │   │   └── workers/              # Standalone Ingestion Worker
│   │   ├── alembic/                  # Database migration scripts
│   │   └── pytest.ini                # Pytest configuration
│   └── web/                          # Phase 2 Next.js Web Application
│       ├── app/                      # Next.js App Router (Dashboard, Explore, Calendar, Detail, Search, Ask, Exams, Settings)
│       ├── components/               # Layout, Dashboard, Events, Calendar, Domains, Common UI
│       ├── lib/                      # Centralized API client & utilities
│       ├── services/                 # Events, Domains, Calendar, Sources, Search, Ask, Exams
│       ├── types/                    # TypeScript data models matching FastAPI Pydantic schemas
│       └── .env.local                # Frontend API environment variables
├── docs/                             # Architecture & Requirements Documentation
├── tests/                            # Pytest backend test suite (23 passed)
├── docker-compose.yml                # Docker compose (PostgreSQL, Redis, API)
├── Dockerfile                        # API Docker container setup
└── README.md                         # Project documentation
```

---

## 🌐 Available Frontend Pages

| Page Route | Description | API Integration |
|---|---|---|
| `/` | **Dashboard** | `GET /api/v1/domains`, `GET /api/v1/events` |
| `/explore` | **Event Explorer** | `GET /api/v1/events` (domain, date, start_date, end_date, limit, offset) |
| `/calendar` | **Interactive Calendar** | `GET /api/v1/calendar?month=YYYY-MM`, `GET /api/v1/events?date=YYYY-MM-DD` |
| `/event/[id]` | **Event Detail View** | `GET /api/v1/events/{id}`, `GET /api/v1/events` |
| `/search` | **Keyword Search** | Query search abstraction + client-side/backend search endpoint |
| `/ask` | **Ask FlashFacts AI** | Conversational UI + Phase 3 RAG integration connection notice |
| `/exams` | **Exam Mode** | Exam target selection (TNPSC, UPSC, SSC, Banking, RRB) |
| `/settings` | **System Settings** | `GET /health`, `GET /ready`, `GET /api/v1/sources` |

---

## ⚡ Environment Variables

### Frontend Configuration (`apps/web/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 How to Run the Project

### 1. Run the FastAPI Backend Server
```bash
cd apps/api
pip install -r ../../requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Run the Next.js Frontend Server
```bash
cd apps/web
npm install
npm run dev
```

The web interface will be available at [http://localhost:3000](http://localhost:3000).

---

## 🧪 Testing & Build Validation

### Run Backend Test Suite
```bash
pytest -v
```

### Build Frontend Production Application
```bash
cd apps/web
npm run build
```

## Reliable Ingestion

Ingestion follows this flow:

`Source -> Fetch -> Retry -> Parse -> Normalize -> Document deduplication -> Event extraction -> Event deduplication -> Provenance -> Database`

The manual trigger is `POST /api/v1/sources/ingest`, or the developer report command:

```bash
python tools/run_ingestion_test.py
```

The scheduler is disabled by default. Configure it in `.env`:

```env
INGESTION_ENABLED=false
INGESTION_INTERVAL_MINUTES=30
INGESTION_REQUEST_TIMEOUT=15
INGESTION_MAX_RETRIES=3
INGESTION_RETRY_BACKOFF=1
INGESTION_USER_AGENT=FlashFacts/0.1 (+https://example.com)
```

Retries apply to timeouts, connection failures, HTTP 429, and HTTP 5xx responses. Each source records its last attempt and error, and a failed source does not stop other enabled sources. Feed GUIDs and normalized content hashes keep repeated runs idempotent while event-source links preserve provenance.

Apply database migrations with `alembic upgrade head` before using an existing database. Automated tests use mocked feeds and do not depend on live websites.

The Day 1 live validation used the three development sources seeded by `tools/init_db.py` on 2026-09-04. The first run attempted 3 sources, succeeded for 3, discovered and inserted 57 documents, created 57 events, and completed in 7.87 seconds. The repeat run attempted 3 sources, succeeded for 3, skipped 57 duplicate documents, created 0 events, and completed in 2.39 seconds.

## Event Intelligence (Day 2)

New events can be enriched through the existing `AIProvider` abstraction. The fallback provider is deterministic and requires no API key; the OpenAI provider is selected only when `AI_PROVIDER=openai` and `AI_API_KEY` are configured. Provider failures and invalid responses fall back without breaking ingestion or event APIs.

Enrichment output is validated with a Pydantic contract. Scores are constrained to 0-100, confidence to 0-1, summaries and explanations are length-limited, and entities are limited to known types. Entity names are checked against the source text before persistence, and normalized entity matching prevents duplicate records.

The fallback importance score is explainable: it starts from a neutral baseline, adds domain significance and bounded impact-keyword signals, then applies the source reliability score and clamps the result to 0-100. It does not invent dates, claims, or unsupported entities.

Processing states are `pending`, `processing`, `completed`, and `failed`. Completed events are skipped by default. Enrich a batch from the command line or API:

```bash
python tools/enrich_events.py --limit 20
python tools/enrich_events.py --limit 20 --force
```

```text
POST /api/v1/events/enrich?limit=20&force=false
```

Batch results report requested, processed, succeeded, failed, fallback, and skipped counts. `AI_MAX_INPUT_CHARS` limits content sent to a provider. These counts and event fields support later measurement of enrichment latency, fallback rate, score distribution, confidence, entity counts, and duplicate-entity rate.

## Evaluation & Observability (Day 3)

FlashFacts now includes a deterministic evaluation layer for research and reproducibility. The benchmark dataset lives at `evaluation/benchmark_events.json` and uses synthetic benchmark entries explicitly marked as synthetic to avoid claiming real-world facts. Every item includes an `id`, title, content, expected domain, expected event type, expected importance score, and expected entity list.

The evaluator measures:

- Classification accuracy
- Event-type accuracy
- Named-entity precision, recall, and F1 using normalized matching with duplicate entity de-duplication
- Importance-score MAE and RMSE
- Enrichment success, fallback, failure, and skipped rates
- Latency in milliseconds for average and median durations

The evaluation service is implementation-agnostic and can be reused in tests or by downstream research tooling. It reads a dataset, compares expected labels against a prediction payload, and returns a stable JSON structure. The evaluation summary endpoint is available at `GET /api/v1/evaluation/summary`.

### Benchmark dataset and methodology

- Dataset file: `evaluation/benchmark_events.json`
- Structured benchmark items: each row is deterministic and contains expected labels
- Entity matching: names are normalized to lowercase, whitespace-normalized, and compared without case sensitivity
- Duplicate entities are removed before scoring so repeated labels do not inflate precision or recall
- Deterministic output: metrics are based only on input data and stored predictions, not current time values except metadata timestamps written by the CLI

### Run evaluation

```bash
python tools/evaluate_events.py
python tools/evaluate_events.py --dataset evaluation/benchmark_events.json
python tools/evaluate_events.py --output evaluation/results.json
```

The CLI prints human-readable metrics and writes a JSON result file under `evaluation/results.json` when requested.

### Interpreting results

- Accuracy should be read as a percentage over valid benchmark rows only.
- Empty or malformed datasets return zeroed metrics rather than throwing an exception so the evaluation pipeline remains resilient.
- A successful enrichment is counted when processing completes without fallback. Fallback and failure rates are tracked separately for observability research.
- Results are intended for internal benchmarking and model comparison, not for proving real-world event accuracy without a vetted ground-truth dataset.

### Limitations

- The bundled benchmark is synthetic by design to keep the project deterministic and offline-safe.
- It does not represent a production ground-truth dataset for live event claims.
- Real-world evaluation should add curated, reviewed benchmark corpora over time.

---

## 📡 Backend API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health probe |
| `GET` | `/ready` | Database readiness check |
| `GET` | `/api/v1/sources` | List all registered permitted sources |
| `POST` | `/api/v1/sources` | Register a new RSS feed |
| `POST` | `/api/v1/sources/ingest` | Trigger feed ingestion cycle |
| `GET` | `/api/v1/events` | List events with filters (`domain`, `date`, `start_date`, `end_date`, `limit`, `offset`) |
| `GET` | `/api/v1/events/{id}` | Single event record details |
| `GET` | `/api/v1/domains` | List 13 core domain counts |
| `GET` | `/api/v1/calendar` | Monthly event breakdown matrix (`?month=YYYY-MM`) |
