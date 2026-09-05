from fastapi import APIRouter
from app.api.v1 import health, sources, events, domains, calendar, evaluation

api_router = APIRouter()

# Health endpoints at root level (/health, /ready)
api_router.include_router(health.router)

# V1 API Endpoints under /api/v1
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(sources.router)
v1_router.include_router(events.router)
v1_router.include_router(domains.router)
v1_router.include_router(calendar.router)
v1_router.include_router(evaluation.router)

api_router.include_router(v1_router)
