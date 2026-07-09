"""Performance tests for memory search.

Tests latency requirements for memory retrieval operations.
"""

import pytest
from time import monotonic
from statistics import mean, quantiles

from jarvis.memory.search import search_memory
from jarvis.database import qdrant


@pytest.mark.slow
@pytest.mark.integration
def test_search_latency_p95_under_100ms_for_small_k():
    """Test that P95 latency for k<=10 queries is under 100ms.

    Acceptance Criteria (Story 2.4, AC #3):
    P95 latency <100ms for k<=10 under nominal load.

    This test runs 20 queries and validates P95 is under target.
    """
    client = qdrant.get_qdrant_client()

    # Verify collection has data
    collection_info = client.get_collection(qdrant.DEFAULT_COLLECTION_NAME)
    points_count = collection_info.points_count

    if points_count < 100:
        pytest.skip(f"Not enough data for performance test (found {points_count} points, need 100+)")

    # Run 20 queries with k=10
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
        "conversation storage",
        "document chunking",
        "semantic search",
        "LLM provider routing",
        "cost tracking",
        "health checks",
        "configuration management",
        "test coverage",
        "integration tests",
        "retrospective analysis",
    ]

    for query in test_queries:
        start = monotonic()
        results = search_memory(query, k=10)
        duration_ms = (monotonic() - start) * 1000.0
        latencies.append(duration_ms)

        # Sanity check: results returned
        assert len(results) > 0, f"Query '{query}' returned no results"

    # Calculate statistics
    mean_latency = mean(latencies)
    p95_latency = quantiles(latencies, n=20)[18]  # 95th percentile (19th of 20 values)
    max_latency = max(latencies)
    min_latency = min(latencies)

    # Log results for visibility
    print(f"\n📊 Memory Search Latency (k=10, {len(latencies)} queries):")
    print(f"   Mean:  {mean_latency:.2f}ms")
    print(f"   P95:   {p95_latency:.2f}ms")
    print(f"   Min:   {min_latency:.2f}ms")
    print(f"   Max:   {max_latency:.2f}ms")

    # Validate P95 requirement
    assert p95_latency < 100.0, (
        f"P95 latency {p95_latency:.2f}ms exceeds 100ms target "
        f"(mean: {mean_latency:.2f}ms, max: {max_latency:.2f}ms)"
    )


@pytest.mark.integration
def test_search_error_handling_empty_query():
    """Test that empty queries raise ValueError with clear message."""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        search_memory("")


@pytest.mark.integration
def test_search_error_handling_invalid_k():
    """Test that invalid k values raise ValueError with clear message."""
    with pytest.raises(ValueError, match="k must be between 1 and 50"):
        search_memory("test query", k=0)

    with pytest.raises(ValueError, match="k must be between 1 and 50"):
        search_memory("test query", k=100)
