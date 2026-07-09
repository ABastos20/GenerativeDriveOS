"""Research decision logic for ARCHES planning.

Extracted from ArchesPlanningController for complexity compliance.
"""
from typing import Any, Dict, Optional

import structlog

from jarvis.arches.state import ARCHESSession

logger = structlog.get_logger(__name__)


class ResearchDecisionEngine:
    """Encapsulates research trigger decision logic."""

    def should_trigger_research(
        self,
        session: ARCHESSession,
        gap_analysis: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Decide if research is needed based on session state and gap analysis.
        
        Args:
            session: The current session
            gap_analysis: Optional gap analysis results
            
        Returns:
            True if research should be triggered
        """
        # Already triggered - don't repeat
        if session.flags.is_research_triggered:
            logger.info(
                "research_already_triggered",
                session_id=session.session_id,
            )
            return False

        # Sufficient memory available
        if session.flags.has_sufficient_memory:
            logger.info(
                "sufficient_memory_available",
                session_id=session.session_id,
            )
            return False

        # Check gap analysis
        return self._evaluate_gaps(session, gap_analysis)

    def _evaluate_gaps(
        self,
        session: ARCHESSession,
        gap_analysis: Optional[Dict[str, Any]],
    ) -> bool:
        """Evaluate gap analysis to determine if research needed."""
        if not gap_analysis:
            return False

        coverage_gap = gap_analysis.get("coverage_gap", False)
        coverage_score = gap_analysis.get("coverage_score", 1.0)
        recency_gap = gap_analysis.get("recency_gap", False)

        # Trigger on significant coverage gaps
        if coverage_gap and coverage_score < 0.6:
            logger.info(
                "research_triggered_coverage_gap",
                session_id=session.session_id,
                coverage_score=coverage_score,
            )
            return True

        # Trigger on recency gaps
        if recency_gap:
            logger.info(
                "research_triggered_recency_gap",
                session_id=session.session_id,
            )
            return True

        return False
