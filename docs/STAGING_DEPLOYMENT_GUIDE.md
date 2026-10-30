# FlashFacts — Staging & Production Deployment Guide

This guide details the procedure for deploying the **FlashFacts** platform (Next.js frontend and FastAPI backend) to staging and production environments, including database migrations, scheduler isolation, and verification.

---

## 1. Architecture Overview

```
                      +-----------------------------+
                      |   Vercel Edge Network       |
                      |   (Next.js Web Frontend)    |
                      +--------------+--------------+
                                     |
                                     | HTTPS (REST API)
                                     v
                      +-----------------------------+
                      |  Managed Container Host     |
                      |  (Render / Railway / ECS)   |
                      |  FastAPI Backend Service    |
                      |  INGESTION_ENABLED=False    |
                      +-------+-------------+-------+
                              |             |
           +------------------+             +------------------+
           |                                                   |
           v                                                   v
+------------------------+                           +------------------------+
| Managed PostgreSQL     |                           | Hosted Redis (Optional)|
| (Neon / Supabase / RDS)|                           | (Upstash / Redis Cloud)|
+-----------+------------+                           +------------------------+
            ^
            |
+-----------+--------------------+
| Singleton Ingestion Worker     |
| (1 Container / Railway Replica)|
| INGESTION_ENABLED=True         |
+--------------------------------+
```

The application is architected into two decoupled runtime services:
1. **API Web Service (`FastAPI`)**: Handles user HTTP traffic, authentication, mock examinations, syllabus progress, and AI queries. Scalable across multiple workers or instances with `INGESTION_ENABLED=False`.
2. **Ingestion Worker Service (`Python daemon`)**: Executes as a dedicated singleton process to poll configured RSS news feeds without concurrency collisions.

---

## 2. Managed PostgreSQL Setup

1. **Provision Database**:
   - Supported versions: PostgreSQL 14, 15, or 16 (e.g. Neon Serverless, Supabase, AWS RDS, Render PostgreSQL).
   - Ensure SSL mode is enabled (`sslmode=require`).
2. **Connection String Format**:
   - FlashFacts automatically normalizes both `postgres://` and `postgresql://` URI schemes to `postgresql+psycopg2://`.
   - Example template: `postgresql://<user>:<password>@<host>:<port>/<dbname>?sslmode=require`
3. **Connection Pooling**:
   - The SQLAlchemy engine enables `pool_pre_ping=True` by default, automatically reconnecting dropped or idle connections without application errors.

---

## 3. Database Migration Procedure (Alembic)

> [!IMPORTANT]
> Always execute Alembic migrations **before** starting the web API or worker services. Do not rely on `Base.metadata.create_all()` in staging or production.

### Initial Migration (Blank Database)
Run the migration command from the `apps/api` directory:
```bash
cd apps/api
alembic upgrade head
```

### Automated Deployment Release Phase
- **Railway**: Set the **Pre-Deploy / Release Command** to:
  ```bash
  cd apps/api && alembic upgrade head
  ```
- **Render**: Configure the **Pre-Deploy Command** in `render.yaml`:
  ```bash
  cd apps/api && alembic upgrade head
  ```
- **Docker Compose / Direct Container**:
  The default `Dockerfile` executes migrations prior to starting Uvicorn:
  ```dockerfile
  CMD ["sh", "-c", "cd apps/api && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
  ```

### Seeding Official Exam Data (One-Time Setup)
After running migrations on a fresh staging database, seed official past question papers and syllabus questions:
```bash
python -m scripts.sync_official_pyq_papers
python -m scripts.seed_all_questions
```

---

## 4. API & Worker Runtime Commands

### 4.1 Web API Service
- **Command**:
  ```bash
  cd apps/api && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
  ```
- **Container Environment Flags**:
  - `APP_ENV=staging` (or `production`)
  - `INGESTION_ENABLED=False`
  - `SECRET_KEY=<generate-secure-64-byte-secret>`
  - `CORS_ORIGINS=https://staging.flashfacts.app,https://flashfacts-staging.vercel.app`

### 4.2 Dedicated Ingestion Worker
- **Continuous Scheduled Daemon Command**:
  ```bash
  cd apps/api && python -m app.workers.ingestion_worker --loop --interval 30
  ```
- **Single-Cycle Cron Job Command** (for periodic platforms or cron):
  ```bash
  cd apps/api && python -m app.workers.ingestion_worker
  ```
- **Worker Environment Flags**:
  - `APP_ENV=staging`
  - `INGESTION_ENABLED=True`
  - `INGESTION_INTERVAL_MINUTES=30`
  - `INGESTION_FRESHNESS_HOURS=72`

