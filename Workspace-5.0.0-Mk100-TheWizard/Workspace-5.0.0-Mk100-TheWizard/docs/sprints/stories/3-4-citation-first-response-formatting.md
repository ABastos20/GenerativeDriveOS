# Story 3.4: Citation‑First Response Formatting

Status: done

## Story

As an end user,  
I want every answer to cite its sources,  
So that I can verify correctness quickly.

## Acceptance Criteria

1. **Given** the RAG pipeline returns results, **When** the LLM returns a response, **Then** the CLI renders an answer that clearly associates statements with numbered citations.  
2. **Given** citations are displayed, **When** the user inspects them, **Then** each citation includes at least: filename (relative to workspace), logical section (if available), domain, and a relevance score or confidence.  
3. **Given** the user chooses `--json-output`, **When** `jarvis query` completes, **Then** the JSON envelope includes a `sources[]` array with structured provenance fields (filename, section, domain, score, optional chunk_id) suitable for MCP tooling.  
4. **Given** no sources are available (edge case), **When** the CLI renders output, **Then** it clearly indicates that no retrieved context was used instead of fabricating citations.

## Tasks / Subtasks

- [x] **Task 1:** Define citation metadata schema (AC: #2, #3)  
  - [x] Confirm/extend `SearchResult` and JSON envelope shape to include: `source_file`, `section`, `domain`, `score`, optional `chunk_id` and `hash`.  
  - [x] Document the `sources[]` structure in `docs/full-documentation.md` and `README.md` (API/CLI examples).  

- [x] **Task 2:** CLI human‑readable formatting (AC: #1, #2, #4)  
  - [x] Ensure `src/jarvis/cli/query.py` human output prints:  
    - An answer block.  
    - A “Sources” block with numbered entries `[1]`, `[2]`, … including filename, domain, section, and score.  
  - [x] Keep the format stable and easy to parse visually (simple block layout).  
  - [x] Handle the “no sources” case with an explicit message (no fabricated citations).  

- [x] **Task 3:** JSON envelope provenance (AC: #3)  
  - [x] Extend the `--json-output` envelope in `src/jarvis/cli/query.py` to emit a `sources[]` array, each entry including:  
    - `id`: citation index (1‑based).  
    - `source_file`: workspace‑relative path.  
    - `section`: logical heading / filename.  
    - `domain`: `jarvis-core`, `jarvis-conversations`, `jarvis-insights`, etc.  
    - `score` / `relevance_score`: similarity score (float).  
    - Optional: `chunk_id`, `hash`.  
  - [x] Align this schema with MCP/server needs and keep it stable for future tools.  

- [ ] **Task 4:** Conversation log storage of citations (nice‑to‑have from epic notes)  
  - [ ] Evaluate whether to persist citation metadata alongside conversations in PostgreSQL (e.g., in `messages.metadata` or a dedicated table).  
  - [ ] If implemented, add a compact representation of `sources[]` to the message record for later review.  

- [x] **Task 5:** Tests (AC: all)  
  - [x] Unit tests for citation formatting (human output) given a mocked `SearchResult[]`.  
  - [x] Unit tests for JSON envelope shape and field presence.  
  - [x] Unit test for the “no sources” edge case (covered by existing “no results” path).  
  - [x] Integration test: run a real `jarvis query` against test memory and assert that citations correspond to actual payload metadata.

## Dev Notes

- The RAG + hybrid retrieval pipeline from Stories 3.1–3.3 already returns `SearchResult` objects with `text`, `score`, `source_file`, `section`, `domain`, and `metadata`. This story focuses on **presentation and explicit provenance**, not the retrieval algorithm.  
- Human‑readable output should remain compact and terminal‑friendly; avoid over‑rendering inside the main answer – a dedicated “Sources” block with numbered entries is often clearer than inline `[1]` markers everywhere.  
- JSON envelope is the contract for MCP / external tooling; keep it stable and documented. If additional fields are needed later (e.g., line ranges), append instead of renaming existing keys.  
- Citation logic must never fabricate sources: only use what comes back from `SearchResult[]`.

### Learnings from Previous Stories

**From Story 3.1 – Query Command & Response Envelope**

- `jarvis query` already builds a JSON envelope (`--json-output`) and returns a list of `SearchResult`s. The new `sources[]` structure should reuse these objects and simply make provenance explicit.  
- Human‑readable output already prints a basic sources block; this story can tighten the format (filenames, domains, scores).  

**From Story 3.2 – Hybrid Retrieval Toggle**

- Hybrid retrieval produces a merged set of `SearchResult`s with scores that combine semantic and keyword signals. These scores are the natural candidates for the `score`/confidence field in each citation.  
- Deduplication logic by `chunk_id`/`message_id` + `domain` is already in place; citations should reflect the deduplicated set.  

**From Story 3.3 – Query Expansion & Multi‑Query Fusion (in progress)**

- Expanded/multi‑query retrieval will produce fused results. Citations must still map 1:1 to concrete chunks; fusion should not elide provenance.  
- Telemetry for expansions (original query + expansions + per‑expansion counts) can be complemented by citation metadata for deeper analysis in future stories.

### Project Structure Notes

- CLI: `src/jarvis/cli/query.py` – central place for human and JSON outputs.  
- Retrieval: `src/jarvis/memory/search.py` – continues to supply `SearchResult` objects.  
- Schemas (if needed): `src/jarvis/api/schemas.py` – potential addition of a `Citation` schema used by API + MCP.  
- Tests:  
  - `tests/unit/cli/test_query.py` – extend with citation formatting tests.  
  - `tests/integration/cli/test_query_integration.py` – extend to assert `sources[]` correctness in JSON output and human output examples.
