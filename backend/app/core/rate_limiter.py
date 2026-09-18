import time
from collections import defaultdict
from typing import Optional


class RateLimiter:
    """
    Sliding window rate limiter.
    Usa Redis si está disponible, fallback a memoria.
    """

    def __init__(self, redis_client: Optional[object] = None):
        self.redis = redis_client
        self._memory: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        if self.redis is not None:
            try:
                return self._redis_check(key, max_attempts, window_seconds)
            except Exception:
                return self._memory_check(key, max_attempts, window_seconds)
        return self._memory_check(key, max_attempts, window_seconds)

    def _redis_check(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds + 1)
        results = pipe.execute()
        return int(results[2]) <= max_attempts

    def _memory_check(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        self._memory[key] = [t for t in self._memory[key] if t > window_start]
        self._memory[key].append(now)
        return len(self._memory[key]) <= max_attempts

    def reset(self, key: str):
        if self.redis is not None:
            try:
                self.redis.delete(key)
            except Exception:
                pass
        self._memory.pop(key, None)


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def init_rate_limiter(redis_client=None):
    global _rate_limiter
    _rate_limiter = RateLimiter(redis_client)
