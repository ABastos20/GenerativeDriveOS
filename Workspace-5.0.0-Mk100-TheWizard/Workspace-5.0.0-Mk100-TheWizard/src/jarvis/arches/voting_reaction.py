"""Voting reaction logic for ARCHES planning.

Extracted from ArchesPlanningController for complexity compliance.
"""
from typing import Any

import structlog

from jarvis.arches.state import ARCHESSession, PlanAction

logger = structlog.get_logger(__name__)


class VotingReactionEngine:
    """Encapsulates voting outcome reaction logic."""

    def react_to_voting_outcome(
        self,
        session: ARCHESSession,
        voting_result: Any,
    ) -> PlanAction:
        """Decide next action based on voting outcome.
        
        Priorities:
        1. Failed agents -> Retry (if not done)
        2. High disagreement/Tie -> Research (if not done)
        3. High overlap -> Diversity (if not done)
        4. NOOP
        """
        # 1. Check for failed agents
        action = self._check_failed_agents(session, voting_result)
        if action != PlanAction.NOOP:
            return action
            
        # 2. Check for disagreement
        action = self._check_disagreement(session, voting_result)
        if action != PlanAction.NOOP:
            return action
            
        # 3. Check for overlap/diversity needs
        action = self._check_overlap_diversity(session)
        if action != PlanAction.NOOP:
            return action
            
        return PlanAction.NOOP

    def _check_failed_agents(self, session: ARCHESSession, voting_result: Any) -> PlanAction:
        """Check for failed agents and trigger retry if needed."""
        failed_agents = getattr(voting_result, "failed_agents", [])
        if not failed_agents:
            return PlanAction.NOOP
            
        if session.planner_state.fallback_used:
            return PlanAction.NOOP
            
        session.flags.fallback_needed = True
        session.planner_state.fallback_used = True
        logger.info("fallback_retry_triggered", failed_agents=failed_agents)
        return PlanAction.RETRY_WITH_FALLBACK

    def _check_disagreement(self, session: ARCHESSession, voting_result: Any) -> PlanAction:
        """Check for high disagreement/ties and trigger research expansion if needed."""
        disagreement = getattr(voting_result, "disagreement_score", 0.0)
        ties = getattr(voting_result, "ties", [])
        high_disagreement = disagreement > 0.7
        has_tie = len(ties) > 1
        
        if not (high_disagreement or has_tie):
            return PlanAction.NOOP
            
        if session.planner_state.research_expanded:
            return PlanAction.NOOP
            
        session.flags.gap_detected = True
        session.planner_state.research_expanded = True
        logger.info("research_expansion_triggered", disagreement=disagreement, ties=ties)
        return PlanAction.TRIGGER_RESEARCH_EXPANSION

    def _check_overlap_diversity(self, session: ARCHESSession) -> PlanAction:
        """Check memory overlap and increase diversity if needed."""
        overlap = self._detect_chunk_overlap(session)
        if overlap <= 0.8:
            return PlanAction.NOOP
            
        if session.planner_state.diversity_adjusted:
            return PlanAction.NOOP
        
        session.planner_state.diversity_adjusted = True
        logger.info("diversity_increase_triggered", overlap=overlap)
        return PlanAction.INCREASE_DIVERSITY

    def _detect_chunk_overlap(self, session: ARCHESSession) -> float:
        """Calculate overlap ratio of retrieved chunks (0.0=unique, 1.0=identical docs)."""
        chunks = session.memory_state.chunks_used
        if not chunks:
            return 0.0
            
        unique_docs = set()
        for c in chunks:
            # Try to extract doc ID from common formats (e.g. "doc::file.md::chunk_0")
            parts = str(c).split("::")
            if len(parts) >= 2:
                unique_docs.add(parts[1])
            else:
                unique_docs.add(c)
                
        ratio = len(unique_docs) / len(chunks)
        return 1.0 - ratio
