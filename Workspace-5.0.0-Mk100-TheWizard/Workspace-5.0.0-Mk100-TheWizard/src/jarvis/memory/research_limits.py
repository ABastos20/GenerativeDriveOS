"""Rate limiting and cost cap enforcement for research mode."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import redis

@dataclass
class ResearchLimitConfig:
    hourly_limit: int = 10
    cost_cap_usd: float = 2.0
    redis_url: str | None = None


class InMemoryCounter:
    def __init__(self) -> None:
        self._bucket: dict[str, list[float]] = {}

    def increment(self, key: str, ttl_seconds: int) -> int:
        now = time.time()
        window_start = now - ttl_seconds
        entries = [ts for ts in self._bucket.get(key, []) if ts >= window_start]
        entries.append(now)
        self._bucket[key] = entries
        return len(entries)


class RedisCounter(InMemoryCounter):
    """Redis-backed counter for rate limiting (time-windowed)."""

    def __init__(self, redis_url: str) -> None:
        super().__init__()
        redis_cls = getattr(redis, "Redis")
        if hasattr(redis_cls, "from_url"):
            self.client = redis_cls.from_url(redis_url)
        else:
            self.client = redis_cls(redis_url)

    def increment(self, key: str, ttl_seconds: int) -> int:  # pragma: no cover - external service
        now_ms = int(time.time() * 1000)
        window_start = now_ms - ttl_seconds * 1000
        pipe = self.client.pipeline()
        pipe.zadd(key, {now_ms: now_ms})
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.expire(key, ttl_seconds)
        _, _, count, _ = pipe.execute()
        return int(count)


class ResearchLimiter:
    """Lightweight hourly limiter and cost cap checker."""

    def __init__(self, config: ResearchLimitConfig, counter: Optional[InMemoryCounter] = None) -> None:
        self.config = config
        if counter:
            self.counter = counter
        elif config.redis_url:
            try:
                self.counter = RedisCounter(config.redis_url)
            except Exception:
                self.counter = InMemoryCounter()
        else:
            self.counter = InMemoryCounter()

    def check_limit(self, user_id: str) -> tuple[bool, int]:
        count = self.counter.increment(user_id, ttl_seconds=3600)
        return count <= self.config.hourly_limit, count

    def check_cost(self, projected_cost: float) -> bool:
        return projected_cost <= self.config.cost_cap_usd
