"""Research planner helpers - Separated for complexity compliance.

Contains parsing and gap detection logic extracted from ResearchPlanner.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from jarvis.llm.client import call_llm


@dataclass
class ResearchQuery:
    query: str
    reason: str


def extract_terms(text: str) -> list[str]:
    """Extract keyword terms from text."""
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2]


def parse_llm_response(response: object, max_queries: int) -> list[ResearchQuery]:
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


def detect_gap_types(gap_analysis: dict) -> list[str]:
    """Detect gap types from analysis results."""
    gap_types: list[str] = []
    if gap_analysis.get("coverage_gap"):
        gap_types.append("COVERAGE")
    if gap_analysis.get("recency_gap"):
        gap_types.append(gap_analysis.get("recency_status", "RECENCY"))
    if gap_analysis.get("contradictory"):
        gap_types.append("CONTRADICTORY")
    return gap_types


def generate_fallback_queries(
    question: str,
    missing_terms: Sequence[str],
    max_queries: int,
) -> list[ResearchQuery]:
    """Generate fallback queries from terms."""
    terms = extract_terms(question)[:3]
    seeds = list(missing_terms)[:3] or terms
    queries: list[ResearchQuery] = []
    for term in seeds:
        if len(queries) >= max_queries:
            break
        queries.append(ResearchQuery(query=f"{term} overview", reason="fallback_term"))
    return queries
