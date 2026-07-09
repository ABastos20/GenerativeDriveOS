from __future__ import annotations

import os
from typing import List, NamedTuple
from unittest.mock import MagicMock, patch

import pytest

from jarvis.memory import search as search_mod
from jarvis.memory.retrieval import core as core_mod
from jarvis.memory.retrieval import filters as filters_mod
from jarvis.memory.retrieval import fusion as fusion_mod


class DummyPoint:
    def __init__(
        self,
        text: str,
        score: float,
        domain: str = "test",
        **extra_payload: object,
    ) -> None:
        payload = {
            "text": text,
            "source_file": "docs/example.md",
            "section": "Example",
            "domain": domain,
        }
        payload.update(extra_payload)
        self.payload = payload
        self.score = score


def _stub_search(points: List[DummyPoint]) -> List[DummyPoint]:
    return points


@patch("jarvis.memory.retrieval.core._embed_query", return_value=[0.1] * 384)
def test_search_memory_basic(mock_embed: MagicMock) -> None:
    client = MagicMock()
    response = MagicMock()
    response.points = _stub_search(
        [DummyPoint("hello world", 0.9), DummyPoint("other", 0.8)]
    )
    client.query_points.return_value = response

    results = search_mod.search_memory("test query", k=5, client=client)

    assert len(results) == 2
    assert results[0].text == "hello world"
    assert results[0].score >= results[1].score
    client.query_points.assert_called_once()


@patch("jarvis.memory.retrieval.core._embed_query", return_value=[0.1] * 384)
def test_search_memory_domain_filter(mock_embed: MagicMock) -> None:
    client = MagicMock()

    def fake_query_points(**kwargs):
        q_filter = kwargs.get("query_filter")
        # Ensure filter is built when domains passed
        assert q_filter is not None
        response = MagicMock()
        response.points = _stub_search(
            [DummyPoint("core text", 0.95, domain="jarvis-core")]
        )
        return response

    client.query_points.side_effect = fake_query_points

    results = search_mod.search_memory("core query", domains=["jarvis-core"], client=client)

    assert len(results) == 1
    assert results[0].domain == "jarvis-core"


@patch("jarvis.memory.retrieval.core._embed_query", return_value=[0.1] * 384)
def test_search_memory_empty_query(mock_embed: MagicMock) -> None:
    client = MagicMock()
    try:
        search_mod.search_memory("   ", client=client)
    except ValueError:
        client.search.assert_not_called()
    else:  # pragma: no cover - defensive, should not happen
        assert False, "Expected ValueError for empty query"


@patch("jarvis.memory.retrieval.core._embed_query", return_value=[0.1] * 384)
@patch("jarvis.memory.retrieval.core._load_reranker")
@patch("jarvis.memory.retrieval.core._should_rerank", return_value=True)
def test_search_memory_reranking_uses_reranker(
    mock_should_rerank: MagicMock,
    mock_load_reranker: MagicMock,
    mock_embed: MagicMock,
) -> None:
    """search_memory should call the reranker when enabled."""
    client = MagicMock()
    response = MagicMock()
    response.points = _stub_search(
        [
            DummyPoint("doc A", 0.9),
            DummyPoint("doc B", 0.8),
            DummyPoint("doc C", 0.7),
        ]
    )
    client.query_points.return_value = response

    # Stub reranker to swap order deterministically via scores
    class _DummyReranker:
        def predict(self, pairs: List[List[str]]) -> List[float]:
            # Assign higher score to the second document to prove reranking
            return [0.1, 0.9, 0.5][: len(pairs)]

    mock_load_reranker.return_value = _DummyReranker()

    results = search_mod.search_memory("test query", k=3, client=client)

    # Reranking should have elevated "doc B" to the top
    texts = [r.text for r in results[:2]]
    assert "doc B" in texts


class _KeywordRow(NamedTuple):
    id: int
    content: str
    rank: float


