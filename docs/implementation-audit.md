# FlashFacts Implementation Audit

Audit date: 2026-09-19

## Current Architecture

FlashFacts is an existing monorepo with a FastAPI backend in `apps/api`, a Next.js TypeScript frontend in `apps/web`, shared documentation in `docs`, evaluation fixtures in `evaluation`, and pytest coverage in `tests`.

Backend runtime:

- FastAPI application entrypoint: `apps/api/app/main.py`
- API router: `apps/api/app/api/router.py`
- SQLAlchemy ORM and session management: `apps/api/app/core/database.py`
- Alembic migrations: `apps/api/alembic/versions`
- PostgreSQL is the configured default database through `DATABASE_URL`; tests use in-memory SQLite.
- Redis helper exists in `apps/api/app/core/cache.py` and degrades to no-cache when Redis is unavailable.

Frontend runtime:

- Next.js App Router under `apps/web/app`
- TypeScript service clients under `apps/web/services`
- Product routes present: `/`, `/explore`, `/search`, `/calendar`, `/event/[id]`, `/exams`, `/ask`, `/settings`

Infrastructure:

- `docker-compose.yml` defines PostgreSQL, Redis, and API services.
- Docker Compose config renders, but the local Docker daemon was not reachable during this audit.

## Dependency Map

Primary backend dependencies:

- `Source` -> `Document` -> `Event` -> `EventSource`
- `Event` -> `EventEntity` -> `Entity`
- `Event` -> `EventLocation` -> `GeographicLocation`
- `Event` -> `EventRelation` -> `Event`
- `IngestionService` uses `SourceRepository`, `DocumentRepository`, `EventRepository`, `EventExtractorService`, `DeduplicationService`, and `AIProvider`.
- `ExamIntelligenceService` uses stored `Event` records and static `EXAM_DEFINITIONS`.
- `LocationService` seeds and queries `GeographicLocation`, extracts deterministic mentions, and links `EventLocation`.
- `EventRelationService` creates explicit relations and currently provides same-domain chronological fallback timelines.

Frontend dependencies:

- `apps/web/lib/api.ts` is the shared API client.
- `services/events.ts`, `calendar.ts`, `search.ts`, `domains.ts`, `sources.ts`, `exams.ts`, and `locations.ts` connect product views to backend endpoints.
- `event-detail-view.tsx` composes event provenance, locations, timeline, exam relevance, MCQs, and related event cards.

## Working Features

Verified:

- Backend automated tests passed: `63 passed, 1 warning` with `python -m pytest -q`.
- Frontend production build passed with `npm.cmd --prefix apps/web run build`.
- Docker Compose configuration rendered successfully with `docker compose config`.

Implemented and covered by code/tests:

- RSS ingestion service with retry/backoff for timeout, HTTP 429, and HTTP 5xx.
- Source failure isolation in ingestion.
- Malformed feed handling.
- Document deduplication by content hash.
- Event deduplication by title/date hash.
- Event-source provenance links through `event_sources`.
- Ingestion run and per-source metric models.
- Deterministic classification and enrichment fallback.
- Exam definitions for TNPSC Group 4, TNPSC Group 2, SSC CGL, SSC CHSL, UPSC CSE, RRB NTPC, and Banking.
- Deterministic exam relevance scoring.
- Deterministic MCQ fallback generation.
- Calendar, events, sources, domains, search, evaluation, exams, locations, and coverage routers are present.
- Geographic tables and services exist for a small canonical reference set.
- Event relations table and explicit relation creation service exist.
- Redis cache helper is optional and fails open.

## Broken Or Risky Features

Runtime verification gaps:

- `docker compose ps` failed because Docker was not reachable: daemon pipe `npipe:////./pipe/docker_engine` was missing.
- Docker emitted access-denied warnings while reading `C:\Users\Parvesh\.docker\config.json`.
- `curl.exe http://localhost:8000/health` failed because no API server was listening on port 8000.

Backend risks:

- `apps/api/app/api/v1/exams.py` defines `GET /exams` twice, creating duplicate route registration risk.
- `apps/api/app/services/ingestion.py` has duplicate datetime imports and currently updates `last_ingested_at` even for failed source fetches; `last_attempted_at` is not consistently updated.
- `apps/api/app/api/v1/events.py` uses a no-op `pass` branch for empty exam relevance instead of explicit behavior.
- `apps/api/app/services/ai_provider.py` exposes `generate_embedding`, but the fallback returns SHA-derived pseudo-vectors. These must not be represented as semantic embeddings.
- `EventRelationService.get_event_timeline` infers chronological context from same-domain events. This is useful context, but it is not evidence of explicit event lineage.
- `LocationService.get_location_events` only includes direct children, not deeper descendants.
- Geographic extraction uses simple substring matching, which can create false positives for short aliases such as `US`.
- Geographic coverage statistics are hardcoded by reference seed counts rather than computed from the current database.
- Cache invalidation is not implemented for location/tree caches after new reference data or event-location links are created.
- Health checks distinguish app and database readiness, but Redis status is not included.
- `Base.metadata.create_all()` runs during app lifespan even though Alembic migrations exist; this can hide migration drift in development.
- PostgreSQL-specific migration behavior has not been verified in this audit because Docker/PostgreSQL were unavailable.