> [!TIP]
> Guaranteeing Singleton Execution: Ensure your cloud platform is configured to run exactly **1 replica / instance** of the worker service (`scale: 1`).

---

## 5. Frontend Deployment on Vercel

1. **Project Root**: `apps/web`
2. **Framework Preset**: Next.js
3. **Build Command**: `npm run build`
4. **Output Directory**: `.next`
5. **Environment Variables on Vercel**:
   - `NEXT_PUBLIC_API_URL`: Public HTTPS URL of the deployed FastAPI backend (e.g. `https://api-staging.flashfacts.app` without trailing slash).
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID`: Your Google OAuth 2.0 Web Client ID.

### Google OAuth Configuration
In the Google Cloud Console (APIs & Services > Credentials):
- **Authorized JavaScript Origins**:
  - `https://staging.flashfacts.app`
  - `https://flashfacts-staging.vercel.app`
  - `http://localhost:3000` (for local development)
- **Authorized Redirect URIs**:
  - `https://staging.flashfacts.app`
  - `https://flashfacts-staging.vercel.app`

---

## 6. Environment Variable Checklist

| Variable Name | Required Service | Example / Format | Purpose |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | API, Worker | `staging` or `production` | Enables strict security, CORS, and migration validation. |
| `SECRET_KEY` | API, Worker | `openssl rand -hex 32` | 64+ char cryptographic key for JWT tokens. |
| `DATABASE_URL` | API, Worker | `postgresql://user:pass@host:5432/db?sslmode=require` | Connection to managed PostgreSQL database. |
| `REDIS_URL` | API, Worker (Optional) | `rediss://default:pass@host:6379` | Cache store (system gracefully operates if omitted). |
| `CORS_ORIGINS` | API | `https://staging.flashfacts.app,https://flashfacts.vercel.app` | Comma-separated list of trusted frontend client origins. |
| `INGESTION_ENABLED` | API, Worker | `false` on API, `true` on Worker | Decouples news ingestion scheduler from web API. |
| `INGESTION_INTERVAL_MINUTES` | Worker | `30` | Ingestion cycle frequency in minutes. |
| `INGESTION_FRESHNESS_HOURS` | Worker | `72` | Freshness threshold for inbound RSS feed articles. |
| `AI_PROVIDER` | API | `gemini` or `fallback` | LLM provider for current affairs synthesis and Ask AI. |
| `GEMINI_API_KEY` | API | `AIzaSy...` | API key for Google Gemini (if using Gemini provider). |
| `NEXT_PUBLIC_API_URL` | Frontend | `https://api-staging.flashfacts.app` | Base API URL consumed by the Next.js browser client. |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Frontend | `*.apps.googleusercontent.com` | Google OAuth Client ID for student sign-in. |

---

## 7. Health & Readiness Verification

After deployment, verify that services are healthy:

1. **Liveness Probe**:
   ```bash
   curl -i https://api-staging.flashfacts.app/health
   ```
   *Expected Response:*
   ```json
   {
     "status": "ok",
     "timestamp": "2026-10-30T10:00:00Z",
     "version": "1.0.0",
     "environment": "staging"
   }
   ```

2. **Readiness Probe**:
   ```bash
   curl -i https://api-staging.flashfacts.app/ready
   ```
   *Expected Response:*
   ```json
   {
     "status": "ready",
     "database": "connected",
     "redis": "connected",
     "timestamp": "2026-10-30T10:00:00Z"
   }
   ```
   *(If Redis is not configured, `"redis": "unavailable (operating without cache)"` will be returned with HTTP 200 status).*

---

## 8. Rollback Strategy

If a deployment fails verification:
1. **Frontend (Vercel)**:
   - Navigate to **Deployments** in the Vercel dashboard.
   - Click the three dots next to the previous known good deployment and select **Instant Rollback**.
2. **Backend (Container Host)**:
   - Re-deploy the previous image tag or rollback commit.
3. **Database Schema Rollback**:
   - If a migration caused an issue, downgrade to the specific previous revision:
     ```bash
     cd apps/api
     alembic downgrade -1
     ```

---

## 9. Preserving Local Development Environment

Local development remains completely unaffected:
- In `APP_ENV=development`, `SECRET_KEY` falls back to a development key automatically.
- `CORS_ORIGINS` defaults to `["http://localhost:3000", "http://localhost:8000"]`.
- `Base.metadata.create_all()` runs automatically on startup in development mode so new tables are created without manual migration runs.
- `docker-compose up` continues to work with local PostgreSQL and Redis containers.
