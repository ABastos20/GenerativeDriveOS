"""Unit tests for Memory Recency & Lineage Enforcement (Story 4.5.3).

Tests:
- _compute_freshness_score() - 30-day half-life decay formula
- _apply_freshness_filter() - stale document filtering
- _resolve_version_conflicts() - newest version preference
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from jarvis.memory.retrieval.filters import (
    _compute_freshness_score,
    apply_freshness_filter as _apply_freshness_filter,
    resolve_version_conflicts as _resolve_version_conflicts,
    FRESHNESS_HALFLIFE_DAYS,
    DEFAULT_MIN_FRESHNESS,
)
from jarvis.memory.retrieval.types import SearchResult


# ═══════════════════════════════════════════════════════════════════════════════
# ✨ FRESHNESS SCORING TESTS
# ═══════════════════════════════════════════════════════════════════════════════


def _make_result(
    text: str = "test",
    doc_key: str = "doc-1",
    doc_last_seen: str | None = None,
    ingested_at: str | None = None,
) -> SearchResult:
    """Create a SearchResult with given metadata."""
    metadata = {}
    if doc_last_seen:
        metadata["doc_last_seen"] = doc_last_seen
    if ingested_at:
        metadata["ingested_at"] = ingested_at
    return SearchResult(
        text=text,
        score=0.9,
        source_file=None,
        section=None,
        domain="test",
        metadata=metadata,
        doc_id=None,
        doc_key=doc_key,
    )


class TestComputeFreshnessScore:
    """Tests for _compute_freshness_score function."""

    def test_brand_new_document_returns_max_freshness(self):
        """Document just ingested should have freshness close to 1.0."""
        now = datetime.now(timezone.utc).isoformat()
        result = _make_result(doc_last_seen=now)
        score = _compute_freshness_score(result)
        assert 0.99 <= score <= 1.0

    def test_30_day_old_doc_returns_half_freshness(self):
        """Document 30 days old should have ~0.5 freshness (half-life)."""
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        result = _make_result(doc_last_seen=thirty_days_ago)
        score = _compute_freshness_score(result)
        assert 0.48 <= score <= 0.52

    def test_60_day_old_doc_returns_third_freshness(self):
        """Document 60 days old should have ~0.33 freshness."""
        sixty_days_ago = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        result = _make_result(doc_last_seen=sixty_days_ago)
        score = _compute_freshness_score(result)
        assert 0.30 <= score <= 0.36

    def test_no_timestamp_assumes_fresh(self):
        """Document without timestamp should be assumed fresh (1.0)."""
        result = _make_result()  # No timestamp
        score = _compute_freshness_score(result)
        assert score == 1.0

    def test_uses_ingested_at_fallback(self):
        """Should fallback to ingested_at if doc_last_seen missing."""
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        result = _make_result(ingested_at=thirty_days_ago)
        score = _compute_freshness_score(result)
        assert 0.48 <= score <= 0.52

    def test_handles_unix_timestamp(self):
        """Should handle Unix timestamps (float)."""
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).timestamp()
        result = SearchResult(
            text="test",
            score=0.9,
            source_file=None,
            section=None,
            domain="test",
            metadata={"doc_last_seen": thirty_days_ago},
            doc_key="test",
        )
        score = _compute_freshness_score(result)
        assert 0.48 <= score <= 0.52


class TestApplyFreshnessFilter:
    """Tests for _apply_freshness_filter function."""

    def test_fresh_results_pass_filter(self):
        """Results above threshold should pass through."""
        now = datetime.now(timezone.utc).isoformat()
        results = [_make_result(doc_key=f"doc-{i}", doc_last_seen=now) for i in range(5)]
        
        filtered = _apply_freshness_filter(results, min_freshness=0.5)
        
        assert len(filtered) == 5
        assert all(r.freshness_score >= 0.5 for r in filtered)

    def test_stale_results_filtered_by_default(self):
        """Stale results should be filtered by default."""
        now = datetime.now(timezone.utc)
        results = [
            _make_result(doc_key="fresh", doc_last_seen=now.isoformat()),
            _make_result(doc_key="stale", doc_last_seen=(now - timedelta(days=90)).isoformat()),
        ]
        
        filtered = _apply_freshness_filter(results, min_freshness=0.5)
        
        assert len(filtered) == 1
        assert filtered[0].doc_key == "fresh"

    def test_allow_stale_includes_all(self):
        """allow_stale=True should include stale docs."""
        now = datetime.now(timezone.utc)
        results = [
            _make_result(doc_key="fresh", doc_last_seen=now.isoformat()),
            _make_result(doc_key="stale", doc_last_seen=(now - timedelta(days=90)).isoformat()),
        ]
        
        filtered = _apply_freshness_filter(results, min_freshness=0.5, allow_stale=True)
        
        assert len(filtered) == 2

    def test_empty_results_returns_empty(self):
        """Empty input should return empty output."""
        filtered = _apply_freshness_filter([], min_freshness=0.5)
        assert filtered == []


class TestResolveVersionConflicts:
    """Tests for _resolve_version_conflicts function."""

    def test_single_version_passes_through(self):
        """Single version of doc should pass unchanged."""
        now = datetime.now(timezone.utc).isoformat()
        results = [_make_result(doc_key="architecture", doc_last_seen=now)]
        
        resolved = _resolve_version_conflicts(results)
        
        assert len(resolved) == 1
        assert resolved[0].doc_key == "architecture"

    def test_keeps_freshest_version(self):
        """Multiple versions should keep the freshest one."""
        now = datetime.now(timezone.utc)
        results = [
            _make_result(doc_key="arch-v1", doc_last_seen=(now - timedelta(days=60)).isoformat()),
            _make_result(doc_key="arch-v2", doc_last_seen=now.isoformat()),
        ]
        # Compute freshness scores first (normally done by _apply_freshness_filter)
        for r in results:
            r.freshness_score = _compute_freshness_score(r)
        
        resolved = _resolve_version_conflicts(results)
        
        assert len(resolved) == 1
        assert resolved[0].doc_key == "arch-v2"

    def test_strips_various_version_suffixes(self):
        """Should handle -v1, _v2, .v3, (v4) suffixes."""
        now = datetime.now(timezone.utc).isoformat()
        results = [
            _make_result(doc_key="doc-v1", doc_last_seen=now),
            _make_result(doc_key="other_v1", doc_last_seen=now),
            _make_result(doc_key="third.v1", doc_last_seen=now),
        ]
        for r in results:
            r.freshness_score = _compute_freshness_score(r)
        
        resolved = _resolve_version_conflicts(results)
        
        # Each has unique base key, so all should pass
        assert len(resolved) == 3

    def test_empty_results_returns_empty(self):
        """Empty input should return empty output."""
        resolved = _resolve_version_conflicts([])
        assert resolved == []


class TestFreshnessConstants:
    """Tests for module-level constants."""

    def test_halflife_is_30_days(self):
        """Half-life should be 30 days."""
        assert FRESHNESS_HALFLIFE_DAYS == 30

    def test_default_threshold_is_half(self):
        """Default freshness threshold should be 0.5."""
        assert DEFAULT_MIN_FRESHNESS == 0.5
