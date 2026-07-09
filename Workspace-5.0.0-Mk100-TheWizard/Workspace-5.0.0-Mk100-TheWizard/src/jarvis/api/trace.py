"""API endpoints for cognitive trace retrieval (Story 4.5.6).

Endpoints:
- GET /api/traces/{trace_id} - Get full trace
- GET /api/traces - List traces with filters
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from jarvis.database import postgres as pg
from jarvis.arches.trace import (
    get_cognitive_trace,
    list_cognitive_traces,
)

router = APIRouter(prefix="/traces", tags=["traces"])


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════


class TraceSummary(BaseModel):
    """Lightweight trace summary for list endpoint."""
    
    trace_id: str
    session_id: Optional[str] = None
    query: str
    mode: str
    severity: str
    total_latency_ms: Optional[int] = None
    created_at: Optional[str] = None


class TraceListResponse(BaseModel):
    """Response for trace list endpoint."""
    
    traces: List[TraceSummary]
    count: int


class PlannerAction(BaseModel):
    """Planner action from ARCHES (Story 4.5.5 + 4.5.7)."""

    action: str = Field(..., description="Action type: INCREASE_DIVERSITY, TRIGGER_RESEARCH_EXPANSION, etc.")
    reason: str = Field(..., description="Why the planner took this action")
    timestamp: Optional[str] = None


class TraceDetailResponse(BaseModel):
    """Full trace response (matches CognitiveTrace.to_dict()).

    Enhanced for Story 4.5.7 with explicit planner_actions field.
    """

    trace_id: str
    session_id: Optional[str] = None
    query: str
    mode: str
    arches_version: str
    trace_schema_version: int

    # Timing
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_latency_ms: Optional[int] = None
    phase_timings: Dict[str, int] = Field(default_factory=dict)

    # Context
    conversation_history_summary: Optional[str] = None
    plan_summary: Optional[str] = None

    # Retrieval
    retrievers_used: List[str] = Field(default_factory=list)
    diversity_mode: str = "balanced"
    k_initial: int = 0
    k_final: int = 0
    retrieval_events: List[Dict[str, Any]] = Field(default_factory=list)

    # Agents & Research
    agents: List[Dict[str, Any]] = Field(default_factory=list)
    research_calls: List[Dict[str, Any]] = Field(default_factory=list)

    # Planner Actions (Story 4.5.7 AC5)
    planner_actions: List[PlannerAction] = Field(
        default_factory=list,
        description="ARCHES planner decisions extracted from trace.meta"
    )

    # Output
    final_answer_summary: Optional[str] = None
    sources: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    confidence_estimate: Optional[float] = None

    # Meta
    model_versions: Dict[str, str] = Field(default_factory=dict)
    severity: str = "normal"
    sampled: bool = True
    errors: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)

    # Future: redacted flag for PII handling
    # redacted: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


def get_db() -> Session:
    """Dependency to get DB session."""
    with pg.get_session() as session:
        yield session


@router.get("/{trace_id}", response_model=TraceDetailResponse)
def get_trace(
    trace_id: str,
    db: Session = Depends(get_db),
) -> TraceDetailResponse:
    """Get a cognitive trace by ID.

    Returns full trace data for debugging and analysis.
    Enhanced for Story 4.5.7 to extract planner_actions from trace.meta.
    """
    try:
        uuid_id = UUID(trace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid trace ID: {trace_id}")

    trace = get_cognitive_trace(uuid_id, db)

    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace not found: {trace_id}")

    # Convert trace to dict
    trace_dict = trace.to_dict()

    # Extract planner actions from meta if present (Story 4.5.5 + 4.5.7)
    planner_actions = []
    if trace.meta and "planner_actions" in trace.meta:
        for action_dict in trace.meta["planner_actions"]:
            planner_actions.append(
                PlannerAction(
                    action=action_dict.get("action", "UNKNOWN"),
                    reason=action_dict.get("reason", "No reason provided"),
                    timestamp=action_dict.get("timestamp")
                )
            )

    # Add planner_actions to response
    trace_dict["planner_actions"] = planner_actions

    return TraceDetailResponse(**trace_dict)


@router.get("", response_model=TraceListResponse)
def list_traces(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db),
) -> TraceListResponse:
    """List cognitive traces with optional filters.
    
    Returns lightweight summaries for efficiency.
    """
    traces = list_cognitive_traces(
        db,
        session_id=session_id,
        severity=severity,
        limit=limit,
    )
    
    summaries = [TraceSummary(**t) for t in traces]
    
    return TraceListResponse(traces=summaries, count=len(summaries))
