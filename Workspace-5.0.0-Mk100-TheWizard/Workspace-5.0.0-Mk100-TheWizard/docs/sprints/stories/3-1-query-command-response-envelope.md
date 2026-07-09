# Story 3.1: Query Command & Response Envelope

Status: done

## Story

As a knowledge worker,
I want a `jarvis query "question"` command,
so that I can ask anything and receive structured answers with metadata.

## Acceptance Criteria

1. **Given** memories exist, **When** the user queries via CLI or MCP, **Then** the system embeds the query, fetches top-k context, calls the selected LLM, and returns text + cited sources.
2. **Given** the CLI query succeeds, **When** called with `--json-output`, **Then** the response includes a JSON envelope with `query`, `response`, `sources[]`, and `metadata` matching the PRD shape.
3. **Given** chunk metadata in Qdrant, **When** results are returned, **Then** each source entry includes enough information (source_file, domain, optional chunk_id) to map back to workspace files.
4. **Given** provider routing is configured, **When** `provider="auto"` is used, **Then** the system prefers free/cheap providers and falls back to others only when necessary.

## Tasks / Subtasks

- [x] **Task 1:** Implement RAG query command (AC: #1, #2, #3)
  - [x] Create `src/jarvis/cli/query.py` with Typer-based CLI entrypoint
  - [x] Wire query command into JARVIS CLI main app (`src/jarvis/cli/main.py`)
  - [x] Implement RAG loop: embed query, search Qdrant (k=5 default), build context block
  - [x] Call `call_llm()` with provider routing (defaults to "auto")
  - [x] Return human-readable answer with citations in CLI
  - [x] Add JSON response envelope (`--json-output`) for MCP / tool integrations
  - [x] Include chunk IDs / metadata for linking back to workspace files
  - [x] Ensure error handling for empty results and provider failures

- [x] **Task 2:** Provider routing integration (AC: #4)
  - [x] Use existing LLM client infrastructure from Story 2.5
  - [x] Ensure `provider="auto"` uses priority routing (OpenRouter → Perplexity → Official CLIs → Fallback CLI wrappers → Direct APIs)
  - [x] Test LLM response with citations and cost tracking

- [x] **Task 3:** CLI parameters and validation (AC: #1, #2, #3)
  - [x] Add CLI parameters: `question` (required), `provider` (default: "auto"), `source` (optional domain filter), `k` (default: 5, range: 1-20), `max_tokens` (default: 2000), `json_output` (boolean flag)
  - [x] Validate `k` parameter range (1-20)
  - [x] Handle no results gracefully with user guidance

- [x] **Task 4:** Tests (AC: all)
  - [x] Unit tests for query parameter validation
  - [x] Unit tests for context building and citation formatting
  - [x] Integration test: query with real memory data, verify response format
  - [x] Integration test: JSON output envelope validation

## Dev Notes

- Reuse LLM client infrastructure from Story 2.5 (`src/jarvis/llm/client.py`)
- Follow memory search patterns from Story 2.4 (`src/jarvis/memory/search.py`)
- Follow CLI patterns from `src/jarvis/cli/memory.py` (Typer with type hints)
- RAG loop: Query → Embed → Search (top-k) → Build context → LLM call → Format response
- Citations: Track source_file, section, domain, relevance score for each retrieved chunk
- JSON envelope matches PRD schema: `{query, response, sources[], metadata{}}`
- Progressive streaming mentioned in Epic 3 AC but deferred (outputs after completion for MVP)
- Error handling: Empty results, LLM failures, invalid parameters

### Learnings from Previous Story

**From Story 2-5-scheduled-memory-compilation (Status: done)**

- **LLM Client Infrastructure**: Complete provider routing at `src/jarvis/llm/client.py` with OpenRouter, Perplexity, Official CLIs (claude, codex, gemini), Fallback CLI wrappers (claude-cli, codex-cli, gemini-cli), and Direct APIs (GoogleAI, Anthropic, OpenAI) - use `call_llm()` for all LLM interactions
- **Memory Search Service**: Available at `src/jarvis/memory/search.py` with `search_memory(query, k, domains)` - returns `SearchResult[]` with text, score, metadata
- **CLI Patterns**: Follow Typer patterns in `src/jarvis/cli/memory.py` - use type hints, structlog, and error handling with `typer.Exit(code=...)`
- **Domain Filtering**: Qdrant payloads include `domain` field (jarvis-core, jarvis-conversations, jarvis-insights) - filter using `domains=[...]` parameter
- **Cost Tracking**: `LLMResponse` includes provider, model, input_tokens, output_tokens, cost_usd - display in CLI output footer
- **Structlog**: Log metadata only, not content; use events like `query_start`, `query_completed`, `llm_call_completed`
- **Typer/Click Compatibility**: Click 8.1.7 pinned in pyproject.toml to resolve compatibility issues - use simple parameter defaults without explicit `typer.Option()` wrappers

[Source: stories/2-5-scheduled-memory-compilation.md#Dev-Agent-Record]

### Project Structure Notes

- CLI entrypoint: `src/jarvis/cli/query.py` (new module)
- Main CLI wiring: `src/jarvis/cli/main.py` (add query command)
- Memory search: `src/jarvis/memory/search.py` (reuse from Story 2.4)
- LLM integration: `src/jarvis/llm/client.py` (reuse from Story 2.5)
- Testing: `tests/unit/cli/test_query.py`, `tests/integration/cli/test_query_integration.py`

### References

- [Source: docs/epics.md#Epic-3 → Story 3.1] Query Command & Response Envelope requirements
- [Source: docs/prd.md#FR1] RAG Query System with semantic search and citations
- [Source: docs/architecture.md#CLI Framework] Typer CLI patterns and error handling
- [Source: stories/2-4-memory-retrieval-filters-api.md] Memory search API and domain filtering
- [Source: stories/2-5-scheduled-memory-compilation.md] LLM client infrastructure and cost tracking

## Dev Agent Record

### Context Reference

- [3-1-query-command-response-envelope.context.xml](3-1-query-command-response-envelope.context.xml)

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

### Completion Notes

**Completed:** 2025-11-27
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

**Task 4 - Test Implementation (2025-11-27)**

Created comprehensive test suite for RAG query command:

**Unit Tests** (`tests/unit/cli/test_query.py`):
- 11 unit tests covering all acceptance criteria
- Parameter validation: k range (1-20), edge cases
- Context building with search results and citations
- JSON output envelope structure validation
- Error handling: no results, search failures, LLM failures
- Provider routing (auto and explicit providers)
- Mock patching strategy: Patch where functions are used (`jarvis.cli.query.call_llm`) not where defined

**Integration Tests** (`tests/integration/cli/test_query_integration.py`):
- Real memory search against Qdrant collection
- JSON output validation with real services
- Service availability checks with pytest.skip for graceful degradation

**Test Results**:
- All 11 unit tests passing
- 94.12% code coverage on `src/jarvis/cli/query.py` (85 statements, 5 missed)
- All acceptance criteria validated through tests

### File List

**New Files:**
- `src/jarvis/cli/query.py` - RAG query command implementation (196 lines)
- `tests/unit/cli/__init__.py` - Unit test package marker
- `tests/unit/cli/test_query.py` - Comprehensive unit tests (11 tests, 94% coverage)
- `tests/integration/cli/__init__.py` - Integration test package marker
- `tests/integration/cli/test_query_integration.py` - Integration tests with real services

**Modified Files:**
- `src/jarvis/cli/main.py` - Wired query command into main CLI app

## Change Log

- Created 2025-11-27: Initial story file created documenting implemented RAG query command
- Updated 2025-11-27: Task 4 completed - comprehensive test suite added (11 unit tests, integration tests, 94% coverage), all acceptance criteria validated, ready for review
