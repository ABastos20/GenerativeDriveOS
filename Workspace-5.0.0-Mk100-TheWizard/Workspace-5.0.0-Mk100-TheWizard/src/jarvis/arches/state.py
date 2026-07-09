"""ARCHES state dataclasses.

Extracted from controller.py for modularity and deterministic hot-reload safety.
Per architect notes: Explicit state extraction makes ARCHES modifications safer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from jarvis.arches.trace import CognitiveTrace
from jarvis.memory.search import RetrievalMode


class PlanStage(str, Enum):
    """ARCHES processing stages."""
    ASSESS = "assess"
    RESEARCH = "research"
    CRITICAL = "critical"
    HYBRID = "hybrid"
    EXECUTE = "execute"
    STORE = "store"
    
    # Meta-stages
    PENDING = "pending"
    COMPLETE = "complete"


class PlanAction(str, Enum):
    """Planner feedback loop actions."""
    NOOP = "noop"
    COMPLETE = "complete"
    TRIGGER_RESEARCH_EXPANSION = "trigger_research_expansion"
    RETRY_WITH_FALLBACK = "retry_with_fallback"
    INCREASE_DIVERSITY = "increase_diversity"


@dataclass
class PlannerState:
    """Per-query planner loop guards."""
    diversity_adjusted: bool = False
    research_expanded: bool = False
    fallback_used: bool = False


@dataclass
class StageStatus:
    """Status of a single ARCHES stage."""
    stage: PlanStage
    status: str  # "pending", "running", "complete", "skipped"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def start(self) -> None:
        """Mark stage as started."""
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)
    
    def complete(self) -> None:
        """Mark stage as complete."""
        self.status = "complete"
        self.completed_at = datetime.now(timezone.utc)
    
    def skip(self) -> None:
        """Mark stage as skipped."""
        self.status = "skipped"
        self.completed_at = datetime.now(timezone.utc)


@dataclass
class MemoryState:
    """Tracks memory/retrieval state for a session."""
    chunks_used: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    freshness_scores: Dict[str, float] = field(default_factory=dict)
    retrieved_at: Optional[str] = None
    total_chunks_retrieved: int = 0
    average_freshness: float = 0.0


@dataclass
class SessionFlags:
    """State flags for session control flow."""
    is_research_triggered: bool = False
    fallback_needed: bool = False
    rerun_detected: bool = False
    gap_detected: bool = False
    has_sufficient_memory: bool = False


@dataclass
class ARCHESSession:
    """Single query session state.
    
    Complete state container for ARCHES query processing.
    Extracted for deterministic hot-reload safety per architect notes.
    """
    session_id: str
    query: str
    conversation_id: Optional[str] = None
    plan_state: Dict[str, StageStatus] = field(default_factory=dict)
    memory_state: MemoryState = field(default_factory=MemoryState)
    agent_results: List[Any] = field(default_factory=list)
    flags: SessionFlags = field(default_factory=SessionFlags)
    planner_state: PlannerState = field(default_factory=PlannerState)
    cognitive_trace: Optional[CognitiveTrace] = None
    retrieval_mode: Optional[RetrievalMode] = None
    time_slice_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self) -> None:
        """Initialize plan state with all ARCHES stages."""
        if not self.plan_state:
            self.plan_state = {
                stage.value: StageStatus(stage=stage, status="pending")
                for stage in PlanStage
                if stage not in (PlanStage.PENDING, PlanStage.COMPLETE)
            }
    
    def touch(self) -> None:
        """Update the session's updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)
