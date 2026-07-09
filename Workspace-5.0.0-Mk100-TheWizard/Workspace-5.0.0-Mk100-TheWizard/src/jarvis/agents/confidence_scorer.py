"""Confidence scoring for responses."""
from typing import List, Any

def score_response_confidence(
    response_text: str,
    results: List[Any],
    grounding_level: str
) -> str:
    """Score response confidence based on retrieved results.
    
    Args:
        response_text: The LLM response text
        results: List of search results used for context
        grounding_level: Strictness level (soft, balanced, strict)
        
    Returns:
        Response text with confidence annotations (if any)
    """
    # Placeholder implementation - pass through for now
    # Real implementation would calculate overlap/hallucination risk
    return response_text

def format_confidence_legend() -> str:
    """Format confidence legend for display.
    
    Returns:
        String explaining confidence markers
    """
    return "\nConfidence Scores: 🟢 High  🟡 Medium  🔴 Low"
