"""ARCHES Safety Controller - Retry logic, error handling, and policy enforcement.

Part of cognitive architecture split for autonomous self-improvement safety.
Handles safety-critical operations including loop guards, error handling, and retry policies.
"""
import structlog

from jarvis.arches.state import ARCHESSession

logger = structlog.get_logger(__name__)


class ArchesSafetyController:
    """Manages safety policies, error handling, and retry logic.
    
    Responsibilities:
    - Session flag management (safety gates)
    - Loop guard enforcement (prevents infinite research/retry)
    - Error handling and recovery
    - Policy constraint enforcement
    """

    def __init__(self):
        """Initialize safety controller."""
        self.logger = logger

    def set_flag(self, session: ARCHESSession, flag_name: str, value: bool) -> None:
        """Set a session control flag (safety gate).
        
        Args:
            session: The current session
            flag_name: Name of the flag to set
            value: Boolean value to set
        """
        if hasattr(session.flags, flag_name):
            setattr(session.flags, flag_name, value)
            session.touch()

            self.logger.debug(
                "session_flag_set",
                session_id=session.session_id,
                flag=flag_name,
                value=value,
            )

    def check_loop_guard(
        self,
        session: ARCHESSession,
        action_type: str,
    ) -> bool:
        """Check if action is allowed based on loop guards.
        
        Prevents infinite loops in research/retry/diversity adjustments.
        
        Args:
            session: The current session
            action_type: Type of action ("research", "diversity", "fallback")
            
        Returns:
            True if action is allowed, False if already triggered
        """
        planner = session.planner_state

        if action_type == "research" and planner.research_expanded:
            self.logger.warning(
                "loop_guard_research_blocked",
                session_id=session.session_id,
            )
            return False

        if action_type == "diversity" and planner.diversity_adjusted:
            self.logger.warning(
                "loop_guard_diversity_blocked",
                session_id=session.session_id,
            )
            return False

        if action_type == "fallback" and planner.fallback_used:
            self.logger.warning(
                "loop_guard_fallback_blocked",
                session_id=session.session_id,
            )
            return False

        return True

    def mark_action_taken(
        self,
        session: ARCHESSession,
        action_type: str,
    ) -> None:
        """Mark that an action has been taken (sets loop guard).
        
        Args:
            session: The current session
            action_type: Type of action ("research", "diversity", "fallback")
        """
        planner = session.planner_state

        if action_type == "research":
            planner.research_expanded = True
        elif action_type == "diversity":
            planner.diversity_adjusted = True
        elif action_type == "fallback":
            planner.fallback_used = True

        session.touch()

        self.logger.debug(
            "loop_guard_set",
            session_id=session.session_id,
            action_type=action_type,
        )
