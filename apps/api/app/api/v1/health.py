from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db, verify_database_head
from app.core.config import settings
from app.core.cache import get_redis

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "environment": settings.APP_ENV
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connectivity failed: {str(e)}"
        )

    # In production and staging, verify database migration matches expected Alembic HEAD
    is_prod_or_staging = settings.APP_ENV in ("production", "prod", "staging")
    migration_status = "unverified (development)"
    if is_prod_or_staging:
        try:
            current_rev = verify_database_head(db.get_bind())
            migration_status = f"verified (HEAD: {current_rev})"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database migration readiness check failed: {str(e)}"
            )

    # Optional Redis fallback check
    redis_status = "unavailable (operating without cache)"
    try:
        r = get_redis()
        if r and r.ping():
            redis_status = "connected"
    except Exception:
        redis_status = "unavailable (operating without cache)"

    return {
        "status": "ready",
        "database": "connected",
        "migration": migration_status,
        "redis": redis_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
