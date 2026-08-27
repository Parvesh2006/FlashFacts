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
├── tests/                            # Pytest backend test suite (12 passed)
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
