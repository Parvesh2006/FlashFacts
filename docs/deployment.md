# FlashFacts Deployment Notes

Last updated: 2026-09-19

## Current Deployment Shape

The intended local/container deployment is:

```text
Next.js Web
    |
FastAPI API
    |
PostgreSQL
    |
Redis cache
```

`docker-compose.yml` defines PostgreSQL, Redis, and the API container. The API is designed to be stateless, with persisted state in PostgreSQL and optional acceleration through Redis.

## Required Runtime Configuration

- `DATABASE_URL`
- `REDIS_URL`
- `APP_ENV`
- `CORS_ORIGINS`
- `INGESTION_ENABLED`
- `INGESTION_INTERVAL_MINUTES`
- `INGESTION_FRESHNESS_HOURS`

## Current Verification Status

- Compose config renders.
- Docker runtime startup was not verified because Docker API access was denied on this machine.
- A current-code FastAPI process was verified on port 8001 using SQLite for route checks.

## Production Cautions

- Run Alembic migrations before starting the API against an existing PostgreSQL database.
- Do not rely on `Base.metadata.create_all()` as a production migration strategy.
- Keep Redis optional; PostgreSQL remains the source of truth.
- Do not claim multi-replica load balancing until it is tested with multiple API processes against shared PostgreSQL/Redis.