def test_keyword_search_basic() -> None:
    session = MagicMock()
    session.execute.return_value.all.return_value = [
        _KeywordRow(id=1, content="First message about vectors", rank=0.8),
        _KeywordRow(id=2, content="Second message about BM25", rank=0.5),
    ]

    results = search_mod.keyword_search("vectors", k=5, session=session)

    assert len(results) == 2
    assert results[0].text == "First message about vectors"
    assert results[0].domain == "jarvis-conversations"
    assert results[0].metadata["message_id"] == "1"
    session.execute.assert_called_once()


def test_keyword_search_domain_filter_excludes_when_not_matching() -> None:
    session = MagicMock()
    results = search_mod.keyword_search(
        "vectors",
        k=5,
        domains=["jarvis-insights"],
        session=session,
    )
    assert results == []
    session.execute.assert_not_called()


@patch("jarvis.memory.retrieval.core.document_keyword_search")
@patch("jarvis.memory.retrieval.core.keyword_search")
@patch("jarvis.memory.retrieval.core.search_memory")
def test_hybrid_search_merges_and_weights(
    mock_semantic: MagicMock,
    mock_keyword: MagicMock,
    mock_doc_keyword: MagicMock,
) -> None:
    semantic_results = [
        search_mod.SearchResult(
            text="Semantic A",
            score=0.2,
            source_file=None,
            section=None,
            domain="jarvis-insights",
            metadata={"chunk_id": "1"},
        ),
        search_mod.SearchResult(
            text="Semantic B",
            score=0.6,
            source_file=None,
            section=None,
            domain="jarvis-insights",
            metadata={"chunk_id": "2"},
        ),
    ]
    keyword_results = [
        search_mod.SearchResult(
            text="Keyword A",
            score=0.5,
            source_file=None,
            section=None,
            domain="jarvis-insights",
            metadata={"chunk_id": "1"},
        )
    ]
    doc_results = [
        search_mod.SearchResult(
            text="Doc Keyword C",
            score=0.4,
            source_file=None,
            section=None,
            domain="jarvis-insights",
            metadata={"chunk_id": "3"},
        )
    ]

    mock_semantic.return_value = semantic_results
    mock_keyword.return_value = keyword_results
    mock_doc_keyword.return_value = doc_results

    results = search_mod.hybrid_search("test", k=5, weight=0.7)

    # Hybrid now includes document keyword hits; expect 3 merged results
    assert len(results) == 3
    # Ensure scores are in descending order
    assert results[0].score >= results[1].score
    # Ensure metadata carries normalization info
    assert "semantic_score_norm" in results[0].metadata
    assert "keyword_score_norm" in results[0].metadata


@patch("jarvis.memory.retrieval.fusion.expand_query")
@patch("jarvis.memory.retrieval.core.search_memory")
def test_expanded_search_rrf_and_deduplication(
    mock_search_memory: MagicMock,
    mock_expand_query: MagicMock,
) -> None:
    """expanded_search should deduplicate docs and attach RRF metadata."""
    # Force two query variants (original + 2 expansions)
    mock_expand_query.return_value = ["original", "variant-a", "variant-b"]

    # Helper to build SearchResult with a given chunk_id
    def make_result(text: str, chunk_id: str) -> search_mod.SearchResult:
        return search_mod.SearchResult(
            text=text,
            score=1.0,
            source_file="docs/example.md",
            section="Example",
            domain="jarvis-insights",
            metadata={"chunk_id": chunk_id},
        )

    # Same document (chunk-2) appears in multiple variant result sets
    original_results = [make_result("Doc A", "chunk-1"), make_result("Doc B", "chunk-2")]
    variant_a_results = [make_result("Doc B", "chunk-2"), make_result("Doc C", "chunk-3")]
    variant_b_results = [make_result("Doc C", "chunk-3")]

    def search_side_effect(query: str, *args, **kwargs):
        if query == "original":
            return original_results
        if query == "variant-a":
            return variant_a_results
        if query == "variant-b":
            return variant_b_results
        return []

    mock_search_memory.side_effect = search_side_effect

    results = search_mod.expanded_search(
        "original",
        k=10,
        expansion_count=2,
        retriever="semantic",
    )

    # expand_query called with original query and requested expansion_count
    mock_expand_query.assert_called_once_with("original", count=2)
    # search_memory called once per variant (3 total: original + 2 expansions)
    assert mock_search_memory.call_count == 3

    # Deduplication: three unique chunk_ids
    assert len(results) == 3
    chunk_ids = {r.metadata.get("chunk_id") for r in results}
    assert chunk_ids == {"chunk-1", "chunk-2", "chunk-3"}

    # RRF metadata is attached
    for r in results:
        assert "rrf_score" in r.metadata
        assert r.metadata["fusion_strategy"] == "reciprocal_rank_fusion"
        assert r.metadata["expansion_count"] == 2


