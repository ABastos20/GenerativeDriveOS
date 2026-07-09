# Story 4-10: Temporal Retrieval & Time-Slice Mode

Status: done
Epic: 4 (ARCHES Stabilization & Cognitive Layer)
Completed: 2025-12-06

## Story

As a **Jarvis user navigating temporal context**,
I want **date-aware retrieval with TIME_SLICE mode**,
so that **I can ask "what did I do on X date?" and get accurate session/story docs**.

## Acceptance Criteria

1. [x] RetrievalMode enum with NORMAL, META, TIME_SLICE, HISTORICAL
2. [x] parse_date_from_query() extracts dates (2025-12-03 format)
3. [x] detect_retrieval_mode() classifies queries by keywords/dates
4. [x] _build_filter_for_mode() with semantic_family support
5. [x] Wire mode detection into ARCHES controller
6. [x] Add session_date to session docs during ingestion
7. [x] UI toggle for "Include historical docs" (via `allow_stale` param)

## Implementation

### Completed

```python
# In search.py
class RetrievalMode(str, Enum):
    NORMAL = "normal"      # Default - excludes system docs
    META = "meta"          # Introspection - includes jarvis-core
    TIME_SLICE = "time_slice"  # Temporal - filters by date
    HISTORICAL = "historical"  # Archive - includes stale docs
```

### Verification

- **Time Slice**: "What happened on 2025-12-03?" -> Filters by date range.
- **Historical**: "Show me old PRDs" -> Includes `is_latest=false` docs.

## References

- `src/jarvis/memory/search.py` - RetrievalMode, detect_retrieval_mode
- Story 4-9 (semantic_family implementation)
