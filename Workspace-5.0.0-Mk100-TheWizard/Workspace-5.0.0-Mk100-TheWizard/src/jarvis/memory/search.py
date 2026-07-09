"""Memory retrieval service for JARVIS.

Refactored into `jarvis.memory.retrieval` package (Story 8-5).
This file remains as a facade for backward compatibility.
"""

from __future__ import annotations

from jarvis.memory.retrieval.types import RetrievalMode, SearchResult
from jarvis.memory.retrieval.filters import (
    detect_retrieval_mode,
    parse_date_from_query,
    build_filter_for_mode,
    MONTH_NAMES,
    DATE_PATTERNS,
    META_KEYWORDS,
    TEMPORAL_KEYWORDS,
    HISTORICAL_KEYWORDS,
)
from jarvis.memory.retrieval.core import (
    search_memory,
    keyword_search,
    document_keyword_search,
    hybrid_search,
    deduplicate_results,
    _embed_query,
)
from jarvis.memory.retrieval.fusion import expanded_search
from jarvis.database import qdrant as qdrant_db

def _build_filter(*args, **kwargs):
    """Facade for backward compatibility with legacy tests.
    
    Legacy tests often expect raw access without system document filtering
    unless explicitly requested.
    """
    if "include_system_docs" not in kwargs:
        kwargs["include_system_docs"] = True
    return build_filter_for_mode(*args, **kwargs)

# Re-export for compatibility
__all__ = [
    "RetrievalMode",
    "SearchResult",
    "search_memory",
    "keyword_search",
    "document_keyword_search",
    "hybrid_search",
    "expanded_search",
    "deduplicate_results",
    "detect_retrieval_mode",
    "_embed_query",
    "qdrant_db",
]
