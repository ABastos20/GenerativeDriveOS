# Story 4.5.2: Agent Memory Attribution

Status: done

## Story

As a **Jarvis user debugging persona disagreements**,
I want **each agent's response to include which memory chunks, domains, and sources it used**,
so that **I can understand why agents gave different answers and trace their reasoning to specific documents**.

## Acceptance Criteria

1. [x] `AgentResponse` dataclass extended with `chunks_used`, `domains_accessed`, `sources`, `memory_freshness`
2. [x] `invoke_personas_parallel()` passes chunk context to each agent
3. [x] Context includes chunk IDs for attribution tracking (e.g., `[Source 1 | Chunk ID: abc123]`)
4. [x] Agent responses parsed to extract which chunks were actually cited
5. [x] Voting transcript includes per-agent memory attribution
6. [x] CLI `--show-all` displays agent-specific chunk usage
7. [x] API `/api/chat` returns agent attribution in response JSON
8. [x] Database stores `memory_attribution` JSONB per message

## Tasks / Subtasks

- [x] Task 1: Enhance AgentResponse dataclass (AC: #1)
- [x] Task 2: Modify parallel invocation (AC: #2, #3, #4)
- [x] Task 3: Update voting and consensus (AC: #5)
- [x] Task 4: CLI output formatting (AC: #6)
- [x] Task 5: API response updates (AC: #7)
- [x] Task 6: Database migration (AC: #8)

## Dev Notes

- **Key Insight**: Agents currently see identical context → attribution reveals if true diversity exists
- **Citation Pattern**: Use `[N]` format matching existing citation behavior
- **Performance**: Extraction should be regex-based, not LLM-based

### Project Structure Notes

- Modifies: `src/jarvis/agents/response.py`, `parallel_invocation.py`, `consensus.py`, `aggregator.py`
- API: `src/jarvis/api/schemas.py` 
- Migration: `alembic/versions/20241204_add_memory_attribution.py`

### References

- [Source: docs/sprints/epic-4.5-arches-stabilization.md#Story-4.5.2]
- [Source: src/jarvis/agents/parallel_invocation.py] - Current invocation logic

## Dev Agent Record

### Context Reference

- [4-5-2-agent-memory-attribution.context.xml](docs/sprints/stories/4-5-2-agent-memory-attribution.context.xml)

### Agent Model Used

Gemini 2.5 Pro (BMAD Orchestrator Mode)

### Debug Log References

- Unit tests: 17 passed in tests/unit/agents/test_memory_attribution.py

### Completion Notes List

- Created `MemoryAttribution` dataclass in `response.py` with chunks_used, domains_accessed, sources, memory_freshness
- Added `to_dict()` method for JSON serialization
- Added convenience properties on `PersonaResponse` for backward compatibility
- Created `_build_attributed_context()` function to add chunk IDs to context
- Created `_extract_used_chunks()` function with regex citation extraction
- Updated `invoke_personas_parallel()` to accept chunks parameter
- Updated `VotingResult` to include per-agent attribution dictionary
- Updated `weighted_chaos_vote()` to collect attribution from responses
- Enhanced `aggregate_responses()` in aggregator.py to display 📚 Memory Attribution in --show-all
- Added voting breakdown with chunk citation counts
- Created `AgentAttribution` Pydantic schema in schemas.py
- Added `agent_attributions` optional field to `ChatMetadata`
- Added `memory_attribution` JSONB column to `Message` model
- Created alembic migration `20241204_add_memory_attribution.py` with GIN index

### File List

- [MODIFIED] src/jarvis/agents/response.py - Added MemoryAttribution, updated PersonaResponse
- [MODIFIED] src/jarvis/agents/parallel_invocation.py - Added attribution functions
- [MODIFIED] src/jarvis/agents/consensus.py - Added attribution to VotingResult
- [MODIFIED] src/jarvis/agents/aggregator.py - Added attribution display in --show-all
- [MODIFIED] src/jarvis/api/schemas.py - Added AgentAttribution schema
- [MODIFIED] src/jarvis/database/models.py - Added memory_attribution column
- [NEW] alembic/versions/20241204_add_memory_attribution.py - DB migration
- [NEW] tests/unit/agents/test_memory_attribution.py - 17 unit tests
