"""Cognitive Trace System for ARCHES (Story 4.5.6).

Captures the full query lifecycle for debugging and replay analysis.
Trace ownership is EXCLUSIVE to ARCHES controller - subsystems only append data.

Key contracts:
- ARCHES creates trace at query start, finalizes at end
- Subsystems append to in-memory trace, never persist directly
- Replay is inspect-only (no LLM calls)
- Summaries only, no raw prompts/outputs
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# ═══════════════════════════════════════════════════════════════════════════════
# ✨ COGNITIVE TRACE DATACLASSES (Story 4.5.6)
# ═══════════════════════════════════════════════════════════════════════════════
# "Not all memories are equal; some illuminate the path walked."
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class RetrievedChunkTrace:
    """Trace of a single retrieved chunk during memory search."""
    
    chunk_id: str
    doc_key: str
    version: Optional[int]
    domain: Optional[str]
    score_before_mmr: float
    score_after_mmr: float
    freshness_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class AgentTrace:
    """Trace of a single agent (persona) invocation in Council of Ricks."""
    
    name: str                     # e.g. "architect", "critic", "researcher"
    role: str                     # semantic role of the agent
    input_summary: str            # short distilled summary of inputs
    output_summary: str           # short distilled summary of outputs
    vote: Optional[float]         # voting / weighting
    latency_ms: int               # time spent in reasoning
    model_name: Optional[str]     # e.g. GPT/Claude model used

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ResearchCallTrace:
    """Trace of a research/external API call."""
    
    query: str
    provider: str                 # e.g. "web-search", "bing", "memory-fallback"
    success: bool
    duration_ms: int
    results_count: int
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class CognitiveTrace:
    """Complete cognitive trace of a query lifecycle.
    
    Ownership: ARCHES controller creates, finalizes, and persists.
    Subsystems append data but NEVER persist directly.
    
    Replay: Inspect-only (no LLM calls during trace review).
    """
    
    # --- Core Identifiers ---
    trace_id: UUID = field(default_factory=uuid4)
    session_id: Optional[str] = None
    query: str = ""
    mode: str = "qa"                            # qa | research | planning | hybrid
    arches_version: str = "4.5.6"
    trace_schema_version: int = 1               # increments on schema change

    # --- Timing ---
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    total_latency_ms: Optional[int] = None
    phase_timings: Dict[str, int] = field(default_factory=dict)
    # e.g. {"retrieval_ms": 40, "council_ms": 120}

    # --- Inputs / Conversation Context ---
    conversation_history_summary: Optional[str] = None  # short summary of prior turns
    plan_summary: Optional[str] = None                  # high-level plan / strategy

    # --- Retrieval Phase ---
    retrievers_used: List[str] = field(default_factory=list)
    retrieval_mode: str = "normal"  # Story 4-10: normal | meta | time_slice | historical
    diversity_mode: str = "balanced"
    k_initial: int = 0
    k_final: int = 0
    retrieval_events: List[RetrievedChunkTrace] = field(default_factory=list)

    # --- Council of Ricks / Agents ---
    agents: List[AgentTrace] = field(default_factory=list)

    # --- Research Loops ---
    research_calls: List[ResearchCallTrace] = field(default_factory=list)

    # --- Final Decision / Output ---
    final_answer_summary: Optional[str] = None
    sources: List[str] = field(default_factory=list)     # chunk_ids/doc_keys
    domains: List[str] = field(default_factory=list)
    confidence_estimate: Optional[float] = None

    # --- Meta ---
    model_versions: Dict[str, str] = field(default_factory=dict)
    severity: str = "normal"                    # normal | error | low_confidence | debug
    sampled: bool = True                        # indicates retained trace
    errors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # --- Raw storage (optional future use) ---
    meta: Dict[str, Any] = field(default_factory=dict)   # misc extra info

    # ═══════════════════════════════════════════════════════════════════════
    # SERIALIZATION HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for JSONB storage.
        
        Handles UUID and datetime conversion to JSON-safe formats.
        """
        data = {
            # Core IDs
            "trace_id": str(self.trace_id),
            "session_id": self.session_id,
            "query": self.query,
            "mode": self.mode,
            "arches_version": self.arches_version,
            "trace_schema_version": self.trace_schema_version,
            
            # Timing
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_latency_ms": self.total_latency_ms,
            "phase_timings": self.phase_timings,
            
            # Inputs / Context
            "conversation_history_summary": self.conversation_history_summary,
            "plan_summary": self.plan_summary,
            
            # Retrieval
            "retrievers_used": self.retrievers_used,
            "retrieval_mode": self.retrieval_mode,
            "diversity_mode": self.diversity_mode,
            "k_initial": self.k_initial,
            "k_final": self.k_final,
            "retrieval_events": [e.to_dict() for e in self.retrieval_events],
            
            # Agents
            "agents": [a.to_dict() for a in self.agents],
            
            # Research
            "research_calls": [r.to_dict() for r in self.research_calls],
            
            # Output
            "final_answer_summary": self.final_answer_summary,
            "sources": self.sources,
            "domains": self.domains,
            "confidence_estimate": self.confidence_estimate,
            
            # Meta
            "model_versions": self.model_versions,
            "severity": self.severity,
            "sampled": self.sampled,
            "errors": self.errors,
            "tags": self.tags,
            "meta": self.meta,
        }
        return data

    def to_json(self) -> str:
        """Convert trace to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveTrace":
        """Reconstruct CognitiveTrace from dictionary.
        
        Used for loading from JSONB storage.
        """
        # Parse UUID
        trace_id = UUID(data["trace_id"]) if data.get("trace_id") else uuid4()
        
        # Parse datetimes
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"].replace("Z", "+00:00"))
        
        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00"))
        
        # Parse nested objects
        retrieval_events = [
            RetrievedChunkTrace(**e) for e in data.get("retrieval_events", [])
        ]
        agents = [AgentTrace(**a) for a in data.get("agents", [])]
        research_calls = [ResearchCallTrace(**r) for r in data.get("research_calls", [])]
        
        return cls(
            trace_id=trace_id,
            session_id=data.get("session_id"),
            query=data.get("query", ""),
            mode=data.get("mode", "qa"),
            arches_version=data.get("arches_version", "4.5.6"),
            trace_schema_version=data.get("trace_schema_version", 1),
            started_at=started_at or datetime.now(timezone.utc),
            completed_at=completed_at,
            total_latency_ms=data.get("total_latency_ms"),
            phase_timings=data.get("phase_timings", {}),
            conversation_history_summary=data.get("conversation_history_summary"),
            plan_summary=data.get("plan_summary"),
            retrievers_used=data.get("retrievers_used", []),
            retrieval_mode=data.get("retrieval_mode", "normal"),
            diversity_mode=data.get("diversity_mode", "balanced"),
            k_initial=data.get("k_initial", 0),
            k_final=data.get("k_final", 0),
            retrieval_events=retrieval_events,
            agents=agents,
            research_calls=research_calls,
            final_answer_summary=data.get("final_answer_summary"),
            sources=data.get("sources", []),
            domains=data.get("domains", []),
            confidence_estimate=data.get("confidence_estimate"),
            model_versions=data.get("model_versions", {}),
            severity=data.get("severity", "normal"),
            sampled=data.get("sampled", True),
            errors=data.get("errors", []),
            tags=data.get("tags", []),
            meta=data.get("meta", {}),
        )

    # ═══════════════════════════════════════════════════════════════════════
    # FINALIZATION HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def finalize(self) -> None:
        """Finalize trace after query completion.
        
        Sets completed_at and computes total_latency_ms.
        Called by ARCHES controller before persistence.
        """
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.total_latency_ms = int(delta.total_seconds() * 1000)

    def add_error(self, error: str) -> None:
        """Add an error to the trace and update severity."""
        self.errors.append(error)
        if self.severity == "normal":
            self.severity = "error"

    def add_phase_timing(self, phase: str, duration_ms: int) -> None:
        """Record timing for a processing phase."""
        self.phase_timings[phase] = duration_ms


# ═══════════════════════════════════════════════════════════════════════════════
# PERSISTENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def log_cognitive_trace(trace: CognitiveTrace, session: "Session") -> None:
    """Persist a cognitive trace to the database.
    
    ONLY called by ARCHES controller after query completion.
    
    Args:
        trace: Finalized CognitiveTrace instance
        session: SQLAlchemy database session
    """
    from jarvis.database.models import CognitiveTraceLog
    
    logger = structlog.get_logger("jarvis.arches.trace")
    
    # Ensure trace is finalized
    if trace.completed_at is None:
        trace.finalize()
    
    # Create DB record
    db_trace = CognitiveTraceLog(
        trace_id=trace.trace_id,
        session_id=trace.session_id,
        query=trace.query,
        mode=trace.mode,
        severity=trace.severity,
        sampled=trace.sampled,
        trace_schema_version=trace.trace_schema_version,
        trace_data=trace.to_dict(),
        total_latency_ms=trace.total_latency_ms,
    )
    
    session.add(db_trace)
    session.commit()
    
    logger.info(
        "cognitive_trace_logged",
        trace_id=str(trace.trace_id),
        session_id=trace.session_id,
        mode=trace.mode,
        severity=trace.severity,
        total_latency_ms=trace.total_latency_ms,
    )


def get_cognitive_trace(trace_id: UUID, session: "Session") -> Optional[CognitiveTrace]:
    """Retrieve a cognitive trace by ID.
    
    Args:
        trace_id: UUID of the trace
        session: SQLAlchemy database session
        
    Returns:
        CognitiveTrace if found, None otherwise
    """
    from jarvis.database.models import CognitiveTraceLog
    
    db_trace = session.query(CognitiveTraceLog).filter(
        CognitiveTraceLog.trace_id == trace_id
    ).first()
    
    if db_trace is None:
        return None
    
    return CognitiveTrace.from_dict(db_trace.trace_data)


def list_cognitive_traces(
    session: "Session",
    session_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List cognitive traces with optional filters.
    
    Returns lightweight summaries, not full trace data.
    
    Args:
        session: SQLAlchemy database session
        session_id: Filter by session ID
        severity: Filter by severity level
        limit: Maximum number of results
        
    Returns:
        List of trace summaries
    """
    from jarvis.database.models import CognitiveTraceLog
    
    query = session.query(CognitiveTraceLog).order_by(
        CognitiveTraceLog.created_at.desc()
    )
    
    if session_id:
        query = query.filter(CognitiveTraceLog.session_id == session_id)
    
    if severity:
        query = query.filter(CognitiveTraceLog.severity == severity)
    
    query = query.limit(limit)
    
    results = []
    for trace in query.all():
        results.append({
            "trace_id": str(trace.trace_id),
            "session_id": trace.session_id,
            "query": trace.query[:100] + "..." if len(trace.query) > 100 else trace.query,
            "mode": trace.mode,
            "severity": trace.severity,
            "total_latency_ms": trace.total_latency_ms,
            "created_at": trace.created_at.isoformat() if trace.created_at else None,
        })
    
    return results
