"""
Redis Caching Helper.
"""
import json
import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger("app")

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis
        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.Redis.from_url(redis_url, decode_responses=True, socket_timeout=2.0)
        _redis_client.ping()
        return _redis_client
    except Exception as exc:
        logger.debug("Redis connection unavailable, operating without cache: %s", exc)
        return None


def cache_get(key: str) -> Optional[Any]:
    r = get_redis()
    if not r:
        return None
    try:
        data = r.get(key)
        if data:
            return json.loads(data)
    except Exception as exc:
        logger.debug("Cache get error for key %s: %s", key, exc)
    return None


def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    r = get_redis()
    if not r:
        return False
    try:
        r.setex(key, ttl, json.dumps(value))
        return True
    except Exception as exc:
        logger.debug("Cache set error for key %s: %s", key, exc)
        return False


def cache_delete(key: str) -> bool:
    r = get_redis()
    if not r:
        return False
    try:
        r.delete(key)
        return True
    except Exception as exc:
        logger.debug("Cache delete error for key %s: %s", key, exc)
        return False

