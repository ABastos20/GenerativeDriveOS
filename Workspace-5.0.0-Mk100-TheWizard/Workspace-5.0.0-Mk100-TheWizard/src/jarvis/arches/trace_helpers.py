"""Trace helper functions for ARCHES.

Extracted from controller.py for modularity.
"""
from typing import Any, Dict, List, Optional

import structlog

from jarvis.arches.state import ARCHESSession
from jarvis.arches.trace import (
    AgentTrace,
    RetrievedChunkTrace,
    ResearchCallTrace,
    CognitiveTrace,
)

logger = structlog.get_logger(__name__)


def append_retrieval_trace(
    session: ARCHESSession,
    chunks: List[Any],
    phase_ms: int,
    retrievers_used: List[str] | None = None,
    diversity_mode: str = "balanced",
    k_initial: int = 0,
    k_final: int = 0,
) -> None:
    """Append retrieval data to cognitive trace."""
    if not session.cognitive_trace:
        return

    trace = session.cognitive_trace
    trace.add_phase_timing("retrieval_ms", phase_ms)
    trace.retrievers_used = retrievers_used or []
    trace.diversity_mode = diversity_mode
    trace.k_initial = k_initial
    trace.k_final = k_final

    # Build RetrievedChunkTrace from chunks
    for chunk in chunks:
        chunk_id = getattr(chunk, "id", None) or str(getattr(chunk, "point_id", ""))
        doc_key = getattr(chunk, "doc_key", "") or ""
        version = getattr(chunk, "version", None)
        domain = getattr(chunk, "domain", None)
        score = getattr(chunk, "score", 0.0) or 0.0
        freshness = session.memory_state.freshness_scores.get(chunk_id, None)

        trace.retrieval_events.append(RetrievedChunkTrace(
            chunk_id=str(chunk_id),
            doc_key=str(doc_key),
            version=version,
            domain=domain,
            score_before_mmr=score,
            score_after_mmr=score,
            freshness_score=freshness,
        ))

    logger.debug(
        "trace_retrieval_appended",
        session_id=session.session_id,
        chunks_traced=len(chunks),
        phase_ms=phase_ms,
    )


def append_agent_trace(
    session: ARCHESSession,
    name: str,
    role: str,
    input_summary: str,
    output_summary: str,
    latency_ms: int,
    vote: float | None = None,
    model_name: str | None = None,
) -> None:
    """Append agent invocation to cognitive trace."""
    if not session.cognitive_trace:
        return

    trace = session.cognitive_trace
    trace.agents.append(AgentTrace(
        name=name,
        role=role,
        input_summary=input_summary[:200],
        output_summary=output_summary[:200],
        vote=vote,
        latency_ms=latency_ms,
        model_name=model_name,
    ))

    logger.debug(
        "trace_agent_appended",
        session_id=session.session_id,
        agent_name=name,
        latency_ms=latency_ms,
    )


def append_research_trace(
    session: ARCHESSession,
    query: str,
    provider: str,
    success: bool,
    duration_ms: int,
    results_count: int,
    meta: Dict[str, Any] | None = None,
) -> None:
    """Append research call to cognitive trace."""
    if not session.cognitive_trace:
        return

    trace = session.cognitive_trace
    trace.research_calls.append(ResearchCallTrace(
        query=query[:200],
        provider=provider,
        success=success,
        duration_ms=duration_ms,
        results_count=results_count,
        meta=meta or {},
    ))

    logger.debug(
        "trace_research_appended",
        session_id=session.session_id,
        provider=provider,
        success=success,
    )


def append_error_trace(
    session: ARCHESSession,
    error: str,
    severity: str = "error",
) -> None:
    """Append error to cognitive trace."""
    if not session.cognitive_trace:
        return

    trace = session.cognitive_trace
    trace.add_error(error)
    if severity in ("error", "low_confidence"):
        trace.severity = severity

    logger.debug(
        "trace_error_appended",
        session_id=session.session_id,
        severity=severity,
    )


def populate_trace_from_session(
    session: ARCHESSession,
    trace: CognitiveTrace,
) -> None:
    """Populate trace metadata from session state."""
    # Add memory stats
    trace.chunks_used_count = len(session.memory_state.chunks_used)
    trace.domains_used = session.memory_state.domains

    # Add agent count
    trace.agents_invoked_count = len(session.agent_results)

    # Add flags
    trace.research_triggered = session.flags.is_research_triggered
    trace.gap_detected = session.flags.gap_detected
