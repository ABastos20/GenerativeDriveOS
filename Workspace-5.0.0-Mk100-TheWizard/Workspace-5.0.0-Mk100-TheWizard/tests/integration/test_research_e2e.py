from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import List
import uuid

import pytest
from fastapi.testclient import TestClient

from src.jarvis.api import app as fastapi_app
from src.jarvis.api import chat as chat_mod
from jarvis.memory.search import SearchResult


class _FakeQuery:
    def __init__(self, data: List[object]):
        self._data = data

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self._data

    def first(self):
        return self._data[0] if self._data else None


class _FakeSession:
    def __init__(self):
        self.added = []
        self._conversation = None

    def add(self, obj):
        self.added.append(obj)
        if not getattr(obj, "id", None):
            obj.id = uuid.uuid4()
        if getattr(obj, "__tablename__", "") == "conversations":
            self._conversation = obj

    def flush(self):
        return None

    def commit(self):
        return None

    def close(self):
        return None

    def query(self, *args, **kwargs):
        from src.jarvis.database.models import Conversation

        model = args[0] if args else None
        if model is Conversation and self._conversation:
            return _FakeQuery([self._conversation])
        return _FakeQuery([])


@pytest.fixture(autouse=True)
def override_db_dependency():
    shared = _FakeSession()

    def _get_db():
        try:
            yield shared
        finally:
            shared.close()

    fastapi_app.app.dependency_overrides[chat_mod.get_db] = _get_db
    yield
    fastapi_app.app.dependency_overrides.pop(chat_mod.get_db, None)


@pytest.fixture
def client():
    return TestClient(fastapi_app.app)


@pytest.fixture
def stub_search(monkeypatch):
    state = {"results": []}

    def _search(*args, **kwargs):
        return state["results"]

    monkeypatch.setattr(chat_mod.memory_search, "search_memory", _search)
    monkeypatch.setattr(chat_mod.memory_search, "keyword_search", _search)
    monkeypatch.setattr(chat_mod.memory_search, "hybrid_search", _search)
    monkeypatch.setattr(chat_mod.memory_search, "deduplicate_results", lambda r: r)
    return state


@pytest.fixture(autouse=True)
def stub_llm(monkeypatch):
    fake_llm_resp = SimpleNamespace(
        content="answer",
        input_tokens=5,
        output_tokens=5,
        provider="test",
        model="test-model",
        cost_usd=0.01,
    )
    monkeypatch.setattr(chat_mod, "call_llm", lambda **kwargs: fake_llm_resp)
    import jarvis.llm.client as llm_client

    monkeypatch.setattr(llm_client, "call_llm", lambda **kwargs: fake_llm_resp)


def _planner_queries():
    return [SimpleNamespace(query="q1"), SimpleNamespace(query="q2")]


def _executor_payload(content: str):
    return [
        SimpleNamespace(
            sources=[SimpleNamespace(content=content, metadata={"chunk_id": "new", "verified_at": datetime.now(timezone.utc).isoformat()})]
        )
    ]


def test_missing_gap_research_then_requery(monkeypatch, client: TestClient, stub_search):
    """End-to-end: initial gap triggers research; follow-up benefits from new chunk."""
    stub_search["results"] = [
        SearchResult(
            text="unrelated content",
            score=0.1,
            source_file="doc.md",
            section=None,
            domain="jarvis-core",
            metadata={},
        )
    ]
    monkeypatch.setattr(chat_mod.ResearchPlanner, "plan", lambda self, q, g: SimpleNamespace(queries=_planner_queries()))
    monkeypatch.setattr(chat_mod.MCPResearchExecutor, "execute", lambda self, plan: _executor_payload("new chunk content about benchmarks"))
    monkeypatch.setattr(
        chat_mod.CriticalIntegrator,
        "integrate",
        lambda self, q, existing, new: SimpleNamespace(
            summary="integrated",
            conflicts=[],
            confidence_before=0.2,
            confidence_after=0.7,
            delta=0.5,
        ),
    )

    payload = {
        "message": "latest benchmarks coverage gap",
        "user_id": "u1",
        "provider": "auto",
        "k": 1,
        "enable_research": True,
    }
    resp = client.post("/api/chat", content=json.dumps(payload))
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["gap_analysis"]["coverage_gap"] is True
    assert data["metadata"]["research_summary"]["triggered"] is True
    assert data["metadata"]["research_summary"]["sources_collected"] == 1
    conversation_id = data["conversation_id"]

    # Seed retrieval with researched chunk for follow-up
    stub_search["results"] = [
        SearchResult(
            text="latest benchmarks coverage gap resolved with new data",
            score=0.9,
            source_file="web.md",
            section=None,
            domain="web",
            metadata={"verified_at": datetime.now(timezone.utc).isoformat()},
        )
    ]
    follow_up = {
        "message": "latest benchmarks coverage gap",
        "conversation_id": conversation_id,
        "user_id": "u1",
        "enable_research": False,
        "k": 1,
    }
    resp2 = client.post("/api/chat", content=json.dumps(follow_up))
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["metadata"]["gap_analysis"]["recency_gap"] is False
    assert data2["metadata"]["gap_analysis"]["recency_status"] == "FRESH"
    assert data2["metadata"]["research_summary"] is None


