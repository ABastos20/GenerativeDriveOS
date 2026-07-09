# Story 2.2: Document Ingestion Pipeline

Status: done

## Story

As a data librarian,  
I want a pipeline that converts uploads (Markdown, PDF, HTML) into normalized Markdown chunks and embeddings,  
So that the memory store is consistent and ready for semantic search.

## Acceptance Criteria

1. **Given** the user runs `jarvis memory add path/to/file.pdf`, **When** ingestion completes, **Then** the file is converted via pandoc, chunked, embedded, and stored with metadata in Qdrant/PostgreSQL.
2. **Given** ingestion jobs run, **When** chunking occurs, **Then** a hybrid strategy (semantic + fixed window) is used and metadata includes source path, section, domain, and timestamps.
3. **Given** ingestion succeeds or fails, **When** logs are inspected, **Then** events show success/failure with file path, chunk counts, and error details.
4. **Given** supported formats (Markdown, PDF, HTML), **When** a file of each type is ingested, **Then** normalized Markdown is produced and embedded with 384-d vectors (all-MiniLM-L6-v2).

## Tasks / Subtasks

- [x] **Task 1:** Add CLI entrypoint for ingestion (AC: #1, #4)  
  - [x] Implement `jarvis memory add <path>` command with input validation and format detection  
  - [x] Integrate pandoc conversion for PDF/HTML to Markdown; no-op for Markdown inputs  
  - [x] Ensure metadata (source path, section/file name, detected domain, ingested_at) is captured

- [x] **Task 2:** Chunking and embedding pipeline (AC: #1, #2, #4)  
  - [x] Implement hybrid chunker (semantic + fixed window fallback) respecting model token limits  
  - [x] Generate embeddings with all-MiniLM-L6-v2 (384-d) and attach to chunk payloads  
  - [x] Normalize text to Markdown and strip unsafe characters before embedding

- [x] **Task 3:** Persistence to stores (AC: #1, #2)  
  - [x] Upsert chunk payload + metadata into PostgreSQL staging tables (if defined)  
  - [x] Write vectors and payload to Qdrant collection `knowledge` with Cosine distance  
  - [x] Ensure idempotent writes (skip/overwrite via content hash)

- [x] **Task 4:** Observability and error handling (AC: #3)  
  - [x] Add structlog events for start/success/failure with counts and durations  
  - [x] Surface non-zero exit codes for CLI failures; include actionable error messages

- [x] **Task 5:** Tests (AC: all)  
  - [x] Unit tests for chunking logic, format detection, and metadata shaping  
  - [x] Integration test: ingest sample PDF/MD/HTML, verify chunks + embeddings persisted  
  - [x] Integration test: idempotent re-run and failure path (bad file)

## Dev Notes

- Align with architecture defaults: all-MiniLM-L6-v2 embeddings (384 dimensions), Cosine distance, Qdrant collection `knowledge`, HNSW m=16/ef_construct=200/full_scan_threshold=10000.  
- Use existing structlog pattern (see CLI/doctor) for structured events.  
- Respect existing test layout under `tests/unit` and `tests/integration`; add fixtures for sample documents.  
- Avoid logging sensitive data; only file paths and counts.  
- Consider content hashing for idempotency and to skip unchanged files.

### Project Structure Notes

- CLI lives under `src/jarvis/cli`; pipeline helpers may go under `src/jarvis`.  
- Qdrant client wrapper available at `src/jarvis/database/qdrant.py`; reuse instead of re-instantiating clients.  
- Environment configuration via `.env`/docker-compose supports QDRANT_HOST/PORT and embedding model requirements.

### References

- [Source: docs/epics.md#Epic-2 -> Story 2.2] Document Ingestion Pipeline (requirements, formats, logging).  
- [Source: docs/architecture.md#Qdrant Configuration & Schema] Vector DB setup (size=384, Cosine, HNSW).  
- [Source: docs/prd.md#FR4.2 Document Ingestion] Functional needs for ingest and normalization.  
- [Source: docker/docker-compose.yml#qdrant service] Service availability and volume persistence.  
- [Source: docs/test-design-system.md] Testing standards and fixtures guidance.

## Dev Agent Record

### Context Reference

- [2-2-document-ingestion-pipeline.context.xml](2-2-document-ingestion-pipeline.context.xml)

### Agent Model Used

Local execution (no hosted model recorded)

### Debug Log References

- Implemented ingestion pipeline (`src/jarvis/memory/ingest.py`) with format detection, pypandoc Markdown conversion, chunking, embedding hook, and Qdrant upsert payloads.
- Added CLI entrypoint (`src/jarvis/cli/main.py`, `src/jarvis/cli/memory.py`) exposing `jarvis memory add`.
- Added unit/integration tests for ingestion flow (mocks + live Qdrant with stub embeddings).
- Tests executed via `uv run --with pytest==8.3.4 --with pytest-cov --with qdrant-client==1.15.1 --with structlog==24.1.0 pytest tests/unit/memory/test_ingest.py tests/integration/memory/test_ingest_integration.py`; unit passed, integration skipped (Qdrant DNS failure).

### Completion Notes List

- Pipeline supports Markdown/PDF/HTML (via pypandoc) normalization, hybrid chunking, embedding hook (pluggable, defaults to all-MiniLM-L6-v2), and Qdrant upsert with metadata/idempotent hashes.
- CLI command `jarvis memory add <path>` wires to ingestion with collection override; structlog emits ingest events.
- Integration harness uses stub embeddings and skips if Qdrant unavailable; vectors target 384-d Cosine collection per architecture.
- Tests run locally (unit + integration) with:
  `QDRANT_HOST=localhost QDRANT_PORT=6333 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS='' python -m pytest -o addopts='' tests/unit/memory/test_ingest.py tests/integration/memory/test_ingest_integration.py` (7 passed ~5s). Direct `pytest` without env overrides can skip integration if DNS/env differs.

### File List

- src/jarvis/memory/ingest.py
- src/jarvis/memory/__init__.py
- src/jarvis/cli/main.py
- src/jarvis/cli/memory.py
- tests/unit/memory/test_ingest.py
- tests/integration/memory/test_ingest_integration.py
- docs/sprints/stories/2-2-document-ingestion-pipeline.context.xml
- docs/sprints/stories/2-2-document-ingestion-pipeline.md

### Change Log

- Added ingestion pipeline, CLI command `jarvis memory add`, and unit/integration tests with Qdrant stubs; tests not executed locally due to pytest addopts/coverage plugin conflicts.
- Ran tests locally with explicit envs and plugin autoload disabled; unit + integration passed (7 tests).
