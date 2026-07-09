from __future__ import annotations

import json
from types import SimpleNamespace
from typing import List

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
            import uuid

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
    def _get_db():
        session = _FakeSession()
        try:
            yield session
        finally:
            session.close()

    fastapi_app.app.dependency_overrides[chat_mod.get_db] = _get_db
    yield
    fastapi_app.app.dependency_overrides.pop(chat_mod.get_db, None)


@pytest.fixture
def client():
    return TestClient(fastapi_app.app)


def test_chat_enable_research_returns_summary(monkeypatch, client: TestClient):
    fake_results = [
        SearchResult(
            text="unrelated",
            score=0.1,
            source_file="doc.md",
            section=None,
            domain="jarvis-core",
            metadata={},
        )
    ]

    monkeypatch.setattr(chat_mod.memory_search, "search_memory", lambda *a, **k: fake_results)
    monkeypatch.setattr(chat_mod.memory_search, "deduplicate_results", lambda r: r)
    monkeypatch.setattr(chat_mod.memory_search, "keyword_search", lambda *a, **k: fake_results)
    monkeypatch.setattr(chat_mod.memory_search, "hybrid_search", lambda *a, **k: fake_results)

    fake_llm_resp = SimpleNamespace(
        content="answer",
        input_tokens=1,
        output_tokens=1,
        provider="test",
        model="test-model",
        cost_usd=0.0,
    )
    monkeypatch.setattr(chat_mod, "call_llm", lambda **kwargs: fake_llm_resp)
    import jarvis.llm.client as llm_client

    monkeypatch.setattr(llm_client, "call_llm", lambda **kwargs: fake_llm_resp)
    monkeypatch.setattr(chat_mod.ResearchPlanner, "plan", lambda self, q, g: SimpleNamespace(queries=[], gap_types=[], coverage_score=0.0, recency_status="STALE", coherence_score=0.0))
    monkeypatch.setattr(chat_mod.MCPResearchExecutor, "execute", lambda self, plan: [])

    payload = {
        "message": "coverage gap here",
        "user_id": "u1",
        "provider": "auto",
        "k": 1,
        "enable_research": True,
    }
    response = client.post("/api/chat", content=json.dumps(payload))
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["research_enabled"] is True
    assert data["metadata"]["research_summary"] is not None
    assert data["metadata"]["gap_analysis"]["coverage_gap"] is True
