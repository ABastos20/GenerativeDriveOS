"""ARCHES Planning Controller - Stage orchestration and research triggers.

Part of cognitive architecture split for autonomous self-improvement safety.
Handles stage lifecycle orchestration only - complex logic delegated to engines.
"""
from typing import Any, Dict, Optional

import structlog

from jarvis.arches.state import ARCHESSession, PlanStage, PlanAction
from jarvis.arches.research_decision import ResearchDecisionEngine
from jarvis.arches.voting_reaction import VotingReactionEngine

logger = structlog.get_logger(__name__)


class ArchesPlanningController:
    """Manages ARCHES stage orchestration and planning decisions.
    
    Responsibilities:
    - Stage lifecycle (start/complete/skip)
    - Research trigger decisions
    - Gap analysis interpretation
    - Planning state coordination
    """

    def __init__(self):
        """Initialize planning controller with delegated engines."""
        self.logger = logger
        self.research_engine = ResearchDecisionEngine()
        self.voting_engine = VotingReactionEngine()

    def start_stage(self, session: ARCHESSession, stage: PlanStage) -> None:
        """Mark an ARCHES stage as started."""
        if stage.value in session.plan_state:
            session.plan_state[stage.value].start()
            session.touch()

            self.logger.debug(
                "arches_stage_started",
                session_id=session.session_id,
                stage=stage.value,
            )

    def complete_stage(self, session: ARCHESSession, stage: PlanStage) -> None:
        """Mark an ARCHES stage as complete."""
        if stage.value in session.plan_state:
            session.plan_state[stage.value].complete()
            session.touch()

            self.logger.debug(
                "arches_stage_completed",
                session_id=session.session_id,
                stage=stage.value,
            )

    def skip_stage(self, session: ARCHESSession, stage: PlanStage) -> None:
        """Mark an ARCHES stage as skipped."""
        if stage.value in session.plan_state:
            session.plan_state[stage.value].skip()
            session.touch()

            self.logger.debug(
                "arches_stage_skipped",
                session_id=session.session_id,
                stage=stage.value,
            )

    def should_trigger_research(
        self,
        session: ARCHESSession,
        gap_analysis: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Delegate research decision to specialized engine."""
        return self.research_engine.should_trigger_research(session, gap_analysis)

    def react_to_voting_outcome(
        self,
        session: ARCHESSession,
        voting_result: Any,
    ) -> PlanAction:
        """Delegate voting reaction to specialized engine."""
        return self.voting_engine.react_to_voting_outcome(session, voting_result)


