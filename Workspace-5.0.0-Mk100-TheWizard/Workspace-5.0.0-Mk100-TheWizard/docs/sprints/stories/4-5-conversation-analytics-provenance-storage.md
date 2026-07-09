# Story 4.5: Conversation Analytics & Provenance Storage

Status: done

## Story

As a knowledge engineer,  
I want citation metadata persisted alongside conversations,  
So that I can analyze which sources drive answers and build higher-level analytics.

## Acceptance Criteria

1. **Given** `jarvis query` is invoked and returns cited answers, **When** the assistant response is persisted to PostgreSQL, **Then** the associated message record also stores a compact representation of the `sources[]` array (filenames, sections, domains, scores, chunk IDs and hashes).
2. **Given** citation metadata is stored, **When** I run an analytics query (CLI/API), **Then** I can answer questions like “which files are used most often?” or “which domains are most frequently cited?” for a given period.
3. **Given** the JSON envelope schema evolves, **When** provenance is stored, **Then** the database representation remains compatible with the existing `sources[]` shape (additive changes only, no breaking renames).
4. **Given** migrations are applied, **When** the app starts, **Then** existing messages without citation metadata remain valid and queries handle `NULL`/empty provenance gracefully.

## Tasks / Subtasks

- [x] **Task 1:** Schema design & migration (AC: #1, #4)  
  - [x] Add a JSONB column (`messages.citation_provenance`) to persist `sources[]`-like structures.  
  - [x] Create an Alembic migration that adds the new column without breaking existing data.  
  - [x] Document the schema in `docs/architecture.md` and `docs/full-documentation.md`.  

- [x] **Task 2:** Write path integration (AC: #1)  
  - [x] Extend the path where assistant messages are persisted (API + MCP server flows) to also write citation metadata for responses that include sources.  
  - [x] Use the existing JSON envelope `sources[]` structure as the canonical shape when storing provenance.  
  - [x] Ensure that messages without sources either store `NULL`/empty provenance or skip the write cleanly.  

- [x] **Task 3:** Read path & analytics CLI/API (AC: #2, #3)  
  - [x] Add a minimal analytics CLI endpoint (`jarvis analytics citations --days 30`) that surfaces basic stats: top files, top domains, citation counts.  
  - [x] Ensure the read path handles older messages without provenance (falling back to “no data”).  
  - [x] Keep the analytics output JSON-friendly for future dashboards (Epic 9).  

- [x] **Task 4:** Tests (AC: all)  
  - [x] Unit tests for aggregation/serialization logic (storing and loading citation provenance).  
  - [x] Integration test that logs a message via `/mcp/log_message` with provenance and verifies it through the conversation API.  
  - [x] Tests for analytics aggregation helper to ensure correct counts and resilience to mixed provenance shapes.  

## Dev Notes

- Reuse the existing `sources[]` JSON envelope shape from the query CLI as the single source of truth for provenance fields (`id`, `source_file`, `section`, `domain`, `relevance_score`/`score`, `chunk_id`, `hash`).  
- Prefer a single JSONB column on `messages` for simplicity; if needed later, a normalized table can be introduced in a follow-up story.  
- Be conservative with schema changes: keep this additive and avoid breaking existing queries or tools.  
- This story lays the foundation for future analytics and dashboards in later epics (Epic 5 cost analytics, Epic 9 dashboards).
