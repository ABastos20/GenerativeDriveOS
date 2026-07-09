"""Auto-learning heuristics by mining LLM-classified keywords.

This module analyzes chunks that were classified via LLM fallback and
extracts common keywords that could be added to heuristic mappings to
reduce future LLM calls.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import re

import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from jarvis.database import qdrant as qdrant_db
from jarvis.memory.domain_heuristics import CHAVAO_DOMAIN_MAP

logger = structlog.get_logger(__name__)


def extract_keywords(text: str, min_length: int = 3, max_length: int = 50) -> List[str]:
    """Extract potential keywords from text.

    Args:
        text: Source text
        min_length: Minimum keyword length
        max_length: Maximum keyword length

    Returns:
        List of potential keywords (lowercased, cleaned)
    """
    # Lowercase
    text = text.lower()

    # Extract multi-word phrases (2-4 words) and single words
    keywords = []

    # Multi-word phrases (2-4 words)
    # Match word boundaries with optional hyphens, underscores, dots
    pattern = r'\b[a-z][a-z0-9_\-\.]*(?:\s+[a-z][a-z0-9_\-\.]*){1,3}\b'
    for match in re.finditer(pattern, text):
        phrase = match.group()
        if min_length <= len(phrase) <= max_length:
            keywords.append(phrase.strip())

    # Single technical terms (camelCase, snake_case, kebab-case, dots)
    pattern = r'\b[a-z][a-z0-9_\-\.]{2,}\b'
    for match in re.finditer(pattern, text):
        term = match.group()
        if min_length <= len(term) <= max_length:
            keywords.append(term)

    return keywords


def mine_llm_classified_keywords(
    collection_name: str = "knowledge",
    min_occurrences: int = 10,
    max_suggestions: int = 50,
) -> Dict[str, List[Tuple[str, int]]]:
    """Mine keywords from LLM-classified chunks and suggest heuristic additions.

    Args:
        collection_name: Qdrant collection to analyze
        min_occurrences: Minimum times a keyword must appear
        max_suggestions: Maximum suggestions per domain

    Returns:
        Dict mapping domain -> [(keyword, count), ...]
    """
    client: QdrantClient = qdrant_db.get_qdrant_client()

    logger.info(
        "mining_llm_keywords",
        collection=collection_name,
        min_occurrences=min_occurrences,
    )

    # Scroll all points classified by LLM
    filter_condition = Filter(
        must=[
            FieldCondition(
                key="domain_source",
                match=MatchValue(value="llm"),
            )
        ]
    )

    # Group keywords by domain
    domain_keywords: Dict[str, Counter] = defaultdict(Counter)

    offset = None
    total_chunks = 0

    while True:
        try:
            results = client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            points, next_offset = results

            if not points:
                break

            for point in points:
                payload = point.payload or {}
                domain = payload.get("domain", "unknown")
                text = payload.get("text", "")

                if not text or domain == "unknown":
                    continue

                # Extract keywords from text
                keywords = extract_keywords(text)

                # Count keywords for this domain
                for kw in keywords:
                    # Skip if already in heuristics
                    if kw not in CHAVAO_DOMAIN_MAP:
                        domain_keywords[domain][kw] += 1

                total_chunks += 1

            if next_offset is None:
                break
            offset = next_offset

        except Exception as e:
            logger.error("mining_error", error=str(e))
            break

    logger.info(
        "mining_complete",
        total_chunks=total_chunks,
        domains_found=len(domain_keywords),
    )

    # Filter and sort suggestions
    suggestions: Dict[str, List[Tuple[str, int]]] = {}

    for domain, counter in domain_keywords.items():
        # Get keywords that appear >= min_occurrences
        frequent = [
            (kw, count)
            for kw, count in counter.most_common()
            if count >= min_occurrences
        ]

        if frequent:
            suggestions[domain] = frequent[:max_suggestions]

    return suggestions


def format_keyword_suggestions(
    suggestions: Dict[str, List[Tuple[str, int]]],
    top_domains: int = 10,
) -> str:
    """Format keyword suggestions for CLI output.

    Args:
        suggestions: Domain -> [(keyword, count)] mapping
        top_domains: Number of top domains to show

    Returns:
        Formatted string for CLI display
    """
    lines = ["Keyword Suggestions for Heuristic Expansion", "=" * 60, ""]

    # Sort domains by total keyword frequency
    domain_totals = {
        domain: sum(count for _, count in keywords)
        for domain, keywords in suggestions.items()
    }

    sorted_domains = sorted(
        domain_totals.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:top_domains]

    for domain, total in sorted_domains:
        keywords = suggestions[domain]
        lines.append(f"Domain: {domain}")
        lines.append(f"  Total keyword occurrences: {total}")
        lines.append(f"  Suggested additions ({len(keywords)}):")

        for kw, count in keywords[:15]:  # Show top 15 per domain
            lines.append(f"    - \"{kw}\" (appears {count} times)")

        if len(keywords) > 15:
            lines.append(f"    ... and {len(keywords) - 15} more")

        lines.append("")

    # Summary stats
    total_suggestions = sum(len(kws) for kws in suggestions.values())
    total_domains = len(suggestions)

    lines.append("=" * 60)
    lines.append(f"Total: {total_suggestions} keyword suggestions across {total_domains} domains")
    lines.append("")
    lines.append("To add these to heuristics:")
    lines.append("1. Review suggestions above")
    lines.append("2. Edit src/jarvis/memory/heuristics/<discipline>_domains.py")
    lines.append("3. Add keywords to appropriate *_KEYWORD_MAP dictionaries")
    lines.append("4. Run: jarvis catalog validate-heuristics")
    lines.append("5. Re-run: jarvis catalog domain-job")

    return "\n".join(lines)


def generate_heuristic_code(
    domain: str,
    keywords: List[Tuple[str, int]],
    top_n: int = 20,
) -> str:
    """Generate Python code snippet for adding keywords to heuristics.

    Args:
        domain: Target domain
        keywords: List of (keyword, count) tuples
        top_n: Number of top keywords to include

    Returns:
        Python code snippet ready to paste
    """
    lines = [
        f"# Auto-generated keyword suggestions for: {domain}",
        f"# Based on LLM classification patterns",
        "",
    ]

    for kw, count in keywords[:top_n]:
        lines.append(f'    "{kw}": "{domain}",  # {count} occurrences')

    return "\n".join(lines)
