from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jarvis.memory.gap_analyzer import (
    CoherenceAnalyzer,
    CoverageAnalyzer,
    GapAnalysisConfig,
    RecencyAnalyzer,
)
from jarvis.memory.search import SearchResult


def _result(text: str, **metadata: object) -> SearchResult:
    return SearchResult(
        text=text,
        score=0.5,
        source_file="docs/example.md",
        section=None,
        domain="jarvis-core",
        metadata=metadata,
    )


def test_coverage_analyzer_scores_missing_terms() -> None:
    config = GapAnalysisConfig(coverage_threshold=0.6)
    analyzer = CoverageAnalyzer(config)

    results = [
        _result("Jarvis uses RAG with coverage analysis and recency checks."),
        _result("Gap detection improves research planning and synthesis."),
    ]

    analysis = analyzer.analyze("coverage recency coherence research gaps", results)

    assert 0.0 < analysis.coverage_score < 1.0
    assert "coverage" in analysis.grounded_terms
    assert "coherence" in analysis.missing_terms
    assert analysis.gap_detected is True


def test_recency_analyzer_detects_stale_and_sparse() -> None:
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    stale_date = (now - timedelta(days=120)).isoformat()
    fresh_date = (now - timedelta(days=5)).isoformat()
    config = GapAnalysisConfig(recency_stale_days=90, recency_sparse_days=30, min_recency_results=2)
    analyzer = RecencyAnalyzer(config)

    stale_analysis = analyzer.analyze([_result("old", verified_at=stale_date)], now=now)
    assert stale_analysis.status == "STALE"
    assert stale_analysis.gap_detected is True

    sparse_analysis = analyzer.analyze(
        [
            _result("fresh", verified_at=fresh_date),
        ],
        now=now,
    )
    assert sparse_analysis.status == "SPARSE"
    assert sparse_analysis.gap_detected is True

    missing_analysis = analyzer.analyze([], now=now)
    assert missing_analysis.status == "MISSING"
    assert missing_analysis.gap_detected is True


def test_coherence_analyzer_flags_contradiction_when_overlap_low() -> None:
    config = GapAnalysisConfig(coherence_threshold=0.5)
    analyzer = CoherenceAnalyzer(config)

    coherent_results = [
        _result("Jarvis gap analysis checks coverage and recency."),
        _result("Coverage and recency metrics improve answers."),
    ]
    coherent = analyzer.analyze(coherent_results)
    assert coherent.contradictory is False
    assert coherent.coherence_score > 0.5

    contradictory_results = [
        _result("Jarvis found no gaps and skipped research."),
        _result("Jarvis detected major contradictions needing research."),
    ]
    contradictory = analyzer.analyze(contradictory_results)
    assert contradictory.contradictory is True
    assert contradictory.coherence_score < 0.5
