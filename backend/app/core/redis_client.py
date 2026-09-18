import os
from typing import Optional


def get_redis():
    """
    Retorna cliente Redis si REDIS_URL está disponible y la conexión es válida.
    Retorna None si Redis no está configurado o falla conexión.
    """
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return None
    try:
        import redis
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None
