"""ARCHES Runtime Controller - Thin Facade Pattern.

ARCHITECTURAL NOTE (Per user's cognitive authority requirement):
This is now a THIN FACADE that delegates to specialized controllers.
The monolithic controller created a cognitive bottleneck for autonomous self-improvement.

Specialized Controllers:
- ArchesPlanningController: Stage orchestration, research triggers
- ArchesExecutionController: Agent coordination
- ArchesMemoryController: Memory tracking
- ArchesSafetyController: Loop guards, retry policy

This separation ensures mental clarity for both humans and autonomous agents.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

import structlog

# Specialized controllers (cognitive architecture split)
from jarvis.arches.planning_controller import ArchesPlanningController
from jarvis.arches.execution_controller import ArchesExecutionController
from jarvis.arches.memory_controller import ArchesMemoryController
from jarvis.arches.safety_controller import ArchesSafetyController
from jarvis.arches.session_manager import SessionManager

# State and trace
from jarvis.arches.state import ARCHESSession, PlanStage, PlanAction
from jarvis.arches.trace_helpers import (
    append_retrieval_trace,
    append_agent_trace,
    append_research_trace,
    append_error_trace,
)
from jarvis.memory.search import RetrievalMode
from jarvis.observability.metrics import planner_stages_completed, safety_violations_total

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)

try:
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
except ImportError:
    tracer = None

# Re-export for backward compatibility
__all__ = [
    "ARCHESController",
    "ARCHESSession",
    "PlanStage",
    "PlanAction",
    "get_controller",
]


class ARCHESController:
    """THIN FACADE for ARCHES cognitive architecture.
    
    Delegates to specialized controllers for separation of concerns:
    - Planning: Stage orchestration, research decisions
    - Execution: Agent coordination
    - Memory: Memory tracking, freshness
    - Safety: Loop guards, error handling, policy
    
    This architecture prevents cognitive authority debt and enables
    safe autonomous self-modification.
    
    Usage:
        controller = ARCHESController()
        session = controller.start_session("What is Jarvis?")
        controller.start_stage(session, PlanStage.HYBRID)
        controller.record_memory_usage(session, chunks)
        controller.complete_stage(session, PlanStage.HYBRID)
    """

    def __init__(self) -> None:
        """Initialize the ARCHES facade with specialized controllers."""
        # Specialized controllers
        self.planning = ArchesPlanningController()
        self.execution = ArchesExecutionController()
        self.memory = ArchesMemoryController()
        self.safety = ArchesSafetyController()
        self.session_manager = SessionManager()
        
        self.logger = structlog.get_logger(__name__)



    # ═══════════════════════════════════════════════════════════════════════
    # SESSION LIFECYCLE (delegates to SessionManager)
    # ═══════════════════════════════════════════════════════════════════════

    def start_session(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        mode: str = "qa",
        explicit_retrieval_mode: Optional[RetrievalMode] = None,
    ) -> ARCHESSession:
        """Initialize a new ARCHES session.
        
        Delegates to: SessionManager
        """
        if tracer:
            with tracer.start_as_current_span("arches.start_session") as span:
                span.set_attribute("query", query)
                span.set_attribute("mode", mode)
                if conversation_id:
                    span.set_attribute("conversation_id", conversation_id)
                session = self.session_manager.create_session(
                    query, conversation_id, mode, explicit_retrieval_mode
                )
                span.set_attribute("session_id", session.session_id)
                return session
        
        return self.session_manager.create_session(
            query, conversation_id, mode, explicit_retrieval_mode
        )

    def get_session(self, session_id: str) -> Optional[ARCHESSession]:
        """Retrieve a session by ID.
        
        Delegates to: SessionManager
        """
        # Lightweight lookup, maybe skip tracing to reduce noise
        return self.session_manager.get_session(session_id)

    def end_session(
        self,
        session: ARCHESSession,
        db_session: Optional["Session"] = None,
    ) -> Optional[str]:
        """End and persist session.
        
        Delegates to: SessionManager
        """
        if tracer:
            with tracer.start_as_current_span("arches.end_session") as span:
                span.set_attribute("session_id", session.session_id)
                return self.session_manager.end_session(session, db_session)
                
        return self.session_manager.end_session(session, db_session)

    def get_session_summary(self, session: ARCHESSession) -> Dict[str, Any]:
        """Get summary of session state."""
        return {
            "session_id": session.session_id,
            "completed_stages": [
                k for k, v in session.plan_state.items() if v.status == "complete"
            ],
            "research_triggered": session.flags.is_research_triggered,
            "flags": {
                 "fallback_needed": session.flags.fallback_needed,
                 "rerun_detected": session.flags.rerun_detected,
                 "gap_detected": session.flags.gap_detected,
                 "has_sufficient_memory": session.flags.has_sufficient_memory,
            },
            "memory": {
                "chunks_used": len(session.memory_state.chunks_used),
                "average_freshness": session.memory_state.average_freshness,
            }
        }

    # ═══════════════════════════════════════════════════════════════════════
    # PLANNING & STAGE ORCHESTRATION (delegates to PlanningController)
    # ═══════════════════════════════════════════════════════════════════════

    def start_stage(self, session: ARCHESSession, stage: PlanStage) -> None:
        """Mark stage as started.
        
        Delegates to: ArchesPlanningController
        """
        if tracer:
            with tracer.start_as_current_span(f"arches.stage.start.{stage}") as span:
                span.set_attribute("session_id", session.session_id)
                span.set_attribute("stage", str(stage))
                self.planning.start_stage(session, stage)
                return

        self.planning.start_stage(session, stage)

    def complete_stage(self, session: ARCHESSession, stage: PlanStage) -> None:
        """Mark stage as complete.
        
        Delegates to: ArchesPlanningController
        """
        try:
            planner_stages_completed.add(1, {"stage": str(stage), "mode": session.mode})
        except Exception:
            pass  # Don't fail workflow on metrics error

        if tracer:
            with tracer.start_as_current_span(f"arches.stage.complete.{stage}") as span:
                span.set_attribute("session_id", session.session_id)
                span.set_attribute("stage", str(stage))
                self.planning.complete_stage(session, stage)
                return

        self.planning.complete_stage(session, stage)

    def skip_stage(self, session: ARCHESSession, stage: PlanStage) -> None:
        """Mark stage as skipped.
        
        Delegates to: ArchesPlanningController
        """
        if tracer:
            with tracer.start_as_current_span(f"arches.stage.skip.{stage}") as span:
                 span.set_attribute("session_id", session.session_id)
                 span.set_attribute("stage", str(stage))
                 self.planning.skip_stage(session, stage)
                 return
                 
        self.planning.skip_stage(session, stage)

    def should_trigger_research(
        self,
        session: ARCHESSession,
        gap_analysis: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Decide if research is needed.
        
        Delegates to: ArchesPlanningController
        """
        if tracer:
             with tracer.start_as_current_span("arches.trigger_research") as span:
                span.set_attribute("session_id", session.session_id)
                result = self.planning.should_trigger_research(session, gap_analysis)
                span.set_attribute("decision", result)
                return result

        return self.planning.should_trigger_research(session, gap_analysis)

    def react_to_voting_outcome(
        self,
        session: ARCHESSession,
        voting_result: Any,
    ) -> PlanAction:
        """Decide next action based on voting outcome.
        
        Delegates to: ArchesPlanningController
        """
        if tracer:
             with tracer.start_as_current_span("arches.react_to_vote") as span:
                span.set_attribute("session_id", session.session_id)
                result = self.planning.react_to_voting_outcome(session, voting_result)
                span.set_attribute("action", str(result))
                return result
                
        return self.planning.react_to_voting_outcome(session, voting_result)

    # ═══════════════════════════════════════════════════════════════════════
    # MEMORY TRACKING (delegates to MemoryController)
    # ═══════════════════════════════════════════════════════════════════════

    def record_memory_usage(
        self,
        session: ARCHESSession,
        chunks: List[Any],
        domains: Optional[List[str]] = None,
    ) -> None:
        """Track memory usage.
        
        Delegates to: ArchesMemoryController
        """
        self.memory.record_memory_usage(session, chunks, domains)

    def _compute_freshness(self, chunks: List[Any]) -> Dict[str, float]:
        """Compute memory freshness.
        
        Delegates to: ArchesMemoryController
        """
        return self.memory.compute_freshness(chunks)

    # ═══════════════════════════════════════════════════════════════════════
    # EXECUTION & AGENT COORDINATION (delegates to ExecutionController)
    # ═══════════════════════════════════════════════════════════════════════

    def record_agent_result(self, session: ARCHESSession, result: Any) -> None:
        """Record agent result.
        
        Delegates to: ArchesExecutionController
        """
        self.execution.record_agent_result(session, result)

    # ═══════════════════════════════════════════════════════════════════════
    # SAFETY & POLICY ENFORCEMENT (delegates to SafetyController)
    # ═══════════════════════════════════════════════════════════════════════

    def set_flag(self, session: ARCHESSession, flag_name: str, value: bool) -> None:
        """Set session safety flag.
        
        Delegates to: ArchesSafetyController
        """
        self.safety.set_flag(session, flag_name, value)

    def check_loop_guard(self, session: ARCHESSession, action_type: str) -> bool:
        """Check if action allowed (loop guard).
        
        Delegates to: ArchesSafetyController
        """
        allowed = self.safety.check_loop_guard(session, action_type)
        if not allowed:
            try:
                safety_violations_total.add(1, {"type": "loop_guard", "action": action_type})
            except Exception:
                pass
        return allowed

    def mark_action_taken(self, session: ARCHESSession, action_type: str) -> None:
        """Mark action taken (set loop guard).
        
        Delegates to: ArchesSafetyController
        """
        self.safety.mark_action_taken(session, action_type)

    # ═══════════════════════════════════════════════════════════════════════
    # TRACE APPEND METHODS (thin wrappers around trace_helpers)
    # ═══════════════════════════════════════════════════════════════════════

    def trace_retrieval(
        self,
        session: ARCHESSession,
        chunks: List[Any],
        phase_ms: int,
        retrievers_used: Optional[List[str]] = None,
        diversity_mode: str = "balanced",
        k_initial: int = 0,
        k_final: int = 0,
    ) -> None:
        """Append retrieval data to cognitive trace."""
        append_retrieval_trace(
            session, chunks, phase_ms, retrievers_used, diversity_mode, k_initial, k_final
        )

    def trace_agent(
        self,
        session: ARCHESSession,
        name: str,
        role: str,
        input_summary: str,
        output_summary: str,
        latency_ms: int,
        vote: Optional[float] = None,
        model_name: Optional[str] = None,
    ) -> None:
        """Append agent invocation to cognitive trace."""
        append_agent_trace(
            session, name, role, input_summary, output_summary, latency_ms, vote, model_name
        )

    def trace_research(
        self,
        session: ARCHESSession,
        query: str,
        provider: str,
        success: bool,
        duration_ms: int,
        results_count: int,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append research call to cognitive trace."""
        append_research_trace(
            session, query, provider, success, duration_ms, results_count, meta
        )

    def trace_error(
        self,
        session: ARCHESSession,
        error: str,
        severity: str = "error",
    ) -> None:
        """Append error to cognitive trace."""
        append_error_trace(session, error, severity)


# Singleton accessor for backward compatibility
_global_controller: Optional[ARCHESController] = None


def get_controller() -> ARCHESController:
    """Get or create the global ARCHES controller instance."""
    global _global_controller
    if _global_controller is None:
        _global_controller = ARCHESController()
    return _global_controller
