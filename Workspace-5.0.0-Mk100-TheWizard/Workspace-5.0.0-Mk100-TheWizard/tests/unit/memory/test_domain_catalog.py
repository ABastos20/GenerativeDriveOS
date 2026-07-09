from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pytest

from jarvis.llm.client import LLMResponse
from jarvis.memory import domain_catalog


@dataclass
class _StubPoint:
    id: str
    payload: Dict[str, Any]


class _StubQdrantClient:
    def __init__(self, points: List[_StubPoint]):
        self._points = points
        self._cursor_index = 0
        self.set_payload_calls: List[Tuple[str, Dict[str, Any], List[str]]] = []

    def scroll(
        self,
        collection_name: str,
        limit: int,
        with_payload: bool,
        with_vectors: bool,
        offset: Optional[str] = None,
    ):
        # Simple linear scroll over the in-memory list.
        if self._cursor_index >= len(self._points):
            return [], None

        batch = self._points[self._cursor_index : self._cursor_index + limit]
        self._cursor_index += len(batch)
        next_offset = None if self._cursor_index >= len(self._points) else str(self._cursor_index)
        return batch, next_offset

    def set_payload(
        self,
        collection_name: str,
        payload: Dict[str, Any],
        points: List[str],
    ):
        self.set_payload_calls.append((collection_name, payload, points))


def _stub_classifier(text: str) -> domain_catalog.ChunkDomainMetadata:
    # Very simple classifier for testing: route by keyword.
    if "database" in text.lower():
        primary = "architecture.database"
    else:
        primary = "generic.unknown"

    return domain_catalog.ChunkDomainMetadata(
        primary_domain=primary,
        secondary_domains=[],
        rick_personas=["Architect Rick"],
        tags=["test"],
        confidence=0.9,
    )


def test_catalog_collection_domains_updates_qdrant_payload_without_db():
    points = [
        _StubPoint(id="1", payload={"text": "This talks about database schema design."}),
        _StubPoint(id="2", payload={"text": "Some generic content."}),
    ]
    client = _StubQdrantClient(points)

    result = domain_catalog.catalog_collection_domains(
        collection_name="knowledge",
        provider="google-ai",
        model=None,
        limit=None,
        batch_size=10,
        dry_run=True,  # avoids hitting Postgres
        classifier=_stub_classifier,
        client=client,
    )

    # dry_run=True means we don't call set_payload or touch DB, but we do process points.
    assert result.collection_name == "knowledge"
    assert result.points_processed == 2
    assert result.domains_created == 0
    assert client.set_payload_calls == []


def test_default_classifier_parses_valid_json(monkeypatch):
    # Patch call_llm so we don't hit the network.
    def _fake_call_llm(prompt: str, system: Optional[str], provider: str, model: str, max_tokens: int):
        content = (
            '{"primary_domain":"history.modern","secondary_domains":["history.general"],'
            '"rick_personas":["Historian Rick"],"tags":["history","modern"],"confidence":0.85}'
        )
        return LLMResponse(
            content=content,
            provider=provider,
            model=model or "test-model",
            input_tokens=10,
            output_tokens=20,
            cost_usd=0.0,
        )

    monkeypatch.setattr(domain_catalog, "call_llm", _fake_call_llm)

    meta = domain_catalog._default_classifier("Some text about WW2", provider="google-ai", model=None)

    assert meta.primary_domain == "history.modern"
    assert meta.secondary_domains == ["history.general"]
    assert meta.rick_personas == ["Historian Rick"]
    assert "history" in meta.tags
    assert meta.confidence == pytest.approx(0.85, rel=1e-3)

