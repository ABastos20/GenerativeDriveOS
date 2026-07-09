# Plan – Story 2.4: Memory Retrieval Filters & API

This document is Jarvis’ internal plan for implementing Story **2.4 – Memory Retrieval Filters & API**, aligned with BMAD `dev-story` workflow and Jarvis core docs.

## 1. Inputs & Context

- Story: `docs/sprints/stories/2-4-memory-retrieval-filters-api.md`
- Context: `docs/sprints/stories/2-4-memory-retrieval-filters-api.context.xml`
- Jarvis core:
  - `docs/jarvis/persona.md`
  - `docs/jarvis/operating-manual.md`
  - `docs/jarvis/gd-overview.md`
  - Relevant playbooks under `docs/jarvis/playbooks/`
- Existing plumbing:
  - Qdrant wrapper: `src/jarvis/database/qdrant.py`
  - Ingestion pipeline: `src/jarvis/memory/ingest.py`
  - Bootstrap script: `scripts/bootstrap_jarvis_memory.py`

## 2. High-Level Goals (from Story 2.4)

- Provide a retrieval path that:
  - Queries Qdrant for vector similarity.
  - Uses PostgreSQL metadata (persona, source type, time) as filters.
  - Returns ranked snippets with metadata and citations.
- Expose:
  - CLI: `jarvis memory search --persona … --since … --source …`
  - API: a FastAPI endpoint matching the CLI filters.
- Support Jarvis core domains:
  - `domain = "jarvis-core"` for persona/ops.
  - `domain = "jarvis-conversations"` for GPT export history.

## 3. Implementation Phases

### Phase A – Retrieval Core (Python service)

1. Design a retrieval service module, e.g. `src/jarvis/memory/search.py`:
   - Functions:
     - `search_memory(query: str, *, persona: str | None, source: str | None, since: datetime | None, until: datetime | None, k: int = 10, domains: list[str] | None = None) -> List[Result]`
   - Responsibilities:
     - Embed query (reuse embedding model from ingestion).
     - Call Qdrant for top‑k vectors (collection `knowledge`).
     - Optionally filter by `domain` and other payload fields.
   - For metadata filters:
     - v1 can use Qdrant payload filters.
     - Later, extend to join with PostgreSQL (conversations/docs) if needed.

2. Define a `Result` dataclass:
   - Fields: `text`, `score`, `source_file`, `section`, `domain`, `metadata`.

### Phase B – CLI Integration

1. Add a `search` command under `src/jarvis/cli/memory.py`:
   - `jarvis memory search "question" --persona "Rickiest Rick" --since 7d --source jarvis-core --k 10`
   - Parse:
     - `--persona`
     - `--source` (e.g., `jarvis-core`, `jarvis-conversations`, `docs`, etc.)
     - `--since` / `--until` (relative or absolute time).
     - `--k` (with safe bounds).
   - Call `search_memory()` and render results:
     - Text snippet + metadata.
     - Optional JSON output for tooling.

### Phase C – API Integration

1. Add an endpoint in `src/jarvis/api`:
   - e.g. `GET /api/memory/search`
   - Request model:
     - `query: str`
     - `persona: Optional[str]`
     - `source: Optional[str]`
     - `since: Optional[datetime]`
     - `until: Optional[datetime]`
     - `k: int`
   - Response model:
     - List of `Result` objects (as in Phase A).
   - Hook into the same `search_memory()` core to avoid duplication.

### Phase D – Tests

1. Unit tests:
   - `tests/unit/memory/test_search.py`:
     - Filter parsing (persona/source/time).
     - Result shaping and scoring logic (with mocked Qdrant).

2. Integration tests:
   - `tests/integration/memory/test_search_integration.py`:
     - Requires Docker stack (Postgres + Qdrant + Jarvis).
     - Use pre‑ingested data (bootstrap script) to:
       - Query `domain = "jarvis-core"` and confirm persona/ops snippets.
       - Query `domain = "jarvis-conversations"` and confirm GPT history retrieval.

### Phase E – Story & Sprint Updates

1. Once implementation and tests pass:
   - Update `docs/sprints/stories/2-4-memory-retrieval-filters-api.md`:
     - Check all Tasks/Subtasks.
     - Fill Dev Agent Record (debug log, completion notes, file list, change log).
     - Set Status to `review`.
   - Update `docs/sprints/sprint-status.yaml`:
     - `2-4-memory-retrieval-filters-api: review`.

## 4. Jarvis Behavioral Notes

- Always favour:
  - Clear filters (persona/source/time/domain) over opaque scoring.
  - Testability (unit + integration) and reproducible commands.
- When building prompts later (FR2/FR3), reuse `search_memory()` as the retrieval backbone instead of bespoke queries.

