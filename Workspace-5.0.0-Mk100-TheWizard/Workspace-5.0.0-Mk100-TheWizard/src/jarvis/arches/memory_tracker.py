"""Memory tracking helpers for ARCHES."""
from typing import Any, Dict, List
from datetime import datetime, timezone

import structlog

from jarvis.arches.state import ARCHESSession, MemoryState

logger = structlog.get_logger(__name__)


def record_memory_usage(
    session: ARCHESSession,
    chunks: List[Any],
    domains: List[str] | None = None,
) -> None:
    """Track which chunks and domains were used in retrieval.
    
    Args:
        session: The current session
        chunks: List of retrieved chunks
        domains: Optional list of domains accessed
    """
    # Extract chunk IDs
    chunk_ids = []
    for chunk in chunks:
        if hasattr(chunk, "id"):
            chunk_ids.append(str(chunk.id))
        elif hasattr(chunk, "point_id"):
            chunk_ids.append(str(chunk.point_id))
        elif isinstance(chunk, dict) and "id" in chunk:
            chunk_ids.append(str(chunk["id"]))

    # Compute freshness scores
    freshness_scores = compute_freshness(chunks)

    # Calculate average freshness
    avg_freshness = 0.0
    if freshness_scores:
        avg_freshness = sum(freshness_scores.values()) / len(freshness_scores)

    # Update session memory state
    session.memory_state.chunks_used = chunk_ids
    session.memory_state.domains = list(domains) if domains else []
    session.memory_state.freshness_scores = freshness_scores
    session.memory_state.retrieved_at = datetime.now(timezone.utc).isoformat()
    session.memory_state.total_chunks_retrieved = len(chunks)
    session.memory_state.average_freshness = avg_freshness
    session.touch()

    logger.debug(
        "memory_usage_recorded",
        session_id=session.session_id,
        chunks_used=len(chunk_ids),
        domains=domains,
        average_freshness=round(avg_freshness, 3),
    )


def compute_freshness(chunks: List[Any]) -> Dict[str, float]:
    """Compute freshness scores using 30-day half-life decay.
    
    Returns:
        Dict mapping chunk_id to freshness score (0.0-1.0)
    """
    scores: Dict[str, float] = {}
    now = datetime.now(timezone.utc)

    for chunk in chunks:
        # Get chunk ID
        chunk_id = None
        if hasattr(chunk, "id"):
            chunk_id = str(chunk.id)
        elif hasattr(chunk, "point_id"):
            chunk_id = str(chunk.point_id)
        elif isinstance(chunk, dict) and "id" in chunk:
            chunk_id = str(chunk["id"])
        else:
            continue

        # Get timestamp
        timestamp = None
        for attr in ["created_at", "updated_at", "doc_last_seen", "timestamp"]:
            if hasattr(chunk, attr):
                timestamp = getattr(chunk, attr)
                break
            elif hasattr(chunk, "metadata") and chunk.metadata:
                meta = chunk.metadata if isinstance(chunk.metadata, dict) else {}
                if attr in meta:
                    timestamp = meta[attr]
                    break
            elif isinstance(chunk, dict):
                if attr in chunk:
                    timestamp = chunk[attr]
                    break
                if "metadata" in chunk and isinstance(chunk["metadata"], dict):
                    if attr in chunk["metadata"]:
                        timestamp = chunk["metadata"][attr]
                        break

        # Parse timestamp and compute age
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    dt = now
            elif isinstance(timestamp, datetime):
                dt = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
            else:
                dt = now

            age_days = (now - dt).total_seconds() / 86400
        else:
            age_days = 0  # Assume fresh if no timestamp

        # Apply 30-day half-life decay
        scores[chunk_id] = 1.0 / (1 + age_days / 30)

    return scores
