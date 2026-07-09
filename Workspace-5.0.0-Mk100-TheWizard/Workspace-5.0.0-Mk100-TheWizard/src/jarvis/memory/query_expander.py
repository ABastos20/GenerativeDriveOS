"""Query expansion for improved RAG retrieval.

Generates alternative phrasings of user queries to improve recall for
ambiguous or underspecified questions.
"""

from __future__ import annotations

import re
from typing import List

import structlog

logger = structlog.get_logger("jarvis.memory.query_expander")


# Synonym mappings for common technical terms
SYNONYM_MAP = {
    "optimize": ["improve", "enhance", "tune", "boost"],
    "fix": ["resolve", "repair", "correct", "debug"],
    "create": ["build", "generate", "make", "construct"],
    "delete": ["remove", "erase", "drop", "eliminate"],
    "update": ["modify", "change", "revise", "alter"],
    "show": ["display", "list", "view", "present"],
    "find": ["search", "locate", "discover", "retrieve"],
    "explain": ["describe", "clarify", "detail", "elaborate"],
    "implement": ["build", "create", "develop", "code"],
    "test": ["verify", "validate", "check", "examine"],
}


# Question reformulation patterns
QUESTION_PATTERNS = [
    (r"^how (?:do|can) i (.+)\??$", ["steps to {}", "{} tutorial", "{} guide", "how to {}"]),
    (r"^what is (.+)\??$", ["{} definition", "{} overview", "explain {}", "about {}"]),
    (r"^why (.+)\??$", ["reason for {}", "{} explanation", "rationale behind {}"]),
    (r"^when (?:should|do) (?:i|we) (.+)\??$", ["best time to {}", "{} timing", "when to {}"]),
    (r"^where (?:is|are) (.+)\??$", ["location of {}", "{} whereabouts", "find {}"]),
]


def expand_query(query: str, count: int = 2) -> List[str]:
    """Generate alternative phrasings of a query using heuristics.

    This function uses lightweight heuristic strategies to expand queries
    without requiring LLM calls, ensuring low latency and no API costs.

    Strategies:
    1. Synonym replacement for common technical terms
    2. Question reformulation patterns (How/What/Why/When/Where)
    3. Keyword extraction with variants

    Args:
        query: Original user query text.
        count: Number of expansions to generate (0-5).
               0 returns only original query.
               1-5 returns original + N expansions.

    Returns:
        List of query strings. First element is always the original query,
        followed by up to `count` expansions.

    Raises:
        ValueError: If count is outside valid range [0, 5].

    Examples:
        >>> expand_query("How do I optimize PostgreSQL?", count=2)
        ['How do I optimize PostgreSQL?', 'How do I improve PostgreSQL?',
         'Steps to optimize PostgreSQL']

        >>> expand_query("What is RAG?", count=1)
        ['What is RAG?', 'RAG definition']

        >>> expand_query("Any query", count=0)
        ['Any query']
    """
    if count < 0 or count > 5:
        raise ValueError(f"count must be between 0 and 5, got {count}")

    stripped_query = query.strip()
    if not stripped_query:
        logger.warning("expand_query_empty_input")
        return [query]

    expansions: List[str] = [stripped_query]

    if count == 0:
        logger.info("expand_query_disabled", count=count)
        return expansions

    # Strategy 1: Question reformulation (highest priority)
    question_expansions = _expand_via_question_patterns(stripped_query)
    for expansion in question_expansions:
        if len(expansions) >= count + 1:
            break
        if expansion not in expansions:
            expansions.append(expansion)

    # Strategy 2: Synonym replacement
    if len(expansions) < count + 1:
        synonym_expansions = _expand_via_synonyms(stripped_query)
        for expansion in synonym_expansions:
            if len(expansions) >= count + 1:
                break
            if expansion not in expansions:
                expansions.append(expansion)

    # Strategy 3: Keyword extraction (fallback if still need more)
    if len(expansions) < count + 1:
        keyword_expansions = _expand_via_keywords(stripped_query)
        for expansion in keyword_expansions:
            if len(expansions) >= count + 1:
                break
            if expansion not in expansions:
                expansions.append(expansion)

    # Log expansion results
    logger.info(
        "expand_query_completed",
        original_query=stripped_query,
        requested_count=count,
        generated_count=len(expansions) - 1,
        expansions=expansions[1:],
    )

    return expansions


def _expand_via_question_patterns(query: str) -> List[str]:
    """Apply question reformulation patterns to generate variants.

    Detects question patterns (How/What/Why/When/Where) and generates
    alternative phrasings using predefined templates.
    """
    query_lower = query.lower()
    expansions: List[str] = []

    for pattern, templates in QUESTION_PATTERNS:
        match = re.match(pattern, query_lower)
        if match:
            captured = match.group(1)
            for template in templates:
                expansion = template.format(captured)
                expansions.append(expansion)
            break  # Only apply first matching pattern

    return expansions


def _expand_via_synonyms(query: str) -> List[str]:
    """Replace key technical terms with synonyms to generate variants.

    Uses SYNONYM_MAP to identify replaceable terms and generates
    alternative queries with synonym substitutions.
    """
    query_lower = query.lower()
    expansions: List[str] = []

    for term, synonyms in SYNONYM_MAP.items():
        # Match whole words only (avoid partial matches like "test" in "latest")
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, query_lower):
            for synonym in synonyms[:2]:  # Limit to 2 synonyms per term
                expansion = re.sub(pattern, synonym, query_lower, count=1)
                if expansion != query_lower:
                    expansions.append(expansion)

    return expansions


def _expand_via_keywords(query: str) -> List[str]:
    """Extract key terms and generate keyword-focused variants.

    This is a fallback strategy that extracts significant words
    (excluding stop words) and creates simplified queries.
    """
    # Common stop words to exclude
    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "should",
        "could", "may", "might", "can", "of", "in", "on", "at", "to", "for",
        "with", "by", "from", "about", "i", "you", "we", "they", "it", "this",
        "that", "these", "those", "how", "what", "when", "where", "why", "who",
    }

    # Extract words (alphanumeric sequences)
    words = re.findall(r"\b\w+\b", query.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]

    expansions: List[str] = []

    # Generate keyword-only query (simplified)
    if len(keywords) >= 2:
        keyword_query = " ".join(keywords[:4])  # Use top 4 keywords
        expansions.append(keyword_query)

    # Generate "about {keywords}" variant
    if len(keywords) >= 1:
        about_query = f"about {' '.join(keywords[:3])}"
        expansions.append(about_query)

    return expansions
