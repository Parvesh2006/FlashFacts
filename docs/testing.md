# FlashFacts Testing Notes

Last updated: 2026-09-19

## Verified Commands

```powershell
python -m pytest -q
```

Current result: `67 passed, 1 warning`.

```powershell
npm.cmd --prefix apps/web run build
```

Current result: passed.

```powershell
docker compose config
```

Current result: config renders, with warnings about Docker config access and obsolete Compose `version`.

## Not Fully Verified

- Docker runtime startup was not verified because Docker API access was denied.
- PostgreSQL Alembic upgrade/downgrade was not verified in this pass.
- Production load testing has not been run.
- Redis outage testing has not been run against a live stack.

## Current Test Coverage Areas

- Ingestion reliability and failure isolation
- Document and event deduplication
- Classification, enrichment, extraction, and evaluation helpers
- Event, source, domain, calendar, search, exam, MCQ, location, relation, and security validation paths

