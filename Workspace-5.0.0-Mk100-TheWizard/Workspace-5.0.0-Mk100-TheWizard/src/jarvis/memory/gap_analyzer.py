"""Gap analysis utilities for coverage, recency, and coherence detection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional, Sequence

from jarvis.memory.retrieval.types import SearchResult


@dataclass
class GapAnalysisConfig:
    coverage_threshold: float = 0.6
    recency_stale_days: int = 90
    recency_sparse_days: int = 30
    min_recency_results: int = 1
    coherence_threshold: float = 0.35


@dataclass
class CoverageAnalysis:
    coverage_score: float
    grounded_terms: set[str]
    missing_terms: set[str]
    gap_detected: bool


@dataclass
class RecencyAnalysis:
    average_age_days: Optional[float]
    newest_age_days: Optional[float]
    oldest_age_days: Optional[float]
    status: str
    gap_detected: bool


@dataclass
class CoherenceAnalysis:
    coherence_score: float
    contradictory: bool
    pair_count: int


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t]


def _parse_datetime(value: object) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


class CoverageAnalyzer:
    def __init__(self, config: GapAnalysisConfig) -> None:
        self.config = config

    def analyze(self, query: str, results: Sequence[SearchResult]) -> CoverageAnalysis:
        query_terms = set(_tokenize(query))
        if not query_terms:
            return CoverageAnalysis(coverage_score=0.0, grounded_terms=set(), missing_terms=set(), gap_detected=True)

        combined_context = " ".join(res.text for res in results if res.text)
        context_terms = set(_tokenize(combined_context))

        grounded_terms = {term for term in query_terms if term in context_terms}
        missing_terms = query_terms - grounded_terms
        coverage_score = len(grounded_terms) / len(query_terms)
        # Treat boundary score as a gap to trigger research when coverage is marginal.
        gap_detected = coverage_score <= self.config.coverage_threshold

        return CoverageAnalysis(
            coverage_score=coverage_score,
            grounded_terms=grounded_terms,
            missing_terms=missing_terms,
            gap_detected=gap_detected,
        )


class RecencyAnalyzer:
    def __init__(self, config: GapAnalysisConfig) -> None:
        self.config = config

    def _extract_dates(self, results: Sequence[SearchResult]) -> list[datetime]:
        collected: list[datetime] = []
        for res in results:
            meta = res.metadata or {}
            for key in ("verified_at", "updated_at", "created_at", "timestamp"):
                parsed = _parse_datetime(meta.get(key))
                if parsed:
                    collected.append(parsed)
                    break
        return collected

    def analyze(self, results: Sequence[SearchResult], now: Optional[datetime] = None) -> RecencyAnalysis:
        if not results:
            return RecencyAnalysis(
                average_age_days=None,
                newest_age_days=None,
                oldest_age_days=None,
                status="MISSING",
                gap_detected=True,
            )

        now = now or datetime.now(timezone.utc)
        dates = self._extract_dates(results)

        if not dates:
            return RecencyAnalysis(
                average_age_days=None,
                newest_age_days=None,
                oldest_age_days=None,
                status="SPARSE",
                gap_detected=True,
            )

        ages = sorted([(now - dt).total_seconds() / 86400 for dt in dates])
        average_age = sum(ages) / len(ages)
        newest = ages[0]
        oldest = ages[-1]

        if oldest > self.config.recency_stale_days:
            status = "STALE"
            gap = True
        elif len(dates) < self.config.min_recency_results or average_age > self.config.recency_sparse_days:
            status = "SPARSE"
            gap = True
        else:
            status = "FRESH"
            gap = False

        return RecencyAnalysis(
            average_age_days=average_age,
            newest_age_days=newest,
            oldest_age_days=oldest,
            status=status,
            gap_detected=gap,
        )


class CoherenceAnalyzer:
    def __init__(self, config: GapAnalysisConfig) -> None:
        self.config = config

    def _pairwise_similarity(self, tokens_list: list[set[str]]) -> tuple[float, int]:
        if len(tokens_list) < 2:
            return 1.0, 0

        scores: list[float] = []
        for idx, left in enumerate(tokens_list):
            for right in tokens_list[idx + 1 :]:
                min_len = min(len(left), len(right))
                if min_len == 0:
                    scores.append(0.0)
                    continue
                intersection = left & right
                # Overlap coefficient with a small bonus when any intersection exists to avoid
                # razor-thin borderline scores on near-matching snippets.
                overlap = len(intersection) / min_len
                if intersection:
                    overlap = min(1.0, overlap + 0.1)
                scores.append(overlap)
        avg = sum(scores) / len(scores) if scores else 1.0
        return avg, len(scores)

    def analyze(self, results: Sequence[SearchResult]) -> CoherenceAnalysis:
        if not results:
            return CoherenceAnalysis(coherence_score=0.0, contradictory=False, pair_count=0)

        tokens_list = [set(_tokenize(res.text)) for res in results if res.text]
        coherence_score, pair_count = self._pairwise_similarity(tokens_list)
        contradictory = coherence_score < self.config.coherence_threshold

        return CoherenceAnalysis(
            coherence_score=coherence_score,
            contradictory=contradictory,
            pair_count=pair_count,
        )