def test_expanded_search_validates_expansion_count() -> None:
    """expanded_search should enforce expansion_count range [0, 5]."""
    with pytest.raises(ValueError, match="expansion_count must be between 0 and 5"):
        search_mod.expanded_search("test", expansion_count=-1)

    with pytest.raises(ValueError, match="expansion_count must be between 0 and 5"):
        search_mod.expanded_search("test", expansion_count=10)


def test_infer_query_domains_gd_sines() -> None:
    domains = filters_mod.infer_query_domains("GD Sines hydrogen model smart-grid")
    assert "gd.generative_drive" in domains


def test_infer_query_domains_cyber_and_math() -> None:
    domains = filters_mod.infer_query_domains("Cisco ASA IPSec tunnel and Riemann curvature tensor")
    assert any(d.startswith("network.") or d.startswith("cyber.") for d in domains)
    assert any(d.startswith("math.") for d in domains)


def test_deduplicate_results_prefers_structured_ids_and_text_digest() -> None:
    """deduplicate_results should drop duplicate chunks while preserving order."""
    results = [
        search_mod.SearchResult(
            text="Doc A",
            score=0.9,
            source_file=None,
            section=None,
            domain="jarvis.core",
            metadata={"chunk_id": "chunk-1"},
        ),
        search_mod.SearchResult(
            text="Doc A (repeat)",
            score=0.8,
            source_file=None,
            section=None,
            domain="jarvis.core",
            metadata={"chunk_id": "chunk-1"},
        ),
        search_mod.SearchResult(
            text="Doc B",
            score=0.7,
            source_file=None,
            section=None,
            domain="jarvis.core",
            metadata={"hash": "hash-1"},
        ),
        search_mod.SearchResult(
            text="Doc B",
            score=0.6,
            source_file=None,
            section=None,
            domain="jarvis.core",
            metadata={},
        ),
        search_mod.SearchResult(
            text="Doc C",
            score=0.5,
            source_file=None,
            section=None,
            domain="jarvis.core",
            metadata={},
        ),
    ]

    deduped = search_mod.deduplicate_results(results)

    # With current metadata, chunk/hash duplication yields Doc B twice.
    assert [r.text for r in deduped] == ["Doc A", "Doc B", "Doc B", "Doc C"]
    # Ensure the first occurrence with chunk_id/hash is kept
    assert deduped[0].metadata["chunk_id"] == "chunk-1"
    assert deduped[1].metadata["hash"] == "hash-1"


def test_expanded_search_validates_retriever_name() -> None:
    """expanded_search should reject unknown retriever modes."""
    with pytest.raises(ValueError, match="Invalid retriever"):
        search_mod.expanded_search("test", expansion_count=1, retriever="unknown-mode")


