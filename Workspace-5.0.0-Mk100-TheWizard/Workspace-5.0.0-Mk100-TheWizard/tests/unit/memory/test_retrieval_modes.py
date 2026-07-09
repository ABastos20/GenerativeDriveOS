"""Tests for RetrievalMode and filter contracts (Story 4-10/4-12).

Lock the semantics of mode-based filtering:
- NORMAL: is_latest=true, must_not is_system=true, excludes archive
- META: default domains [jarvis-core, architecture, epic, story], no must_not is_system
- TIME_SLICE: session_date filter with range support, temporal families
- HISTORICAL: no is_latest constraint, allows stale
"""

import pytest
from datetime import datetime, timezone

from jarvis.memory.retrieval.types import RetrievalMode
from jarvis.memory.retrieval.filters import (
    detect_retrieval_mode,
    parse_date_from_query,
    build_filter_for_mode as _build_filter_for_mode,
)


def _build_filter(include_stale: bool = False, include_system_docs: bool = False):
    """Backward-compatible wrapper for old _build_filter API.
    
    Maps to build_filter_for_mode with NORMAL mode for standard cases,
    and HISTORICAL mode when include_stale is True.
    """
    mode = RetrievalMode.HISTORICAL if include_stale else RetrievalMode.NORMAL
    return _build_filter_for_mode(
        mode=mode,
        include_system_docs=include_system_docs,
        allow_stale=include_stale,
    )


class TestRetrievalModeDetection:
    """Test automatic mode detection from query semantics."""

    def test_normal_mode_default(self):
        """Default queries should return NORMAL mode."""
        mode, date = detect_retrieval_mode("What is the hydrogen water loop concept?")
        assert mode == RetrievalMode.NORMAL
        assert date is None

    def test_meta_mode_jarvis_architecture(self):
        """Questions about Jarvis should trigger META mode."""
        mode, date = detect_retrieval_mode("How is Jarvis's memory architecture designed?")
        assert mode == RetrievalMode.META
        assert date is None

    def test_meta_mode_operating_manual(self):
        """Operating manual queries should trigger META mode."""
        mode, date = detect_retrieval_mode("Show me the Jarvis operating manual")
        assert mode == RetrievalMode.META
        assert date is None

    def test_meta_mode_council_of_ricks(self):
        """Council of Ricks queries should trigger META mode."""
        mode, date = detect_retrieval_mode("How does the council of ricks work?")
        assert mode == RetrievalMode.META
        assert date is None

    def test_time_slice_mode_with_date(self):
        """Queries with explicit dates should trigger TIME_SLICE mode."""
        mode, date = detect_retrieval_mode("What happened on 2025-12-03?")
        assert mode == RetrievalMode.TIME_SLICE
        assert date is not None
        assert date.year == 2025
        assert date.month == 12
        assert date.day == 3

    def test_historical_mode_archive(self):
        """Archive/historical queries should trigger HISTORICAL mode."""
        mode, date = detect_retrieval_mode("Show me the original PRD")
        assert mode == RetrievalMode.HISTORICAL
        assert date is None

    def test_historical_mode_legacy(self):
        """Legacy queries should trigger HISTORICAL mode."""
        mode, date = detect_retrieval_mode("What was the old version of the architecture?")
        assert mode == RetrievalMode.HISTORICAL
        assert date is None


class TestDateParsing:
    """Test date extraction from queries."""

    def test_iso_date_format(self):
        """Should parse YYYY-MM-DD format."""
        date = parse_date_from_query("Meeting on 2025-12-03")
        assert date is not None
        assert date.year == 2025
        assert date.month == 12
        assert date.day == 3

    def test_slash_date_format(self):
        """Should parse YYYY/MM/DD format."""
        date = parse_date_from_query("Meeting on 2025/11/17")
        assert date is not None
        assert date.year == 2025
        assert date.month == 11
        assert date.day == 17

    def test_no_date_returns_none(self):
        """Should return None when no date present."""
        date = parse_date_from_query("What is the architecture?")
        assert date is None


class TestBuildFilter:
    """Test the core _build_filter function."""

    def test_normal_mode_excludes_system(self):
        """NORMAL mode should exclude is_system=true docs."""
        flt = _build_filter(include_stale=False, include_system_docs=False)
        assert flt is not None
        
        # Should have is_latest=true in must
        assert flt.must is not None
        is_latest_cond = next((c for c in flt.must if c.key == "is_latest"), None)
        assert is_latest_cond is not None
        
        # Should have is_system=true in must_not
        assert flt.must_not is not None
        is_system_cond = next((c for c in flt.must_not if c.key == "is_system"), None)
        assert is_system_cond is not None

    def test_meta_mode_includes_system(self):
        """META mode should include system docs."""
        flt = _build_filter(include_stale=False, include_system_docs=True)
        assert flt is not None
        
        # Should still have is_latest=true in must
        is_latest_cond = next((c for c in flt.must if c.key == "is_latest"), None)
        assert is_latest_cond is not None
        
        # Should NOT have is_system in must_not
        if flt.must_not:
            is_system_cond = next((c for c in flt.must_not if c.key == "is_system"), None)
            assert is_system_cond is None

    def test_historical_mode_no_is_latest(self):
        """HISTORICAL mode should not require is_latest=true."""
        flt = _build_filter(include_stale=True, include_system_docs=False)
        
        # Should NOT have is_latest=true in must
        if flt and flt.must:
            is_latest_cond = next((c for c in flt.must if c.key == "is_latest"), None)
            assert is_latest_cond is None


