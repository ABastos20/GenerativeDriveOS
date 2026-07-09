from __future__ import annotations

from pathlib import Path
from typing import List
from uuid import uuid4

import pytest

from jarvis.database import qdrant
from jarvis.memory import ingest


@pytest.fixture(scope="module")
def qdrant_running() -> None:
    """Skip integration if Qdrant is not reachable."""
    try:
        client = qdrant.get_qdrant_client(timeout=2.0)
        client.get_collections()
    except Exception as exc:
        pytest.skip(f"Qdrant not available: {exc}")


def _stub_vectors(count: int) -> List[List[float]]:
    return [[0.01] * qdrant.VECTOR_SIZE for _ in range(count)]


def test_ingest_file_integration(tmp_path: Path, qdrant_running: None) -> None:
    sample = tmp_path / "sample.md"
    sample.write_text("# Title\n\nBody paragraph.", encoding="utf-8")

    collection_name = f"ingest_{uuid4().hex[:8]}"

    client = qdrant.get_qdrant_client(timeout=2.0)

    result = ingest.ingest_file(
        sample,
        collection_name=collection_name,
        embed_fn=lambda texts: _stub_vectors(len(texts)),
        client=client,
    )

    assert result.points_written == result.chunks
    info = qdrant.get_collection_info(collection_name=collection_name, client=client)
    assert info.config.params.vectors.size == qdrant.VECTOR_SIZE
    assert info.points_count >= result.points_written

    client.delete_collection(collection_name=collection_name)