def test_expanded_search_validates_weight_for_hybrid() -> None:
    """Hybrid mode must enforce weight range [0.0, 1.0]."""
    with pytest.raises(ValueError, match="weight must be between 0.0 and 1.0"):
        search_mod.expanded_search(
            "test",
            expansion_count=1,
            retriever="hybrid",
            weight=1.5,
        )


@patch("jarvis.memory.retrieval.fusion.expand_query", return_value=["original"])
@patch("jarvis.memory.retrieval.core.search_memory")
@patch("jarvis.memory.retrieval.fusion.logger")
def test_expanded_search_logs_expected_fields(
    mock_logger: MagicMock,
    mock_search_memory: MagicMock,
    mock_expand_query: MagicMock,
) -> None:
    """expanded_search should emit structured logs with expected fields."""
    # mock_logger is the logger instance itself now via patch


    # Provide a minimal result set for the single query variant
    mock_search_memory.return_value = [
        search_mod.SearchResult(
            text="Doc A",
            score=0.5,
            source_file=None,
            section=None,
            domain="jarvis-insights",
            metadata={"chunk_id": "chunk-1"},
        )
    ]

    results = search_mod.expanded_search(
        "original",
        k=3,
        expansion_count=1,
        retriever="semantic",
    )

    # Sanity check: results returned
    assert results

    # Collect all info() events
    events = mock_logger.info.call_args_list
    event_names = [call.args[0] for call in events]

    # Ensure key lifecycle events are logged
    assert "expanded_search_started" in event_names
    assert "expanded_search_retrieval_completed" in event_names
    assert "expanded_search_completed" in event_names

    # Inspect completed event payload
    completed_kwargs = None
    for call in events:
        if call.args[0] == "expanded_search_completed":
            completed_kwargs = call.kwargs
            break

    assert completed_kwargs is not None, "expanded_search_completed event not found"
    assert completed_kwargs.get("k") == 3
    assert completed_kwargs.get("expansion_count") == 1
    assert completed_kwargs.get("retriever") == "semantic"
    assert completed_kwargs.get("fusion_strategy") == "reciprocal_rank_fusion"
    # total_latency_ms should be present and numeric
    assert "total_latency_ms" in completed_kwargs


@patch("jarvis.memory.retrieval.core._embed_query", return_value=[0.1] * 384)
def test_time_weight_prefers_higher_doc_step_count(mock_embed: MagicMock) -> None:
    """search_memory should favour results with higher doc_step_count."""
    client = MagicMock()
    response = MagicMock()
    response.points = _stub_search(
        [
            DummyPoint(
                "early iteration",
                0.5,
                domain="jarvis-insights",
                doc_step_count=1,
            ),
            DummyPoint(
                "later iteration",
                0.5,
                domain="jarvis-insights",
                doc_step_count=10,
            ),
        ]
    )
    client.query_points.return_value = response

    with patch.dict(os.environ, {"JARVIS_TIME_WEIGHT_ALPHA": "0.5"}):
        results = search_mod.search_memory("test query", k=2, client=client)

    assert len(results) == 2
    # Later/richer document should be ranked first
    assert results[0].text == "later iteration"
    assert results[0].metadata.get("time_weight") is not None
    assert "original_score" in results[0].metadata


def test_time_weight_no_doc_step_count_is_noop() -> None:
    """apply_time_weight should not change scores when no doc_step_count."""
    results = [
        search_mod.SearchResult(
            text="A",
            score=0.7,
            source_file=None,
            section=None,
            domain=None,
            metadata={},
        ),
        search_mod.SearchResult(
            text="B",
            score=0.9,
            source_file=None,
            section=None,
            domain=None,
            metadata={},
        ),
    ]
    original_scores = [r.score for r in results]

    with patch.dict(os.environ, {"JARVIS_TIME_WEIGHT_ALPHA": "0.5"}):
        out = filters_mod.apply_time_weight(results)

    assert [r.score for r in out] == original_scores
    for res in out:
        assert "time_weight" not in res.metadata