class TestBuildFilterForModeCanonical:
    """Test canonical mode-based filter builder per architect spec (Story 4-12)."""

    def test_normal_mode_excludes_archive(self):
        """NORMAL mode should exclude archive semantic_family."""
        flt = _build_filter_for_mode(
            mode=RetrievalMode.NORMAL,
            include_system_docs=False,
            allow_stale=False,
        )
        assert flt is not None
        
        # Should have semantic_family != archive in must_not
        assert flt.must_not is not None
        archive_cond = next(
            (c for c in flt.must_not if c.key == "semantic_family"), None
        )
        assert archive_cond is not None

    def test_normal_mode_requires_is_latest(self):
        """NORMAL mode should require is_latest=true."""
        flt = _build_filter_for_mode(
            mode=RetrievalMode.NORMAL,
            include_system_docs=False,
            allow_stale=False,
        )
        assert flt is not None
        
        # Should have is_latest=true in must
        is_latest_cond = next((c for c in flt.must if c.key == "is_latest"), None)
        assert is_latest_cond is not None

    def test_normal_mode_excludes_system(self):
        """NORMAL mode should exclude system docs."""
        flt = _build_filter_for_mode(
            mode=RetrievalMode.NORMAL,
            include_system_docs=False,
            allow_stale=False,
        )
        assert flt is not None
        
        # Should have is_system=true in must_not
        assert flt.must_not is not None
        is_system_cond = next((c for c in flt.must_not if c.key == "is_system"), None)
        assert is_system_cond is not None

    def test_meta_mode_defaults_to_core_domains(self):
        """META mode should default to core domains when none specified."""
        flt = _build_filter_for_mode(
            mode=RetrievalMode.META,
            include_system_docs=True,
            allow_stale=False,
        )
        assert flt is not None
        
        # Should have domain filter with core domains
        domain_cond = next((c for c in flt.must if c.key == "domain"), None)
        assert domain_cond is not None
        # Should include jarvis-core
        assert "jarvis-core" in domain_cond.match.any

    def test_meta_mode_no_system_exclusion(self):
        """META mode with include_system_docs=True should not exclude system."""
        flt = _build_filter_for_mode(
            mode=RetrievalMode.META,
            include_system_docs=True,
            allow_stale=False,
        )
        
        # Should NOT have is_system in must_not
        if flt and flt.must_not:
            is_system_cond = next((c for c in flt.must_not if c.key == "is_system"), None)
            assert is_system_cond is None

    def test_time_slice_temporal_families(self):
        """TIME_SLICE mode should filter to temporal semantic families."""
        flt = _build_filter_for_mode(
            mode=RetrievalMode.TIME_SLICE,
            include_system_docs=False,
            allow_stale=True,
            time_slice="2025-12-03",
        )
        assert flt is not None
        
        # Should have semantic_family filter
        family_cond = next((c for c in flt.must if c.key == "semantic_family"), None)
        assert family_cond is not None
        assert "session-log" in family_cond.match.any

    def test_time_slice_date_filter(self):
        """TIME_SLICE mode should filter on session_date."""
        flt = _build_filter_for_mode(
            mode=RetrievalMode.TIME_SLICE,
            include_system_docs=False,
            allow_stale=True,
            time_slice="2025-12-03",
        )
        assert flt is not None
        
        # Should have session_date filter
        date_cond = next((c for c in flt.must if c.key == "session_date"), None)
        assert date_cond is not None

    # TODO: Re-enable when Qdrant Range API is properly integrated
    # def test_time_slice_date_range(self):
    #     """TIME_SLICE mode should support date ranges."""
    #     flt = _build_filter_for_mode(
    #         mode=RetrievalMode.TIME_SLICE,
    #         include_system_docs=False,
    #         allow_stale=True,
    #         time_slice=("2025-12-01", "2025-12-07"),
    #     )
    #     assert flt is not None
    #     date_cond = next((c for c in flt.must if c.key == "session_date"), None)
    #     assert date_cond is not None

    def test_time_slice_no_is_latest(self):
        """TIME_SLICE mode should NOT enforce is_latest (allows history)."""
        flt = _build_filter_for_mode(
            mode=RetrievalMode.TIME_SLICE,
            include_system_docs=False,
            allow_stale=True,
            time_slice="2025-12-03",
        )
        
        # Should NOT have is_latest in must
        if flt and flt.must:
            is_latest_cond = next((c for c in flt.must if c.key == "is_latest"), None)
            assert is_latest_cond is None

    def test_historical_mode_no_is_latest(self):
        """HISTORICAL mode should NOT enforce is_latest."""
        flt = _build_filter_for_mode(
            mode=RetrievalMode.HISTORICAL,
            include_system_docs=False,
            allow_stale=True,
        )
        
        # Should NOT have is_latest in must
        if flt and flt.must:
            is_latest_cond = next((c for c in flt.must if c.key == "is_latest"), None)
            assert is_latest_cond is None

    def test_historical_mode_excludes_system(self):
        """HISTORICAL mode should still exclude system docs by default."""
        flt = _build_filter_for_mode(
            mode=RetrievalMode.HISTORICAL,
            include_system_docs=False,
            allow_stale=True,
        )
        assert flt is not None
        
        # Should have is_system=true in must_not
        assert flt.must_not is not None
        is_system_cond = next((c for c in flt.must_not if c.key == "is_system"), None)
        assert is_system_cond is not None
