# FlashFacts — Production & Vercel Deployment Architecture Guide

This guide describes the complete production deployment architecture for the **FlashFacts** competitive examination platform, detailing frontend deployment on Vercel, persistent backend deployment, database management, PDF storage, authentication, security, and verification.

---

## 1. System Architecture Overview

FlashFacts is designed with a modern decoupled full-stack architecture:

1. **Frontend**: Next.js 15 (App Router, React 19, TypeScript, Tailwind CSS) deployed on **Vercel Edge/Serverless Network**.
2. **Backend**: FastAPI (Python 3.11+, SQLAlchemy 2.0, Pydantic v2) deployed on a persistent container service (e.g. AWS ECS, Render, Railway, or Google Cloud Run).
3. **Database**: Managed PostgreSQL 15+ (e.g., Neon Serverless Postgres, Supabase, or AWS RDS).
4. **Cache & Queue**: Managed Redis 7+ (e.g., Upstash Serverless Redis or Redis Cloud).
5. **PDF Document Storage**: Direct official portal streaming with persistent client-side IndexedDB caching and optional S3/Cloudflare R2 object storage for archived papers.

```
+--------------------+        HTTPS        +---------------------+
|   Next.js 15 App   | <=================> |   FastAPI Backend   |
| (Vercel Production)|                     | (Docker / Cloud Run)|
+--------------------+                     +---------------------+
         |                                            |
         | Client IndexedDB                           | SQLAlchemy 2.0
         v                                            v
+--------------------+                     +---------------------+
| Offline Cache (PDF)|                     | Managed PostgreSQL  |
| & PWA Shell Assets |                     | (Neon / Supabase)   |
+--------------------+                     +---------------------+
```

---

## 2. Vercel Frontend Deployment

### 2.1 Configuration
The Next.js application resides in `apps/web`. A `vercel.json` file at the root or under `apps/web` configures the build settings.

```json
{
  "framework": "nextjs",
  "rootDirectory": "apps/web",
  "buildCommand": "next build",
  "installCommand": "npm install"
}
```

### 2.2 Environment Variables (Vercel Dashboard)
Configure the following environment variables in **Vercel Project Settings > Environment Variables**:

| Variable Name | Description | Example Value |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Production FastAPI base endpoint | `https://api.flashfacts.in` |
| `NEXT_PUBLIC_APP_URL` | Production Frontend domain | `https://flashfacts.vercel.app` |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth Client ID | `12345-abc.apps.googleusercontent.com` |

---

## 3. Backend Deployment (FastAPI on Cloud Run / Railway / Docker)

Because FastAPI performs long-running RSS news ingestion, LLM streaming, and binary document verification, a persistent container host is recommended over ephemeral serverless execution.

### 3.1 Docker Container Deployment
Use the existing production multi-stage Dockerfile:
```bash
docker build -t flashfacts-api:latest -f Dockerfile .
docker run -d -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@neon.tech/flashfacts?sslmode=require" \
  -e REDIS_URL="rediss://default:token@upstash.io:6379" \
  -e SECRET_KEY="<production_secret_key>" \
  -e CORS_ORIGINS='["https://flashfacts.vercel.app"]' \
  flashfacts-api:latest
```

### 3.2 Database Migrations
Run Alembic migrations automatically during container startup or deployment pipelines:
```bash
cd apps/api && alembic upgrade head
```

### 3.3 PYQ PDF Curation & Ingestion
Execute the repeatable ingestion script to register and verify all official examination question papers:
```bash
python scripts/ingest_pyq_pdfs.py
```

---

## 4. Cross-Origin Resource Sharing (CORS)

Configure backend CORS in `.env` to authorize the Vercel production domain:
```env
CORS_ORIGINS=["https://flashfacts.vercel.app","https://www.flashfacts.in"]
```

FastAPI dynamically evaluates these origins via `app/core/config.py` and applies trusted headers (`Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`).

---

## 5. PDF Storage & Offline Caching Architecture

1. **Storage Integrity**: Production servers store verified PDFs in `data/pyq_pdfs/` or stream directly from authorized examination board portals (`tnpsc.gov.in`, `upsc.gov.in`, `ssc.gov.in`).
2. **Path Traversal Protection**: The endpoint `resolve_safe_pdf_path` strictly validates that resolved paths are contained within approved storage roots.
3. **MIME Validation**: Every stored document verifies `%PDF-1.4` magic byte signatures.
4. **Offline Persistence**: In the browser, documents are stored in IndexedDB (`FlashFacts_Offline_PYQs`), allowing aspirants to reopen papers offline without consuming Vercel serverless storage.

---

## 6. Production Verification Checklist

1. **Health Telemetry**:
   - `GET /health` returns `{"status": "ok"}`
   - `GET /ready` returns `{"status": "ready"}`
2. **Public Content Access**:
   - `GET /api/v1/pyqs/papers` returns 200 with all 8 verified papers.
   - `GET /api/v1/events` returns 200 without requiring auth.
3. **Dual Authentication**:
   - Google Sign-In with ID token verifies and issues JWT.
   - Traditional registration with username/password functions.
   - Guest data seamlessly merges into student profile upon registration.
4. **Offline Resilience**:
   - Service worker caches `/fact-jumper` and offline shell.
   - Downloaded question papers open offline from IndexedDB.

---

## 7. Rollback Procedures

If a deployment fails:
1. **Frontend**: In Vercel Dashboard, select **Deployments**, locate the last passing build, and click **Promote to Production** (instant zero-downtime rollback).
2. **Backend**: Re-deploy previous Docker tag or Git SHA.
3. **Database**: If a migration rollback is required:
   ```bash
   cd apps/api && alembic downgrade -1
   ```
