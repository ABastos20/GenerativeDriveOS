"""In-line confidence scoring for LLM responses.

This module analyzes LLM-generated responses and tags claims with their
evidence pedigree:
- [Grounded: source.md] - Directly from high-trust source
- [Inferred: conversation.txt] - Inferred from conversational context
- [Creative Leap] - Speculative bridge built by Jarvis
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

import structlog

from jarvis.memory.search import SearchResult

logger = structlog.get_logger(__name__)


@dataclass
class ConfidenceTag:
    """Confidence tag for a claim in the response."""

    claim_text: str
    tag_type: str  # "grounded", "inferred", "creative"
    source_ref: Optional[str]
    citation_id: Optional[int]
    confidence: float


def _extract_citations(response: str) -> List[int]:
    """Extract citation IDs from response text (e.g., [1], [2], [3])."""
    pattern = r"\[(\d+)\]"
    matches = re.findall(pattern, response)
    return [int(m) for m in matches]


def _classify_source_trust(result: SearchResult) -> str:
    """Classify source trust level based on domain and source type.

    Returns:
        "high" for core docs/PDFs, "medium" for conversations, "low" for unknown
    """
    domain = result.domain or ""
    source_file = result.source_file or ""

    # High trust: core docs, PDFs, architecture docs
    if domain == "jarvis.core":
        return "high"
    if source_file.endswith(".pdf"):
        return "high"
    if "architecture" in source_file.lower() or "docs/" in source_file:
        return "high"

    # Medium trust: conversations, exports
    if domain == "jarvis.conversations" or "conversations" in source_file:
        return "medium"

    # Low trust: everything else
    return "low"


def score_response_confidence(
    response: str,
    sources: List[SearchResult],
    grounding_level: str,
) -> str:
    """Add in-line confidence tags to response.

    Args:
        response: LLM-generated response text
        sources: Retrieved sources used for grounding
        grounding_level: Current grounding level (soft/balanced/strict)

    Returns:
        Response text with in-line confidence tags added

    Example:
        Input: "The auth API uses JWT tokens [1] and connects to Redis [2]."
        Output: "The auth API uses JWT tokens [Grounded: auth.md] [1] and
                connects to Redis [Grounded: redis-config.yaml] [2]."
    """
    if not sources:
        # No sources = all claims are creative leaps
        return response

    # Extract citation IDs from response
    cited_ids = _extract_citations(response)

    # Build citation ID -> source mapping
    citation_map = {idx + 1: source for idx, source in enumerate(sources)}

    # For each citation in the response, add confidence tag
    tagged_response = response

    for citation_id in cited_ids:
        source = citation_map.get(citation_id)
        if not source:
            continue

        trust_level = _classify_source_trust(source)

        # Build confidence tag
        if trust_level == "high":
            tag_type = "Grounded"
            source_name = source.source_file or source.domain or "unknown"
        elif trust_level == "medium":
            tag_type = "Inferred"
            source_name = source.source_file or source.domain or "conversation"
        else:
            tag_type = "Low-Confidence"
            source_name = source.domain or "unknown"

        # Insert tag before the citation
        citation_pattern = rf"\[{citation_id}\]"
        tag_text = f"[{tag_type}: {source_name}] "

        # Only add tag if not already present (avoid double-tagging)
        if f"[{tag_type}:" not in tagged_response:
            tagged_response = re.sub(
                citation_pattern,
                f"{tag_text}[{citation_id}]",
                tagged_response,
                count=1,
            )

    # Detect unsupported claims (text without any citations)
    # This is a simplified heuristic - in production, would use NLP sentence parsing
    sentences = re.split(r"[.!?]\s+", tagged_response)
    creative_leaps = []

    for sentence in sentences:
        # Skip empty sentences
        if not sentence.strip():
            continue

        # Check if sentence has any citations
        has_citation = bool(re.search(r"\[\d+\]", sentence))

        # In strict/balanced mode, flag uncited sentences as creative leaps
        if not has_citation and grounding_level in {"strict", "balanced"}:
            # Don't flag very short sentences or greetings
            if len(sentence.split()) > 5 and not any(
                greeting in sentence.lower()
                for greeting in ["hello", "hi", "thanks", "regards"]
            ):
                creative_leaps.append(sentence.strip())

    # Log detected creative leaps
    if creative_leaps:
        logger.info(
            "creative_leaps_detected",
            count=len(creative_leaps),
            grounding_level=grounding_level,
            leaps=creative_leaps[:3],  # Log first 3 for debugging
        )

    return tagged_response


def format_confidence_legend() -> str:
    """Generate legend explaining confidence tags.

    Returns:
        Formatted legend text for display to user
    """
    return """
📊 Confidence Legend:
- [Grounded: source.md] = Directly from high-trust source (core docs, PDFs)
- [Inferred: conversation.txt] = Inferred from conversational context
- [Creative Leap] = Speculative bridge built by Jarvis (challenge with "prove it")
""".strip()
