"""Query intent analysis for autonomous grounding level selection.

This module analyzes user queries to determine their intent and automatically
selects the appropriate grounding level:
- Factual queries → strict (no hallucination tolerance)
- Creative queries → soft (allow bridging with speculation markers)
- Explanatory queries → balanced (cite major claims, allow inference)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

import structlog

logger = structlog.get_logger(__name__)

GroundingLevel = Literal["soft", "balanced", "strict"]


@dataclass
class QueryIntent:
    """Classified query intent with confidence."""

    intent_type: Literal["factual", "creative", "explanatory"]
    grounding_level: GroundingLevel
    confidence: float
    reasoning: str


# Pattern definitions for intent classification
FACTUAL_PATTERNS = [
    # Questions asking for specific facts
    r"\b(what is|what are|define|definition of|version|current|status of)\b",
    # Questions asking for documentation
    r"\b(how does|how do|explain how|describe how)\b.*\b(work|function|operate)\b",
    # Questions asking for specifications
    r"\b(spec|specification|requirement|configuration|setting|parameter)\b",
    # Questions asking for current state
    r"\b(show me|list|display|get|fetch|retrieve)\b",
    # Technical queries
    r"\b(error|bug|issue|problem|fail|crash)\b",
]

CREATIVE_PATTERNS = [
    # Brainstorming
    r"\b(brainstorm|ideas for|suggest|propose|imagine|design)\b",
    # Naming
    r"\b(name|naming|call it|names for)\b",
    # Innovation
    r"\b(innovate|improve|optimize|enhance|better way)\b",
    # Future-oriented
    r"\b(could we|should we|what if|possible to)\b",
    # Exploration
    r"\b(explore|experiment|try|test|prototype)\b",
]

EXPLANATORY_PATTERNS = [
    # High-level explanations
    r"\b(explain|describe|walk through|overview|summary)\b",
    # Conceptual understanding
    r"\b(why|reason|purpose|goal|objective)\b",
    # Architecture/design
    r"\b(architecture|design|structure|pattern|approach)\b",
    # Data flow
    r"\b(flow|pipeline|process|workflow|sequence)\b",
]


def _compile_patterns(patterns: list[str]) -> list[re.Pattern]:
    """Compile regex patterns for efficient matching."""
    return [re.compile(p, re.IGNORECASE) for p in patterns]


_FACTUAL_COMPILED = _compile_patterns(FACTUAL_PATTERNS)
_CREATIVE_COMPILED = _compile_patterns(CREATIVE_PATTERNS)
_EXPLANATORY_COMPILED = _compile_patterns(EXPLANATORY_PATTERNS)


def _match_score(query: str, patterns: list[re.Pattern]) -> float:
    """Calculate match score for a query against pattern list."""
    matches = sum(1 for pattern in patterns if pattern.search(query))
    # Normalize by pattern count to get 0.0-1.0 score
    return matches / len(patterns) if patterns else 0.0


def analyze_intent(query: str, *, force_grounding: GroundingLevel | None = None) -> QueryIntent:
    """Analyze query intent and recommend grounding level.

    Args:
        query: User's natural language query
        force_grounding: Optional override to force specific grounding level

    Returns:
        QueryIntent with classified type and recommended grounding level

    Examples:
        >>> analyze_intent("What is the current version of the auth API?")
        QueryIntent(intent_type='factual', grounding_level='strict', ...)

        >>> analyze_intent("Brainstorm names for the new logging service")
        QueryIntent(intent_type='creative', grounding_level='soft', ...)

        >>> analyze_intent("Explain the data flow for user profiles")
        QueryIntent(intent_type='explanatory', grounding_level='balanced', ...)
    """
    if force_grounding:
        logger.info(
            "intent_analysis_skipped",
            query=query[:100],
            forced_grounding=force_grounding,
        )
        return QueryIntent(
            intent_type="explanatory",  # Neutral default when forced
            grounding_level=force_grounding,
            confidence=1.0,
            reasoning=f"Grounding level manually forced to {force_grounding}",
        )

    query_lower = query.lower()

    # Calculate match scores for each intent type
    factual_score = _match_score(query_lower, _FACTUAL_COMPILED)
    creative_score = _match_score(query_lower, _CREATIVE_COMPILED)
    explanatory_score = _match_score(query_lower, _EXPLANATORY_COMPILED)

    # Determine dominant intent
    scores = {
        "factual": factual_score,
        "creative": creative_score,
        "explanatory": explanatory_score,
    }

    # Get intent with highest score
    intent_type = max(scores, key=scores.get)  # type: ignore[arg-type]
    confidence = scores[intent_type]

    # Map intent to grounding level
    grounding_map = {
        "factual": "strict",
        "creative": "soft",
        "explanatory": "balanced",
    }

    grounding_level = grounding_map[intent_type]

    reasoning = (
        f"Query matched {intent_type} patterns with {confidence:.2f} confidence. "
        f"Scores: factual={factual_score:.2f}, creative={creative_score:.2f}, "
        f"explanatory={explanatory_score:.2f}"
    )

    logger.info(
        "query_intent_analyzed",
        query=query[:100],
        intent_type=intent_type,
        grounding_level=grounding_level,
        confidence=confidence,
    )

    return QueryIntent(
        intent_type=intent_type,  # type: ignore[arg-type]
        grounding_level=grounding_level,  # type: ignore[arg-type]
        confidence=confidence,
        reasoning=reasoning,
    )
