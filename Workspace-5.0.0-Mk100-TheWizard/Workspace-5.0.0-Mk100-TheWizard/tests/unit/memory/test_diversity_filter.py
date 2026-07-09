"""Unit tests for Retrieval Saturation Filter - MMR Diversity (Story 4.5.4).

Tests:
- apply_diversity_filter() with different modes
- _select_mmr() algorithm
- Same-doc similarity floor
- Overlap metric computation
"""

import pytest
import numpy as np
from unittest.mock import MagicMock

from jarvis.memory.diversity import (
    apply_diversity_filter,
    _compute_pairwise_similarity,
    _select_mmr,
    _compute_overlap_metric,
    _estimate_text_similarity,
    DIVERSITY_LAMBDAS,
    SAME_DOC_SIM_FLOOR,
)
from jarvis.memory.search import SearchResult


# ═══════════════════════════════════════════════════════════════════════════════
# ✨ TEST FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


def _make_result(
    text: str = "test content",
    score: float = 0.9,
    doc_key: str = "doc-1",
    domain: str = "test",
) -> SearchResult:
    """Create a SearchResult for testing."""
    return SearchResult(
        text=text,
        score=score,
        source_file=None,
        section=None,
        domain=domain,
        metadata={},
        doc_id=None,
        doc_key=doc_key,
    )


class TestApplyDiversityFilter:
    """Tests for apply_diversity_filter function."""

    def test_minimal_mode_preserves_order(self):
        """Minimal mode should not change result order."""
        results = [
            _make_result(text="A", score=0.9, doc_key="doc-1"),
            _make_result(text="B", score=0.8, doc_key="doc-1"),
            _make_result(text="C", score=0.7, doc_key="doc-1"),
        ]
        
        filtered = apply_diversity_filter(results, max_results=3, diversity_mode="minimal")
        
        assert len(filtered) == 3
        assert filtered[0].text == "A"
        assert filtered[1].text == "B"
        assert filtered[2].text == "C"

    def test_empty_results_returns_empty(self):
        """Empty input should return empty output."""
        filtered = apply_diversity_filter([], max_results=5, diversity_mode="balanced")
        assert filtered == []

    def test_balanced_mode_spreads_results(self):
        """Balanced mode should spread across different doc_keys."""
        results = [
            _make_result(text="A from doc1", score=0.95, doc_key="doc-1"),
            _make_result(text="B from doc1", score=0.90, doc_key="doc-1"),
            _make_result(text="C from doc2", score=0.85, doc_key="doc-2"),
            _make_result(text="D from doc3", score=0.80, doc_key="doc-3"),
        ]
        
        filtered = apply_diversity_filter(results, max_results=3, diversity_mode="balanced")
        
        # Should pick docs from different doc_keys
        doc_keys = [r.doc_key for r in filtered]
        # Expect diversity - not all from doc-1
        assert len(set(doc_keys)) >= 2

    def test_respects_max_results(self):
        """Should not return more than max_results."""
        results = [_make_result(doc_key=f"doc-{i}") for i in range(10)]
        
        filtered = apply_diversity_filter(results, max_results=5, diversity_mode="balanced")
        
        assert len(filtered) == 5

    def test_aggressive_mode_exists(self):
        """Aggressive mode should be recognized."""
        results = [_make_result() for _ in range(3)]
        
        # Should not raise
        filtered = apply_diversity_filter(results, max_results=3, diversity_mode="aggressive")
        
        assert len(filtered) <= 3


class TestSelectMMR:
    """Tests for _select_mmr function."""

    def test_selects_first_by_relevance(self):
        """First selected should be highest relevance."""
        results = [
            _make_result(score=0.9),
            _make_result(score=0.5),
        ]
        similarity = np.eye(2)
        
        selected = _select_mmr(results, similarity, lambda_val=0.5, k=1)
        
        assert selected == [0]

    def test_selects_k_items(self):
        """Should select exactly k items."""
        results = [_make_result(score=0.5 + i * 0.1) for i in range(5)]
        similarity = np.eye(5)
        
        selected = _select_mmr(results, similarity, lambda_val=0.5, k=3)
        
        assert len(selected) == 3

    def test_avoids_similar_items(self):
        """High similarity should push items down in selection."""
        results = [
            _make_result(text="A", score=0.9),
            _make_result(text="B similar to A", score=0.85),
            _make_result(text="C different", score=0.7),
        ]
        # A and B are very similar
        similarity = np.array([
            [1.0, 0.95, 0.1],
            [0.95, 1.0, 0.1],
            [0.1, 0.1, 1.0],
        ])
        
        selected = _select_mmr(results, similarity, lambda_val=0.5, k=2)
        
        # First should be A (highest score), second should be C (most diverse)
        assert 0 in selected
        assert 2 in selected  # C is more diverse than B


class TestPairwiseSimilarity:
    """Tests for _compute_pairwise_similarity function."""

    def test_same_doc_key_gets_floor(self):
        """Same doc_key should have high similarity."""
        results = [
            _make_result(text="chunk 1 from doc A", doc_key="doc-A"),
            _make_result(text="chunk 2 from doc A", doc_key="doc-A"),
            _make_result(text="chunk from doc B", doc_key="doc-B"),
        ]
        
        similarity = _compute_pairwise_similarity(results)
        
        # Same doc_key should have floor applied
        assert similarity[0, 1] >= SAME_DOC_SIM_FLOOR
        assert similarity[1, 0] >= SAME_DOC_SIM_FLOOR


class TestOverlapMetric:
    """Tests for _compute_overlap_metric function."""

    def test_single_result_no_overlap(self):
        """Single result has no overlap."""
        results = [_make_result()]
        
        overlap = _compute_overlap_metric(results)
        
        assert overlap == 0.0

    def test_all_same_doc_high_overlap(self):
        """All results from same doc = high overlap."""
        results = [_make_result(doc_key="same-doc") for _ in range(5)]
        
        overlap = _compute_overlap_metric(results)
        
        assert overlap == 0.8  # 1 - 1/5

    def test_all_unique_docs_no_overlap(self):
        """All unique docs = no overlap."""
        results = [_make_result(doc_key=f"doc-{i}") for i in range(5)]
        
        overlap = _compute_overlap_metric(results)
        
        assert overlap == 0.0  # 1 - 5/5


class TestTextSimilarity:
    """Tests for _estimate_text_similarity fallback."""

    def test_identical_text_high_similarity(self):
        """Same text should have similarity 1.0."""
        sim = _estimate_text_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_no_overlap_zero_similarity(self):
        """No word overlap = 0 similarity."""
        sim = _estimate_text_similarity("hello world", "foo bar")
        assert sim == 0.0

    def test_partial_overlap(self):
        """Partial word overlap."""
        sim = _estimate_text_similarity("hello world", "hello there")
        assert 0.0 < sim < 1.0


class TestDiversityConstants:
    """Tests for module constants."""

    def test_lambda_values(self):
        """Lambda values should be correct."""
        assert DIVERSITY_LAMBDAS["balanced"] == 0.5
        assert DIVERSITY_LAMBDAS["aggressive"] == 0.3
        assert DIVERSITY_LAMBDAS["minimal"] == 1.0

    def test_same_doc_floor(self):
        """Same-doc floor should be high."""
        assert SAME_DOC_SIM_FLOOR == 0.85
