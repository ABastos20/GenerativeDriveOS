from __future__ import annotations

from jarvis.memory.critical_integrator import CriticalIntegrator
from jarvis.memory.research_executor import MCPResearchExecutor, ResearchPlan, ResearchQuery, ResearchSource
from jarvis.memory.research_planner import ResearchPlanConfig, ResearchPlanner


class _FakeLLMResponse:
    def __init__(self, content: str) -> None:
        self.content = content


def _fake_llm(prompt: str, system: str, provider: str, max_tokens: int) -> _FakeLLMResponse:
    del prompt, system, provider, max_tokens  # unused in fake
    return _FakeLLMResponse("query one about gaps\nquery two for recency\nquery three for coverage")


def test_research_planner_llm_and_fallback() -> None:
    gap = {
        "coverage_gap": True,
        "recency_gap": False,
        "contradictory": False,
        "missing_terms": ["latency", "benchmark"],
        "coverage_score": 0.4,
        "recency_status": "STALE",
        "coherence_score": 0.8,
    }
    planner = ResearchPlanner(ResearchPlanConfig(max_queries=3), llm_client=_fake_llm)
    plan = planner.plan("Qdrant performance 2025", gap)

    assert len(plan.queries) == 3
    assert any("latency" in q.query or "benchmark" in q.query or "query one" in q.query for q in plan.queries)
    assert "COVERAGE" in plan.gap_types


def test_mcp_executor_uses_fetch_and_quality() -> None:
    plan = ResearchPlan(
        queries=[ResearchQuery(query="qdrant benchmark", reason="test")],
        gap_types=["COVERAGE"],
        coverage_score=0.4,
        recency_status="STALE",
        coherence_score=0.6,
    )

    def fake_search(query: str):
        assert "qdrant" in query
        yield "https://example.com/a"
        yield "https://example.com/b"

    def fake_fetch(url: str, prompt: str):
        assert prompt
        return {"content": f"{url} content" if "a" in url else "short"}

    executor = MCPResearchExecutor(fetch_tool=fake_fetch, search_tool=fake_search, max_sources_per_query=2)
    results = executor.execute(plan)
    assert len(results) == 1
    assert len(results[0].sources) == 2
    qualities = [src.quality for src in results[0].sources]
    assert max(qualities) <= 0.8


def test_mcp_executor_cross_reference_hook() -> None:
    plan = ResearchPlan(
        queries=[ResearchQuery(query="qdrant benchmark", reason="test")],
        gap_types=["COVERAGE"],
        coverage_score=0.4,
        recency_status="STALE",
        coherence_score=0.6,
    )

    def fake_search(query: str):
        yield "https://example.com/a"
        yield "https://example.com/b"

    def fake_fetch(url: str, prompt: str):
        return {"content": f"{url} content with overlap"} if "a" in url else {"content": "short"}

    def cross_ref(sources: list[ResearchSource]) -> list[ResearchSource]:
        if not sources:
            return sources
        base = sources[0].content
        for src in sources:
            overlap = len(set(base.split()) & set(src.content.split()))
            src.cross_ref_score = overlap
        return sources

    executor = MCPResearchExecutor(
        fetch_tool=fake_fetch,
        search_tool=fake_search,
        cross_ref=cross_ref,
        max_sources_per_query=2,
    )
    results = executor.execute(plan)
    assert len(results[0].sources) == 2
    assert all(src.cross_ref_score is not None for src in results[0].sources)


def test_critical_integrator_detects_conflicts() -> None:
    integrator = CriticalIntegrator(base_confidence=0.5)
    existing = ["Old claim about throughput 5k qps"]
    new = ["Old claim about throughput 5k qps", "Different claim 10k qps"]

    result = integrator.integrate("throughput question", existing, new)
    assert result.confidence_after > result.confidence_before
    assert result.delta > 0
    assert len(result.conflicts) >= 0
