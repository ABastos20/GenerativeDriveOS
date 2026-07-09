"""Weighted chaos voting consensus engine for Council of Ricks (Story 4.3).

Enhanced with memory attribution for Story 4.5.2:
- Include per-agent memory attribution in voting transcript
- Track which chunks each agent cited
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import structlog

from jarvis.agents.response import PersonaResponse

logger = structlog.get_logger(__name__)


@dataclass
class VotingResult:
    """Result of weighted chaos voting.

    Attributes:
        winner: Name of the winning persona
        scores: Dict mapping persona names to their weighted scores
        ties: List of persona names if there's a tie (within threshold)
        total_personas: Total number of personas that voted
        disagreement_score: Score 0.0-1.0 indicating vote divergence (Story 4.5.5)
        failed_agents: List of personas that failed (Story 4.5.5)
    """

    winner: str
    scores: Dict[str, float]
    ties: List[str]
    total_personas: int
    # Memory Attribution (Story 4.5.2)
    attribution: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Planner Feedback Loop (Story 4.5.5)
    disagreement_score: float = 0.0
    failed_agents: List[str] = field(default_factory=list)

    @property
    def has_tie(self) -> bool:
        """Check if there's a tie."""
        return len(self.ties) > 1


def weighted_chaos_vote(
    responses: List[PersonaResponse],
    tie_threshold: float = 0.05
) -> VotingResult:
    """Perform weighted chaos voting to select winning persona response.

    Algorithm:
    1. Each persona gets a score equal to its weight (if successful)
    2. Failed personas get score 0
    3. Select persona with highest score as winner
    4. If multiple personas within tie_threshold, mark as tie

    Args:
        responses: List of PersonaResponse objects from parallel invocation
        tie_threshold: Score difference threshold for considering a tie (default: 0.05 = 5%)

    Returns:
        VotingResult with winner, scores, and tie information
    """
    logger.info(
        "starting_weighted_voting",
        response_count=len(responses),
        tie_threshold=tie_threshold
    )

    # Calculate weighted scores
    scores: Dict[str, float] = {}
    success_count = 0

    for response in responses:
        persona_name = response.persona.name

        if response.is_success:
            # Successful response gets full persona weight
            scores[persona_name] = response.persona.weight
            success_count += 1
        else:
            # Failed persona gets 0 score
            scores[persona_name] = 0.0
            logger.warning(
                "persona_failed_voting",
                persona_name=persona_name,
                error=str(response.error)
            )

    if not scores:
        raise ValueError("No persona scores available for voting")

    # Find winner (highest score)
    winner = max(scores, key=scores.get)
    winning_score = scores[winner]

    # Find ties (personas within threshold of winner)
    ties = [
        name for name, score in scores.items()
        if abs(score - winning_score) < tie_threshold and score > 0
    ]

    # Collect per-agent memory attribution (Story 4.5.2)
    attribution: Dict[str, Dict[str, Any]] = {}
    failed_agents: List[str] = []  # Story 4.5.5
    
    for response in responses:
        persona_name = response.persona.name
        
        # Track failed agents (Story 4.5.5)
        if not response.is_success:
            failed_agents.append(persona_name)
        
        if response.memory_attribution:
            attribution[persona_name] = response.memory_attribution.to_dict()
        else:
            attribution[persona_name] = {
                "chunks_used": [],
                "domains_accessed": [],
                "sources": [],
                "memory_freshness": 0.0,
                "total_chunks_available": 0,
                "citation_rate": 0.0,
            }

    # Compute disagreement score (Story 4.5.5)
    # 0.0 = unanimous, 1.0 = max divergence
    # Based on score variance among successful personas
    successful_scores = [s for s in scores.values() if s > 0]
    if len(successful_scores) >= 2:
        avg_score = sum(successful_scores) / len(successful_scores)
        variance = sum((s - avg_score) ** 2 for s in successful_scores) / len(successful_scores)
        max_variance = 0.25  # Max possible variance (scores between 0-1)
        disagreement_score = min(1.0, variance / max_variance) if max_variance > 0 else 0.0
    else:
        disagreement_score = 0.0  # Single or no successful persona = no disagreement

    logger.info(
        "voting_complete",
        winner=winner,
        winning_score=winning_score,
        tie_count=len(ties) if len(ties) > 1 else 0,
        success_count=success_count,
        total_personas=len(responses),
        disagreement_score=round(disagreement_score, 3),
        failed_agents=failed_agents,
    )

    return VotingResult(
        winner=winner,
        scores=scores,
        ties=ties if len(ties) > 1 else [],
        total_personas=len(responses),
        attribution=attribution,
        disagreement_score=disagreement_score,
        failed_agents=failed_agents,
    )


def get_winner_response(
    responses: List[PersonaResponse],
    voting_result: VotingResult
) -> PersonaResponse:
    """Get the winning PersonaResponse object based on voting result.

    Args:
        responses: Original list of persona responses
        voting_result: Result from weighted_chaos_vote()

    Returns:
        The PersonaResponse object for the winning persona

    Raises:
        ValueError: If winner persona not found in responses
    """
    for response in responses:
        if response.persona.name == voting_result.winner:
            return response

    raise ValueError(f"Winner persona '{voting_result.winner}' not found in responses")
