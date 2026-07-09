# Story 2.4: Memory Retrieval Filters & API

Status: done

## Story

As an analyst,  
I want to search memories by source type, time, and persona,  
So that I can retrieve the right context for workflows.

## Acceptance Criteria

1. **Given** stored conversations and documents, **When** the user runs `jarvis memory search --persona "Rickiest Rick" --since 7d`, **Then** the CLI returns ranked snippets with persona/time filters applied.
2. **Given** the API is called with equivalent filters, **When** the request completes, **Then** the response includes ranked results with metadata and citations.
3. **Given** filters and ranking execute, **When** results are returned, **Then** Qdrant vector search is combined with PostgreSQL metadata filters (persona/source/time) and returns <100ms P95 for k<=10 under nominal load.
4. **Given** invalid filters or empty results, **When** the user queries, **Then** clear errors or empty responses are returned without crashes.

## Tasks / Subtasks

- [x] **Task 1:** Define query/filter models (AC: #1, #2, #4)
  - [x] Add Pydantic schemas for CLI/API filter inputs (persona, since/until, source type, limit/k)
  - [x] Validate bounds (k, date ranges) and return structured errors

- [x] **Task 2:** Implement retrieval service (AC: #1, #3)
  - [x] Add service to merge PostgreSQL metadata filters with Qdrant vector search results
  - [x] Ensure vector config matches 384-d Cosine collection and reuse `knowledge` collection
  - [x] Normalize scores/ranks and cap latency targets in logs

- [x] **Task 3:** Expose endpoints/CLI (AC: #1, #2)
  - [x] Add `jarvis memory search` CLI with flags for persona, source, since/until, k
  - [x] Add API endpoint returning ranked snippets + metadata + citations

- [x] **Task 4:** Observability and errors (AC: #3, #4)
  - [x] Add structlog events for queries (filters, k, latency buckets) without logging content
  - [x] Handle empty-result and bad-filter paths with user-friendly messages

- [x] **Task 5:** Tests (AC: all)
  - [x] Unit tests for filter validation, query assembly, and score normalization
  - [x] Integration tests for error handling (empty query, invalid k)
  - [x] Performance/latency validation test targeting <100ms P95 for k<=10

## Dev Notes

- Align with `docs/epics.md` guidance: use PostgreSQL for metadata filtering and join results with Qdrant IDs; default vector settings 384-d Cosine, HNSW m=16/ef_construct=200/full_scan_threshold=10000.  
- Reuse Qdrant client wrapper (`src/jarvis/database/qdrant.py`) and existing CLI patterns (Typer + structlog).  
- Keep outputs citation-ready for future stories (3.x); include payload fields (source file, section, persona, timestamps).  
- Avoid logging query text; log filter parameters and counts only.

### Project Structure Notes

- CLI entrypoint under `src/jarvis/cli`; service logic under `src/jarvis/core` (or similar) separating transport from retrieval logic.  
- Persist/retrieve metadata via PostgreSQL models introduced in 2.1; ensure indexes support persona/time filters.  
- Qdrant collection `knowledge` already provisioned; do not recreate.

### References

- [Source: docs/epics.md#Epic-2 -> Story 2.4] Retrieval filters and API requirements  
- [Source: docs/architecture.md#Qdrant Configuration] Vector size/distance and HNSW defaults  
- [Source: docs/prd.md#FR4 Persistent Memory] Retrieval and filtering expectations  
- [Source: docs/test-design-system.md] Testing standards and fixtures

## Dev Agent Record

### Context Reference

- [2-4-memory-retrieval-filters-api.context.xml](2-4-memory-retrieval-filters-api.context.xml)

### Agent Model Used

- Codex CLI / GPT-5.1

### Debug Log References

- `QDRANT_HOST=qdrant QDRANT_PORT=6333` inside `jarvis-app` container used for live retrieval checks  
- Verified `qdrant-client==1.15.1` and working `search_memory()` calls against `knowledge` collection

### Completion Notes List

- Implemented `MemorySearchRequest`, `MemorySearchResult`, and `MemorySearchResponse` in `src/jarvis/api/schemas.py`
- Added `/api/memory/search` endpoint in `src/jarvis/api/memory.py` wired to `jarvis.memory.search.search_memory`
- Registered memory router in `src/jarvis/api/app.py`
- Added unit test `tests/unit/api/test_memory_search_api.py` mocking `search_memory`
- Documented working CLI and Docker commands in `JARVIS_INGESTION_GUIDE.md` Dev Commands Cheat Sheet
- Confirmed live retrieval in container returns `jarvis-core` snippets from `persona.md` and `operating-manual.md`
- ✅ **Story 2.4 Completion (2025-11-26):**
  - Added comprehensive error handling with ValueError for empty queries and invalid k values
  - Implemented structlog events: `memory_search_completed` with filters, k, result_count, duration_ms
  - Added performance validation test: `tests/integration/memory/test_search_performance.py` (P95 <100ms target for k<=10)
  - Improved API error responses: 400 BAD_REQUEST for invalid input, 503 for service failures
  - All 5 tasks marked complete, all acceptance criteria met

### File List

- `src/jarvis/api/schemas.py`  
- `src/jarvis/api/memory.py`  
- `src/jarvis/api/app.py`  
- `tests/unit/api/test_memory_search_api.py`  
- `JARVIS_INGESTION_GUIDE.md`
