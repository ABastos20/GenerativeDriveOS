# Story 4.5.3: Memory Recency & Lineage Enforcement

Status: done

## Story

As a **Jarvis user asking time-sensitive questions**,
I want **retrieval to prioritize recent document versions and warn about stale content**,
so that **I don't receive outdated information when newer versions exist in the knowledge base**.

## Acceptance Criteria

1. [x] Retrieval computes freshness score using `doc_last_seen` timestamp
2. [x] Freshness formula: `1.0 / (1 + age_days / 30)` (30-day half-life)
3. [x] Results filtered by `min_freshness` threshold (default: 0.5)
4. [x] Version conflicts detected when multiple versions of same doc exist
5. [x] Newest version preferred, stale chunks quarantined from results
6. [x] Warning logs emitted when retrieving from stale documents
7. [x] CLI flag `--allow-stale` overrides freshness filtering
8. [x] API parameter `allow_stale` available on search endpoints

## Tasks / Subtasks

- [x] Task 1: Implement freshness scoring (AC: #1, #2)
- [x] Task 2: Filter by freshness threshold (AC: #3)
- [x] Task 3: Version conflict resolution (AC: #4, #5)
- [x] Task 4: Logging and observability (AC: #6)
- [x] Task 5: CLI and API integration (AC: #7, #8)
- [x] Task 6: Unit tests

## Dev Notes

- **Decay Model**: 30-day half-life balances recency vs. stability
- **Override Semantics**: `--allow-stale` shows ALL results but still logs warnings
- **Conflict Strategy**: Base key extraction uses `-v` suffix regex pattern

### Project Structure Notes

- Primary: `src/jarvis/memory/search.py`
- CLI: `src/jarvis/cli/query.py`

### References

- [Source: docs/sprints/epic-4.5-arches-stabilization.md#Story-4.5.3]

## Dev Agent Record

### Context Reference

- [4-5-3-memory-recency-lineage-enforcement.context.xml](docs/sprints/stories/4-5-3-memory-recency-lineage-enforcement.context.xml)

### Agent Model Used

Gemini 2.5 Pro (BMAD Orchestrator Mode)

### Debug Log References

- Unit tests: 16 passed in tests/unit/memory/test_freshness_scoring.py

### Completion Notes List

- Created `_compute_freshness_score()` with 30-day half-life decay
- Created `_apply_freshness_filter()` with min_freshness threshold
- Created `_resolve_version_conflicts()` for document lineage
- Updated `search_memory()`, `keyword_search()`, `hybrid_search()` with allow_stale param
- Added `--allow-stale` CLI flag to query command
- Added structured logging for stale docs and version conflicts
- Created 16 unit tests covering all freshness functions

### File List

- [MODIFIED] src/jarvis/memory/search.py - Freshness scoring, filtering, version resolution
- [MODIFIED] src/jarvis/cli/query.py - --allow-stale CLI flag
- [NEW] tests/unit/memory/test_freshness_scoring.py - 16 unit tests