def test_stale_gap_triggers_research_and_confidence_delta(monkeypatch, client: TestClient, stub_search):
    """End-to-end: stale knowledge triggers research and raises confidence."""
    stale_date = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
    stub_search["results"] = [
        SearchResult(
            text="old data about latency",
            score=0.6,
            source_file="old.md",
            section=None,
            domain="jarvis-core",
            metadata={"verified_at": stale_date},
        )
    ]
    monkeypatch.setattr(chat_mod.ResearchPlanner, "plan", lambda self, q, g: SimpleNamespace(queries=_planner_queries()))
    monkeypatch.setattr(chat_mod.MCPResearchExecutor, "execute", lambda self, plan: _executor_payload("fresh latency numbers 2025"))
    monkeypatch.setattr(
        chat_mod.CriticalIntegrator,
        "integrate",
        lambda self, q, existing, new: SimpleNamespace(
            summary="synthesized",
            conflicts=["divergence"],
            confidence_before=0.3,
            confidence_after=0.8,
            delta=0.5,
        ),
    )

    payload = {
        "message": "latest latency data",
        "user_id": "u2",
        "provider": "auto",
        "k": 1,
        "enable_research": True,
    }
    resp = client.post("/api/chat", content=json.dumps(payload))
    assert resp.status_code == 200
    data = resp.json()
    gap = data["metadata"]["gap_analysis"]
    assert gap["recency_gap"] is True
    assert gap["recency_status"] in ("STALE", "SPARSE")
    summary = data["metadata"]["research_summary"]
    assert summary["triggered"] is True
    assert summary["confidence_after"] == 0.8
    assert summary["confidence_after"] > summary["confidence_before"]


def test_contradictory_sources_trigger_research(monkeypatch, client: TestClient, stub_search):
    """Contradictory coherence triggers research path."""
    stub_search["results"] = [
        SearchResult(
            text="source claims latency is 10ms",
            score=0.8,
            source_file="a.md",
            section=None,
            domain="jarvis-core",
            metadata={},
        ),
        SearchResult(
            text="source claims latency is 200ms",
            score=0.8,
            source_file="b.md",
            section=None,
            domain="jarvis-core",
            metadata={},
        ),
    ]
    monkeypatch.setattr(chat_mod.CoherenceAnalyzer, "analyze", lambda self, r: SimpleNamespace(coherence_score=0.1, contradictory=True, pair_count=1))
    monkeypatch.setattr(chat_mod.ResearchPlanner, "plan", lambda self, q, g: SimpleNamespace(queries=_planner_queries()))
    monkeypatch.setattr(chat_mod.MCPResearchExecutor, "execute", lambda self, plan: _executor_payload("harmonized latency numbers"))
    monkeypatch.setattr(
        chat_mod.CriticalIntegrator,
        "integrate",
        lambda self, q, existing, new: SimpleNamespace(
            summary="conflicts resolved",
            conflicts=["latency mismatch"],
            confidence_before=0.3,
            confidence_after=0.75,
            delta=0.45,
        ),
    )
    payload = {"message": "conflicting latency info", "user_id": "u3", "enable_research": True, "k": 2}
    resp = client.post("/api/chat", content=json.dumps(payload))
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["gap_analysis"]["contradictory"] is True
    assert data["metadata"]["research_summary"]["triggered"] is True
    assert data["metadata"]["research_summary"]["confidence_after"] > data["metadata"]["research_summary"]["confidence_before"]


def test_rate_limit_blocks_research(monkeypatch, client: TestClient, stub_search):
    """Rate limit rejection surfaces 429."""
    stub_search["results"] = [
        SearchResult(
            text="partial context",
            score=0.2,
            source_file="doc.md",
            section=None,
            domain="jarvis-core",
            metadata={},
        )
    ]
    monkeypatch.setattr(
        chat_mod.CoverageAnalyzer,
        "analyze",
        lambda self, q, r: SimpleNamespace(coverage_score=0.1, grounded_terms=[], missing_terms=["latest"], gap_detected=True),
    )
    monkeypatch.setattr(chat_mod.ResearchLimiter, "check_limit", lambda self, user_id: (False, 11))
    payload = {"message": "latest benchmarks", "user_id": "u4", "enable_research": True}
    resp = client.post("/api/chat", content=json.dumps(payload))
    assert resp.status_code == 429


def test_opt_in_default_off(monkeypatch, client: TestClient, stub_search):
    """When research not enabled, gap analysis does not trigger research_summary."""
    stub_search["results"] = []
    payload = {"message": "missing data question", "user_id": "u5", "enable_research": False}
    resp = client.post("/api/chat", content=json.dumps(payload))
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["gap_analysis"]["coverage_gap"] is True
    assert data["metadata"]["research_summary"] is None


def test_research_smoke_performance(monkeypatch, client: TestClient, stub_search):
    """Smoke performance: research path completes quickly with mocks."""
    stub_search["results"] = []
    monkeypatch.setattr(chat_mod.ResearchPlanner, "plan", lambda self, q, g: SimpleNamespace(queries=_planner_queries()))
    monkeypatch.setattr(chat_mod.MCPResearchExecutor, "execute", lambda self, plan: _executor_payload("fast payload"))
    monkeypatch.setattr(
        chat_mod.CriticalIntegrator,
        "integrate",
        lambda self, q, existing, new: SimpleNamespace(
            summary="fast",
            conflicts=[],
            confidence_before=0.5,
            confidence_after=0.6,
            delta=0.1,
        ),
    )
    start = datetime.now()
    resp = client.post("/api/chat", content=json.dumps({"message": "perf test", "user_id": "u6", "enable_research": True}))
    elapsed = (datetime.now() - start).total_seconds()
    assert resp.status_code == 200
    assert elapsed < 2.0
