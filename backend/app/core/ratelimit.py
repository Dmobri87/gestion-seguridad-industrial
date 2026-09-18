import os
import time
import logging
from typing import Optional

import redis

logger = logging.getLogger(__name__)

_REDIS_CLIENT: Optional[redis.Redis] = None


def _get_redis() -> Optional[redis.Redis]:
    global _REDIS_CLIENT
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT

    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return None

    try:
        _REDIS_CLIENT = redis.Redis.from_url(redis_url, decode_responses=True)
        _REDIS_CLIENT.ping()
        return _REDIS_CLIENT
    except Exception:
        logger.exception("No se pudo conectar a Redis para rate limiting")
        _REDIS_CLIENT = None
        return None


def check_rate_limit_redis(key: str, max_attempts: int, window_seconds: int) -> bool:
    """
    Rate limit basado en Redis.
    Retorna True si se permite, False si excede.
    """
    client = _get_redis()
    if not client:
        return True


def is_redis_enabled() -> bool:
    return _get_redis() is not None

    now = int(time.time())
    window_start = now - window_seconds

    # Usar sorted set para contar eventos en ventana
    try:
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds + 5)
        _, _, count, _ = pipe.execute()
        return count <= max_attempts
    except Exception:
        logger.exception("Error en rate limiting Redis")
        return True
