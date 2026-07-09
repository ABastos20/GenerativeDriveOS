from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

class RetrievalMode(str, Enum):
    """Retrieval modes for cognitive governance.
    
    NORMAL: Default retrieval - excludes system docs, excludes stale
    META: Introspection mode - includes jarvis-core, for "how do you work?" queries
    TIME_SLICE: Temporal navigation - filters by date, for "what did I do on X date?" queries
    HISTORICAL: Archive mode - includes stale/legacy docs, for "original PRD" queries
    """
    NORMAL = "normal"
    META = "meta"
    TIME_SLICE = "time_slice"
    HISTORICAL = "historical"

@dataclass
class SearchResult:
    """Single search result from memory."""

    text: str
    score: float
    source_file: Optional[str]
    section: Optional[str]
    domain: Optional[str]
    metadata: dict
    doc_id: Optional[str] = None
    doc_key: Optional[str] = None
    freshness_score: float = 1.0  # NEW: 0.0-1.0, higher = fresher (Story 4.5.3)
