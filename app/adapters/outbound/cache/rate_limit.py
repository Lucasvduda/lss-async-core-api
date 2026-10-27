import time
from collections import defaultdict, deque

from app.infrastructure.config import get_settings

try:
    import redis.asyncio as redis
except ImportError:  # pragma: no cover
    redis = None  # type: ignore


class RateLimiter:
    """Redis when available; in-memory fallback for local/demo."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._memory: dict[str, deque[float]] = defaultdict(deque)
        self._redis = None

    async def connect(self) -> None:
        if redis is None:
            return
        try:
            client = redis.from_url(self._settings.redis_url, decode_responses=True)
            await client.ping()
            self._redis = client
        except Exception:
            self._redis = None

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()

    async def allow(self, key: str) -> bool:
        limit = self._settings.rate_limit_per_minute
        window = 60
        if self._redis is not None:
            pipe_key = f"rl:{key}"
            count = await self._redis.incr(pipe_key)
            if count == 1:
                await self._redis.expire(pipe_key, window)
            return count <= limit

        now = time.time()
        bucket = self._memory[key]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


rate_limiter = RateLimiter()
