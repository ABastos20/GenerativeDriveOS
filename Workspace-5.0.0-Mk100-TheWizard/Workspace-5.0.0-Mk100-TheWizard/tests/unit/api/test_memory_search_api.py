from __future__ import annotations

from typing import List

from fastapi.testclient import TestClient

from src.jarvis.api.app import app


class DummyResult:
    def __init__(self, text: str, score: float, source_file: str, section: str, domain: str) -> None:
        self.text = text
        self.score = score
        self.source_file = source_file
        self.section = section
        self.domain = domain
        self.metadata = {"foo": "bar"}


client = TestClient(app)


def test_memory_search_api_basic(monkeypatch) -> None:
    from jarvis.memory import search as memory_search

    def fake_search_memory(query: str, k: int = 10, domains: list[str] | None = None, tags: list[str] | None = None) -> List[DummyResult]:
        assert query == "jarvis core rules"
        assert k == 3
        assert domains == ["jarvis-core"]
        return [DummyResult("result text", 0.9, "docs/jarvis/persona.md", "section-1", "jarvis-core")]

    monkeypatch.setattr(memory_search, "search_memory", fake_search_memory)

    response = client.post(
        "/api/memory/search",
        json={
            "query": "jarvis core rules",
            "source": "jarvis-core",
            "k": 3,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "results" in body
    assert len(body["results"]) == 1
    item = body["results"][0]
    assert item["text"] == "result text"
    assert item["domain"] == "jarvis-core"
    assert item["source_file"] == "docs/jarvis/persona.md"

