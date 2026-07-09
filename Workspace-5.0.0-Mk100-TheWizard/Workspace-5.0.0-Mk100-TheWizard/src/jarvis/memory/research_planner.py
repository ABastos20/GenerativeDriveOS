"""Research planning helpers for autonomous research mode."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence

from jarvis.llm.client import call_llm


@dataclass
class ResearchPlanConfig:
    max_queries: int = 3
    min_queries: int = 2
    provider: str = "auto"


@dataclass
class ResearchQuery:
    query: str
    reason: str


@dataclass
class ResearchPlan:
    queries: List[ResearchQuery]
    gap_types: List[str]
    coverage_score: float
    recency_status: str
    coherence_score: float


def _extract_terms(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2]


class ResearchPlanner:
    """Generates targeted research queries from gap analysis."""

    def __init__(
        self,
        config: ResearchPlanConfig | None = None,
        llm_client: Callable[..., object] | None = None,
    ) -> None:
        self.config = config or ResearchPlanConfig()
        self._llm_client = llm_client or call_llm

    @staticmethod
    def _parse_llm_response(response: object, max_queries: int) -> list[ResearchQuery]:
        """Parse LLM response lines into ResearchQuery objects."""
        lines = response.content.splitlines() if hasattr(response, "content") else []
        queries: list[ResearchQuery] = []
        for line in lines:
            line = line.strip(" -•\t")
            if not line:
                continue
            queries.append(ResearchQuery(query=line, reason="llm_suggested"))
            if len(queries) >= max_queries:
                break
        return queries

    def _llm_generate(
        self,
        question: str,
        missing_terms: Sequence[str],
        gap_types: Sequence[str],
        max_queries: int,
    ) -> list[ResearchQuery]:
        from jarvis.memory.research_helpers import parse_llm_response
        prompt = (
            "You generate targeted web research queries.\n"
            f"User question: {question}\n"
            f"Gaps: {', '.join(gap_types) or 'none'}\n"
            f"Missing terms: {', '.join(missing_terms) or 'none'}\n"
            f"Return {max_queries} concise search queries that will close these gaps.\n"
            "Focus on specific keywords and entities. Do NOT repeat the full user question."
        )
        response = self._llm_client(
            prompt=prompt,
            system="Generate research search queries only; one per line.",
            provider=self.config.provider,
            max_tokens=200,
        )
        return parse_llm_response(response, max_queries)

    def _fallback_queries(
        self,
        question: str,
        missing_terms: Sequence[str],
        max_queries: int,
    ) -> list[ResearchQuery]:
        from jarvis.memory.research_helpers import generate_fallback_queries
        return generate_fallback_queries(question, missing_terms, max_queries)

    def _generate_queries(
        self,
        question: str,
        missing_terms: Sequence[str],
        gap_types: Sequence[str],
        limit: int,
    ) -> list[ResearchQuery]:
        """Generate research queries using LLM or fallback."""
        queries = self._llm_generate(question, missing_terms, gap_types, limit)
        if len(queries) < self.config.min_queries:
            queries = self._fallback_queries(question, missing_terms, limit)
        return queries

    def _detect_gap_types(self, gap: dict) -> list[str]:
        """Identify types of gaps present in analysis."""
        types = []
        if gap.get("coverage_gap"):
            types.append("COVERAGE")
        if gap.get("recency_gap"):
            types.append("RECENCY")
        if gap.get("contradictory"):
            types.append("COHERENCE")
        if gap.get("missing_terms"):
            types.append("SPECIFICITY")
        return types

    def plan(
        self,
        question: str,
        gap_analysis: dict,
        max_queries: int | None = None,
    ) -> ResearchPlan:
        limit = max_queries or self.config.max_queries
        limit = max(self.config.min_queries, min(limit, self.config.max_queries))

        gap_types = self._detect_gap_types(gap_analysis)
        missing_terms = gap_analysis.get("missing_terms") or []
        queries = self._generate_queries(question, missing_terms, gap_types, limit)

        return ResearchPlan(
            queries=queries,
            gap_types=gap_types,
            coverage_score=float(gap_analysis.get("coverage_score", 0.0)),
            recency_status=str(gap_analysis.get("recency_status", "UNKNOWN")),
            coherence_score=float(gap_analysis.get("coherence_score", 0.0)),
        )
