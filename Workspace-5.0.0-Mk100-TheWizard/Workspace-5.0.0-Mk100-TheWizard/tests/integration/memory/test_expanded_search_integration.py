"""Integration tests for expanded_search (query expansion + RRF fusion)."""

from __future__ import annotations

from pathlib import Path
from statistics import mean, quantiles
from time import monotonic

import pytest

from jarvis.database.models import Conversation, Message
from jarvis.database.postgres import get_session_factory
from jarvis.database import qdrant
from jarvis.memory import ingest
from jarvis.memory import search as search_mod


@pytest.mark.integration
def test_expanded_search_returns_fused_results(tmp_path: Path) -> None:
    """expanded_search should return deduplicated results with RRF metadata.

    This test mirrors the hybrid retrieval integration test but exercises the
    full expansion + fusion pipeline over real Postgres + Qdrant.
    """
    # --- Arrange Postgres conversation/message ---------------------------------
    SessionFactory = get_session_factory()
    session = SessionFactory()
    try:
        conversation = Conversation()
        session.add(conversation)
        session.flush()

        message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Hybrid retrieval edge case with BM25 and vector search.",
        )
        session.add(message)
        session.commit()
    finally:
        session.close()

    # --- Arrange Qdrant memory chunk -------------------------------------------
    text = "This document describes a hybrid retrieval edge case with BM25 and vector search."
    doc_path = tmp_path / "hybrid-expansion-test.md"
    doc_path.write_text(text, encoding="utf-8")

    # Ingest into Qdrant under the jarvis-conversations domain so domain filters align
    ingest.ingest_file(path=doc_path, domain="jarvis-conversations")

    # --- Act: run expanded search ----------------------------------------------
    results = search_mod.expanded_search(
        "BM25",
        k=5,
        expansion_count=2,
        domains=["jarvis-conversations"],
        retriever="hybrid",
        weight=0.7,
    )

    # --- Assert -----------------------------------------------------------------
    assert results, "Expected at least one expanded search result"
    assert any(r.domain == "jarvis-conversations" for r in results)

    # Ensure RRF metadata is present on at least one result
    assert any(
        "rrf_score" in r.metadata and r.metadata.get("fusion_strategy") == "reciprocal_rank_fusion"
        for r in results
    )


@pytest.mark.slow
@pytest.mark.integration
def test_expanded_search_latency_p95_under_2s_for_small_k() -> None:
    """P95 latency for expanded_search (small k, small expansion_count) stays under 2s.

    This is a coarse-grained performance validation for Story 3.3:
    - expansion_count kept small (2)
    - semantic retriever used to avoid avoidable overhead
    - skips if collection does not have enough data
    """
    client = qdrant.get_qdrant_client()

    # Verify collection has enough data for a meaningful test
    collection_info = client.get_collection(qdrant.DEFAULT_COLLECTION_NAME)
    points_count = collection_info.points_count

    if points_count < 100:
        pytest.skip(f"Not enough data for expanded_search performance test (found {points_count} points, need 100+)")

    latencies = []
    test_queries = [
        "database schema design",
        "API endpoint implementation",
        "error handling patterns",
        "authentication workflow",
        "memory ingestion pipeline",
        "vector embeddings",
        "PostgreSQL queries",
        "Qdrant collection",
        "structlog events",
        "Docker compose services",
    ]

    for query in test_queries:
        start = monotonic()
        try:
            results = search_mod.expanded_search(
                query,
                k=10,
                expansion_count=2,
                retriever="semantic",
            )
        except NotImplementedError as exc:
            # Some Torch builds in lightweight containers expose meta tensors that
            # cannot be moved with .to(), which is an environment limitation, not
            # a logic bug. Treat this as "cannot measure perf here".
            pytest.skip(f"expanded_search performance test skipped due to embedding backend: {exc}")
        duration_ms = (monotonic() - start) * 1000.0
        latencies.append(duration_ms)

        # Sanity check: results returned
        assert len(results) > 0, f"Query '{query}' returned no results for expanded_search"

    # Calculate statistics
    mean_latency = mean(latencies)
    # For n queries, 95th percentile is the element at index floor(0.95 * n) - 1 after sorting
    p95_latency = quantiles(latencies, n=len(latencies))[int(0.95 * len(latencies)) - 1]
    max_latency = max(latencies)
    min_latency = min(latencies)

    # Log results for visibility in test output
    print(f"\n📊 Expanded Search Latency (k=10, expansion_count=2, {len(latencies)} queries):")
    print(f"   Mean:  {mean_latency:.2f}ms")
    print(f"   P95:   {p95_latency:.2f}ms")
    print(f"   Min:   {min_latency:.2f}ms")
    print(f"   Max:   {max_latency:.2f}ms")

    # Validate P95 requirement from Story 3.3 (< 2000ms)
    assert p95_latency < 2000.0, (
        f"P95 latency {p95_latency:.2f}ms exceeds 2000ms target "
        f"(mean: {mean_latency:.2f}ms, max: {max_latency:.2f}ms)"
    )
