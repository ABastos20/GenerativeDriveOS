"""ARCHES Memory Controller - Memory tracking and retrieval coordination.

Part of cognitive architecture split for autonomous self-improvement safety.
Handles memory state, freshness tracking, and retrieval coordination.
"""
from typing import Any, List

import structlog

from jarvis.arches.state import ARCHESSession
from jarvis.arches.memory_tracker import record_memory_usage

logger = structlog.get_logger(__name__)


class ArchesMemoryController:
    """Manages memory tracking and retrieval state.
    
    Responsibilities:
    - Memory usage recording
    - Freshness computation
    - Retrieval state coordination
    """

    def __init__(self):
        """Initialize memory controller."""
        self.logger = logger

    def record_memory_usage(
        self,
        session: ARCHESSession,
        chunks: List[Any],
        domains: List[str] | None = None,
    ) -> None:
        """Track which chunks and domains were used in retrieval.
        
        Delegates to memory_tracker module for implementation.
        """
        record_memory_usage(session, chunks, domains)

    def compute_freshness(self, chunks: List[Any]) -> dict[str, float]:
        """Compute freshness scores.
        
        Delegates to memory_tracker module.
        """
        from jarvis.arches.memory_tracker import compute_freshness
        return compute_freshness(chunks)
