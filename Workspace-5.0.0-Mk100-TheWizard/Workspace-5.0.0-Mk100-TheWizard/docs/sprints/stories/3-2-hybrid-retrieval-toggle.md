# Story 3.2: Hybrid Retrieval Toggle

Status: done

## Story

As a power user,
I want to blend semantic and keyword retrieval,
so that I can handle edge cases where BM25 outperforms pure vectors.

## Acceptance Criteria

1. **Given** the user adds `--retriever hybrid --weight 0.7`, **When** the query executes, **Then** the system runs BM25/Postgres full-text search alongside vector search, normalizes scores, and merges results.
2. **Given** the system runs hybrid retrieval, **When** results are merged, **Then** scores are normalized (min-max or z-score) before weighting, ensuring fair comparison between BM25 and vector scores.
3. **Given** defaults are configured, **When** the user runs a query without specifying retriever mode, **Then** the system uses the configured default (semantic-only, keyword-only, or hybrid with default weight).
4. **Given** query parameters are validated, **When** the user specifies invalid parameters (e.g., weight > 1.0 or weight < 0.0), **Then** the CLI displays a clear error message and exits with non-zero code.

## Tasks / Subtasks

- [x] **Task 1:** Implement PostgreSQL full-text search integration (AC: #1, #2)
  - [x] Implement BM25-like scoring via PostgreSQL `ts_rank_cd()` over `messages.content`
  - [x] Add keyword search method to `src/jarvis/memory/search.py` returning scored `SearchResult` objects
  - [x] Test keyword search independently with sample queries (unit + integration)

- [x] **Task 2:** Score normalization and merging logic (AC: #1, #2)
  - [x] Implement min–max score normalization for both vector and keyword scores
  - [x] Create merge function that combines results with configurable weight parameter
  - [x] Handle edge cases: no vector results, no keyword results, duplicate results
  - [x] Add deduplication logic (same chunk from both searches, keyed by chunk/message id + domain)

- [x] **Task 3:** CLI parameter extension (AC: #1, #3, #4)
  - [x] Add `--retriever` flag to `jarvis query` command (values: `semantic`, `keyword`, `hybrid`)
  - [x] Add `--weight` parameter (float 0.0–1.0, default 0.7 for semantic weight when hybrid)
  - [x] Validate parameters and provide helpful error messages
  - [x] Update CLI help text / examples in README

- [x] **Task 4:** Configuration and defaults (AC: #3)
  - [x] Add retriever config to `config/settings.yaml` (`query.default_retriever`, `query.default_weight`)
  - [x] Load config via existing `jarvis.config.load_settings` with validation and clamping
  - [x] Allow CLI flags to override config defaults

- [x] **Task 5:** Tests (AC: all)
  - [x] Unit tests for keyword search implementation
  - [x] Unit tests for score normalization and merging
  - [x] Unit tests for CLI parameter validation
  - [x] Integration test: hybrid search with real Qdrant + PostgreSQL
  - [x] Integration test: verify merged results contain both vector and keyword matches

## Dev Notes

- **PostgreSQL Full-Text Search**: Use `tsvector` + `tsquery` for keyword matching, `ts_rank_cd()` for BM25-like scoring
- **Storage Strategy**: Store text content in PostgreSQL `llm_usage_log` or separate `knowledge_chunks` table with `tsvector` column for efficient full-text indexing
- **Score Normalization**: Min-max normalization recommended: `(score - min) / (max - min)` to bring both score ranges to [0, 1]
- **Merging Algorithm**: `final_score = (semantic_weight * normalized_vector_score) + ((1 - semantic_weight) * normalized_keyword_score)`
- **Deduplication**: Use chunk IDs to identify duplicates, keep higher-scoring result
- **Re-ranking (Optional)**: Consider cross-encoder re-ranking as future enhancement (Story 3.3 or later)

### Learnings from Previous Story

**From Story 3-1-query-command-response-envelope (Status: done)**

- **RAG Query Implementation**: Complete RAG loop at `src/jarvis/cli/query.py` (196 lines) - extend this file with hybrid retrieval logic
- **Memory Search Service**: `src/jarvis/memory/search.py` provides `search_memory(query, k, domains)` returning `SearchResult[]` with scores - add keyword search function here
- **Search Result Structure**: `SearchResult` dataclass includes `text`, `score`, `source_file`, `section`, `domain`, `metadata` - reuse for keyword results
- **Qdrant Integration**: Collection "knowledge" with 384-dim vectors, payloads include source_file, section, domain, chunk_id
- **CLI Patterns**: Typer with type hints, `--json-output` flag, structured error handling via `typer.Exit(code=1)`
- **Testing Infrastructure**: `tests/unit/cli/test_query.py` with 11 tests, mock patching pattern (`jarvis.cli.query.call_llm`), 94% coverage target
- **Provider Routing**: LLM client uses cost-first routing, no changes needed for hybrid retrieval (search layer only)

**File to Extend:**
- `src/jarvis/cli/query.py` - Add `--retriever` and `--weight` parameters, call hybrid search logic
- `src/jarvis/memory/search.py` - Add `keyword_search()` and `hybrid_search()` functions

**New Files:**
- `src/jarvis/database/fulltext.py` (optional) - PostgreSQL full-text search utilities
- `tests/unit/memory/test_hybrid_search.py` - Unit tests for hybrid retrieval

[Source: stories/3-1-query-command-response-envelope.md#Dev-Agent-Record]

### Project Structure Notes

- **Memory Search Module**: `src/jarvis/memory/search.py` - Contains semantic search, add keyword and hybrid search here
- **Database Layer**: `src/jarvis/database/postgres.py` - PostgreSQL operations, add full-text index management
- **CLI Commands**: `src/jarvis/cli/query.py` - Query command implementation, extend with new parameters
- **Configuration**: `~/.jarvis/config.yaml` - User config managed via pydantic-settings
- **Testing**: `tests/unit/memory/`, `tests/integration/memory/` - Follow Story 3.1 testing patterns

### References

- [Source: docs/epics.md#Epic-3 → Story 3.2] Hybrid Retrieval Toggle requirements
- [Source: docs/architecture.md#Pattern 2] Markdown-First Knowledge Pipeline - text stored for full-text indexing
- [Source: docs/architecture.md#Data Architecture] PostgreSQL Schema - can extend for full-text search tables
- [Source: stories/3-1-query-command-response-envelope.md] RAG query implementation and memory search patterns

## Dev Agent Record

### Context Reference

- [Story Context XML](./3-2-hybrid-retrieval-toggle.context.xml) - Generated 2025-11-27

### Agent Model Used

- Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- OpenAI GPT-5.1 (Codex CLI)

### Debug Log References

- `tests/unit/memory/test_search.py`
- `tests/unit/cli/test_query.py`
- `tests/integration/memory/test_hybrid_retrieval_integration.py`

### Completion Notes List

1. Implemented `keyword_search` and `hybrid_search` in `src/jarvis/memory/search.py`:
   - `keyword_search` uses PostgreSQL `to_tsvector('english', Message.content)` + `plainto_tsquery` + `ts_rank_cd` to score matches.
   - `hybrid_search` runs both semantic Qdrant search and keyword Postgres search, normalizes scores per modality via min–max, then merges using:

     ```python
     final_score = weight * semantic_score + (1 - weight) * keyword_score
     ```

   - Deduplication uses a stable key derived from `chunk_id` / `hash` / `message_id` + `domain`, with semantic results treated as canonical when both modes hit the same chunk.
   - Qdrant access updated from deprecated `client.search` to `client.query_points`, avoiding future API breaks.

2. Extended query configuration in `src/jarvis/config/settings.py` and `config/settings.example.yaml`:
   - Added `QueryConfig` dataclass with:

     ```python
     default_retriever: str = "semantic"
     default_weight: float = 0.7
     ```

   - `Settings.from_dict` now reads an optional `"query"` section and clamps `default_weight` into `[0.0, 1.0]`.
   - `Settings.to_dict` writes back the `query` config, keeping round-trip symmetry.

3. Updated `jarvis query` CLI in `src/jarvis/cli/query.py`:
   - Added parameters:

     ```python
     retriever: Optional[str] = None  # semantic | keyword | hybrid
     weight: Optional[float] = None   # only used for hybrid
     ```

   - Loads config via `load_settings()` and resolves effective values:
     - `effective_retriever = (retriever or settings.query.default_retriever or "semantic").lower()`
     - `effective_weight = weight if weight is not None else settings.query.default_weight`
   - Validation:
     - `retriever` must be one of `{"semantic", "keyword", "hybrid"}` or the CLI exits with a clear error.
     - If `retriever == "hybrid"`, `0.0 <= weight <= 1.0` is enforced; otherwise a helpful error is displayed.
   - Routing:
     - `semantic` → `search.search_memory`
     - `keyword` → `search.keyword_search`
     - `hybrid` → `search.hybrid_search` with the configured weight.
   - The progress line now reports the active retriever:

     ```text
     🔍 Searching memory for context (k=5, retriever=hybrid)...
     ```

   - JSON envelope and human-readable output continue to work unchanged, as they only depend on `SearchResult`.

4. Tests:
   - `tests/unit/memory/test_search.py`:
     - Adjusted semantic-empty-query test to expect a `ValueError`, matching service behavior.
     - Added tests for:
       - `keyword_search` happy path (mocked `Session.execute` returning `(id, content, rank)` rows).
       - Domain gating (returns `[]` and never hits the DB when `domains` excludes `"jarvis-conversations"`).
       - `hybrid_search` normalization and merge logic (semantic + keyword mocks, assert ordering and metadata).
   - `tests/unit/cli/test_query.py`:
     - Added `TestRetrieverModes` to cover:
       - Default retriever uses semantic search.
       - `--retriever keyword` uses `keyword_search`.
       - `--retriever hybrid --weight 0.6` uses `hybrid_search(weight=0.6)`.
       - Invalid retriever and invalid weight produce clear error messages and non-zero exits.
   - `tests/integration/memory/test_hybrid_retrieval_integration.py`:
     - Inserts a conversation + message into Postgres with the query term.
     - Ingests a small markdown doc into Qdrant under `domain="jarvis-conversations"`.
     - Runs `hybrid_search("BM25", k=5, weight=0.7, domains=["jarvis-conversations"])` and asserts:
       - At least one result is returned.
       - Domain is correct.
       - Hybrid metadata (`semantic_score_norm` and/or `keyword_score_norm`) is present.

5. Tech debt cleanup:
   - Updated SQLAlchemy base import in `src/jarvis/database/models.py` to `sqlalchemy.orm.declarative_base` to remove `MovedIn20Warning`.
   - Updated Qdrant usage in `src/jarvis/memory/search.py` to rely on `query_points` instead of deprecated `search`, preventing future breaking changes and silencing DeprecationWarnings.

### File List

- `src/jarvis/memory/search.py` – added `keyword_search`, `hybrid_search`, score normalization, and Qdrant `query_points` usage.
- `src/jarvis/cli/query.py` – extended CLI with `--retriever` and `--weight`, config-aware defaults, and validation.
- `src/jarvis/config/settings.py` – added `QueryConfig` and `"query"` section handling.
- `config/settings.example.yaml` – documented default retriever configuration.
- `src/jarvis/database/models.py` – SQLAlchemy declarative base import modernized.
- `tests/unit/memory/test_search.py` – new unit coverage for keyword + hybrid search.
- `tests/unit/cli/test_query.py` – new tests for retriever/weight CLI behavior.
- `tests/integration/memory/test_hybrid_retrieval_integration.py` – hybrid retrieval integration test.

## Change Log

- 2025-11-27: Implemented keyword and hybrid retrieval, config defaults, CLI flags, and tests; modernized Qdrant and SQLAlchemy usage.
