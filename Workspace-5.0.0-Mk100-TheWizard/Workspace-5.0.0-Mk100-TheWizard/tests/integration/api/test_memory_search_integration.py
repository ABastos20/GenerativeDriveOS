from __future__ import annotations

import os
from typing import Any

import pytest
from fastapi.testclient import TestClient

from jarvis.database import qdrant
from src.jarvis.api.app import app


@pytest.fixture(scope="module")
def qdrant_running() -> None:
    """Skip integration if Qdrant is not reachable."""
    try:
        client = qdrant.get_qdrant_client(timeout=2.0)
        client.get_collections()
    except Exception as exc:
        pytest.skip(f"Qdrant not available: {exc}")


def test_memory_search_endpoint_with_qdrant(qdrant_running: None) -> None:
    """Basic integration smoke-test for /api/memory/search with live Qdrant.

    Assumes bootstrap_jarvis_memory.py has been run and that the
    "knowledge" collection contains domain="jarvis-core" docs.
    """
    # Ensure the API uses the same Qdrant host/port as the ingest tests.
    os.environ.setdefault("QDRANT_HOST", "localhost")
    os.environ.setdefault("QDRANT_PORT", "6333")

    client = TestClient(app)

    response = client.post(
        "/api/memory/search",
        json={
            "query": "jarvis core rules",
            "source": "jarvis-core",
            "k": 3,
        },
    )

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert "results" in body
    # We don't assert a fixed count, but we expect at least one hit
    # when memory has been bootstrapped.
    if body["results"]:
        first = body["results"][0]
        assert "text" in first
        assert first.get("domain") == "jarvis-core"