Frontend risks:

- `apps/web/services/exams.ts` catches API failure and returns `[]`; this violates the required local exam fallback behavior.
- Event detail labels fallback MCQs as deterministic fallback in some places, but the exact requested label "Source-grounded deterministic MCQ" is not consistently shown.
- Explore/search filters do not yet expose country/state/district/city/exam filters.
- Related events shown on event detail are mostly categorical/domain related unless explicit backend relations are supplied.
- Several rendered strings contain mojibake characters such as `Â·`, indicating encoding cleanup is needed.

Documentation risks:

- Some docs claim final architecture and measured API latency without current verification in this audit.
- `README.md` still states an older test count of 23 passed, while the current suite has 63 passing tests.
- Prior-art and patent documents are placeholders and are not yet fully source-backed.
- Research documentation must clearly separate synthetic/offline benchmark results from real-world evaluation.

## Missing Features

- Full global and India administrative reference import architecture.
- Deep hierarchy traversal for locations.
- Location extraction provenance fields: source text span, matched alias, canonical location, confidence.
- Search filters for source, country, state, district, city, and exam.
- Explicit related-events endpoint and transparent relation scoring surface.
- Reproducible load tests under `docs/performance/` with actual results.
- Failure tests for Redis unavailable and database unavailable in a live environment.
- Redis cache invalidation strategy beyond TTL expiry.
- PostgreSQL migration upgrade/downgrade verification.
- Multi-replica API/load-balancer validation.
- Source coverage metrics that distinguish ingestion success from source reliability.
- Evidence-backed prior-art matrix with citations and confidence values.
- Complete `docs/deployment.md`, `docs/testing.md`, `docs/limitations.md`, and `docs/FINAL_PRODUCT_REPORT.md`.

## Baseline Verification Status

Commands executed:

```powershell
python -m pytest -q
```

Result: passed. `63 passed, 1 warning in 3.14s`.

```powershell
npm --prefix apps/web run build
```

Result: blocked by PowerShell execution policy for `npm.ps1`.

```powershell
npm.cmd --prefix apps/web run build
```

Result: passed. Next.js compiled successfully, TypeScript finished, and 10 static pages generated.

```powershell
docker compose config
```

Result: passed with warnings about Docker config access and obsolete Compose `version`.

```powershell
docker compose ps
```

Result: failed because the Docker daemon was not reachable.

```powershell
curl.exe http://localhost:8000/health
```

Result: failed because no API server was listening on localhost:8000.

## Post-Audit Fix Verification

Small remediation changes were applied after the baseline:

- Restored frontend fallback exam data for all seven required exams.
- Removed duplicate backend `GET /api/v1/exams` route registration.
- Labeled fallback MCQs as source-grounded deterministic MCQs in the frontend.
- Preserved source `last_attempted_at` separately from successful `last_ingested_at`.
- Made event-location lookup repeat-safe.
- Made location event retrieval include deeper descendants.
- Computed coverage breakdown from stored location rows instead of hardcoded counts.
- Removed SHA-derived pseudo-embedding output from the fallback AI provider.

Post-change verification:

```powershell
python -m pytest -q
```

Result: passed. `67 passed, 1 warning in 3.43s`.

```powershell
npm.cmd --prefix apps/web run build
```

Result: passed. Next.js compiled successfully, TypeScript finished, and 10 static pages generated.

```powershell
docker compose config
```

Result: passed with the same Docker config access and obsolete `version` warnings.

```powershell
docker compose ps
```

Result: failed because Docker API access was denied at `npipe:////./pipe/docker_engine`.

Live API notes:

- `http://localhost:8000/health` returned 200, but this appeared to be an already-running older API process because `/api/v1/locations`, `/api/v1/locations/tree`, and `/api/v1/coverage` returned 404 there.
- A current-code verification API was started on `http://127.0.0.1:8001` with a temporary SQLite database. On that current-code server, `/health`, `/api/v1/locations`, `/api/v1/locations/tree`, `/api/v1/coverage`, and `/api/v1/exams` all returned 200.

## Proposed Changes

Immediate regression fixes:

1. Restore frontend local exam fallback data.
2. Remove duplicate `GET /api/v1/exams` backend route.
3. Make fallback MCQ labeling explicit as source-grounded deterministic MCQ.
4. Fix ingestion timestamps so attempts and successful ingestions are distinguishable.
5. Compute coverage breakdown from database contents.
6. Remove or clearly relabel pseudo-embedding behavior so it cannot be mistaken for semantic embeddings.

Next hardening phase:

1. Add bounded geographic and exam filters to search and events APIs.
2. Add recursive location descendant queries.
3. Add cache invalidation helpers for location caches.
4. Add Redis status to readiness without making Redis critical.
5. Add tests for duplicate exam route behavior, exam fallback contract, recursive locations, and coverage computation.
6. Verify Alembic upgrade/downgrade against PostgreSQL once Docker is available.

Research/documentation phase:

1. Replace placeholder prior-art docs with cited, source-backed comparisons.
2. Create real performance/load-test scripts and store actual outputs under `docs/performance/`.
3. Create final deployment, testing, limitations, and product report docs based only on verified behavior.
