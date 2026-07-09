"""ARCHES Execution Controller - Agent invocation and results aggregation.

Part of cognitive architecture split for autonomous self-improvement safety.
Handles agent coordination and result management.
"""
from typing import Any

import structlog

from jarvis.arches.state import ARCHESSession

logger = structlog.get_logger(__name__)


class ArchesExecutionController:
    """Manages agent execution and result aggregation.
    
    Responsibilities:
    - Agent invocation coordination
    - Result recording
    - Execution state tracking
    """

    def __init__(self):
        """Initialize execution controller."""
        self.logger = logger

    def record_agent_result(self, session: ARCHESSession, result: Any) -> None:
        """Record an agent's response in the session.
        
        Args:
            session: The current session
            result: AgentResponse or similar result object
        """
        session.agent_results.append(result)
        session.touch()

        self.logger.debug(
            "agent_result_recorded",
            session_id=session.session_id,
            total_results=len(session.agent_results),
        )
