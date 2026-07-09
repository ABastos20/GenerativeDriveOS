from __future__ import annotations

from jarvis.memory.research_limits import InMemoryCounter, ResearchLimitConfig, ResearchLimiter, RedisCounter


def test_research_limiter_allows_within_limit() -> None:
    limiter = ResearchLimiter(ResearchLimitConfig(hourly_limit=2, cost_cap_usd=1.0))
    allowed1, count1 = limiter.check_limit("user1")
    allowed2, count2 = limiter.check_limit("user1")
    assert allowed1 is True and allowed2 is True
    assert count1 == 1 and count2 == 2


def test_research_limiter_blocks_after_limit() -> None:
    limiter = ResearchLimiter(ResearchLimitConfig(hourly_limit=1))
    limiter.check_limit("user2")
    allowed, count = limiter.check_limit("user2")
    assert allowed is False
    assert count == 2


def test_research_limiter_cost_cap() -> None:
    limiter = ResearchLimiter(ResearchLimitConfig(cost_cap_usd=0.5))
    assert limiter.check_cost(0.25) is True
    assert limiter.check_cost(0.75) is False


def test_redis_counter_fallback_to_inmemory_when_unavailable(monkeypatch) -> None:
    class _FakeRedis:
        def __init__(self, *args, **kwargs) -> None:
            raise ConnectionError("Redis unavailable")

    monkeypatch.setattr("jarvis.memory.research_limits.redis.Redis", _FakeRedis)
    cfg = ResearchLimitConfig(redis_url="redis://localhost:6379", hourly_limit=1)
    limiter = ResearchLimiter(cfg)
    allowed, _ = limiter.check_limit("user3")
    assert allowed is True
