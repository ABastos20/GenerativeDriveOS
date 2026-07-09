# Story 2.3: Qdrant Collection Initialization

**Status:** done

## Story

As a vector engineer,
I want a managed Qdrant collection seeded with embeddings,
So that semantic search is consistent across restarts.

## Acceptance Criteria

1. **Given** embeddings exist in PostgreSQL staging tables,
   **When** the provisioning command runs,
   **Then** Qdrant collections with 384-d vectors and metadata payloads are created

2. **Given** the Qdrant service is running,
   **When** health checks are performed,
   **Then** they confirm replication parameters per architecture

3. **Given** a collection is initialized,
   **When** the system restarts,
   **Then** the collection persists with all data intact

4. **Given** the initialization script runs,
   **When** a collection already exists,
   **Then** the script handles idempotently without errors

## Tasks / Subtasks

- [x] **Task 1**: Implement Qdrant client wrapper (AC: #1)
  - [x] Create `src/jarvis/database/qdrant.py` with connection management
  - [x] Implement collection creation with 384-d vector config (Cosine distance)
  - [x] Add error handling for connection failures
  - [x] Add type hints and docstrings

- [x] **Task 2**: Create collection initialization script (AC: #1, #4)
  - [x] Create initialization script (e.g., `scripts/init_qdrant.py` or CLI command)
  - [x] Implement idempotent collection creation (check if exists first)
  - [x] Configure collection parameters per architecture (HNSW, distance metric)
  - [x] Add logging with structlog for initialization events

- [x] **Task 3**: Implement health check validation (AC: #2)
  - [x] Add Qdrant health check to `src/jarvis/cli/commands/doctor.py`
  - [x] Verify collection existence and configuration
  - [x] Check vector dimensions and distance metric
  - [x] Validate connection to Qdrant service

- [x] **Task 4**: Add persistence verification (AC: #3)
  - [x] Verify volume mounting in docker-compose.yml (qdrant-data volume)
  - [x] Test restart scenario (insert points → restart → verify points exist)
  - [x] Document persistence configuration in comments

- [x] **Task 5**: Write unit and integration tests (AC: all)
  - [x] Unit tests for Qdrant wrapper functions
  - [x] Integration test: Initialize collection and verify structure
  - [x] Integration test: Idempotency (run init twice, no errors)
  - [x] Integration test: Persistence (restart Qdrant, verify data)

## Dev Notes

### Architecture Alignment

**From architecture.md:**
- **Vector DB**: Qdrant v1.15.5
- **Python Client**: qdrant-client 1.15.1+
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Distance Metric**: Cosine
- **HNSW Config**: m=16, ef_construct=200
- **Storage**: Volume-backed persistence (`qdrant-data:/qdrant/storage`)

**Collection Structure (from architecture.md #L990-1017):**
```python
{
    "collection_name": "knowledge",
    "vectors_config": {
        "size": 384,  # all-MiniLM-L6-v2
        "distance": "Cosine"
    },
    "hnsw_config": {
        "m": 16,
        "ef_construct": 200,
        "full_scan_threshold": 10000
    }
}
```

**Point Payload Structure:**
```python
{
    "id": "uuid",
    "vector": [0.123, ...],  # 384 dimensions
    "payload": {
        "text": "chunk content",
        "source_file": "docs/file.md",
        "section": "Section Header",
        "domain": "databases",
        "ingested_at": "2025-11-21T..."
    }
}
```

### Learnings from Previous Story (2-2)

**From Story 2-2 (Status: done)**

- **Database Integration Pattern**: Use direct session factory (`get_session_factory()`) for dependency injection - established in `src/jarvis/api/conversations.py`
- **Environment Variables**: Docker Compose now loads `.env` via `env_file` directive - added in Story 2-2
- **Dependencies Management**: Already have pattern for adding deps to pyproject.toml (fastapi, uvicorn added in 2-2)
- **Testing Infrastructure**: Integration test patterns with Docker Compose established in `tests/integration/api/`
- **Docker Services**: PostgreSQL, Qdrant, Redis, and jarvis-app containers already running and configured

**Reusable Patterns:**
- Error handling with try/except and structured logging (structlog)
- Health check pattern in CLI (can extend `jarvis doctor` command)
- Docker volume persistence (postgres-data, qdrant-data volumes exist)

[Source: stories/2-2-conversation-api-persistence.md#Dev-Agent-Record]

### Technical Implementation Guidelines

**Qdrant Client Initialization:**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, HnswConfigDiff

client = QdrantClient(
    host=config.qdrant_host,  # from pydantic-settings
    port=config.qdrant_port   # 6333 default
)
```

**Collection Creation (Idempotent):**
```python
def init_collection(client: QdrantClient, collection_name: str = "knowledge"):
    """Initialize Qdrant collection idempotently"""
    if client.collection_exists(collection_name):
        logger.info(f"Collection '{collection_name}' already exists")
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        ),
        hnsw_config=HnswConfigDiff(
            m=16,
            ef_construct=200,
            full_scan_threshold=10000
        )
    )
    logger.info(f"Collection '{collection_name}' created successfully")
```

**Health Check Integration:**
- Extend existing `jarvis doctor` command in `src/jarvis/cli/commands/doctor.py`
- Check Qdrant service availability
- Verify collection exists and has correct configuration
- Display collection stats (vectors count, config parameters)

### Project Structure Notes

**New Files to Create:**
- `src/jarvis/database/qdrant.py` - Qdrant client wrapper and operations
- `scripts/init_qdrant.py` - Standalone initialization script (or integrate into CLI)
- `tests/unit/database/test_qdrant.py` - Unit tests for Qdrant wrapper
- `tests/integration/database/test_qdrant_integration.py` - Integration tests

**Files to Modify:**
- `src/jarvis/cli/commands/doctor.py` - Add Qdrant health check
- `pyproject.toml` - Already has qdrant-client dependency (verify version)

**Docker Services:**
- Qdrant service already configured in `docker/docker-compose.yml`
- Volume `qdrant-data` already defined for persistence
- Port 6333 exposed for API access
- Config file: `docker/qdrant/config.yaml`

### Testing Strategy

**Unit Tests (Fast, No Docker):**
- Mock Qdrant client responses
- Test collection creation logic
- Test error handling paths

**Integration Tests (Requires Docker):**
1. **Collection Initialization**: Verify collection created with correct params
2. **Idempotency**: Run init twice, no errors, collection unchanged
3. **Persistence**: Insert test points → restart Qdrant container → verify points exist
4. **Health Check**: Validate `jarvis doctor` detects Qdrant status

### References

- [Source: docs/epics.md#L160-173] - Story 2.3 definition
- [Source: docs/architecture.md#L235-241] - Qdrant technology details
- [Source: docs/architecture.md#L988-1023] - Qdrant schema and configuration
- [Source: docker/docker-compose.yml#L67-77] - Qdrant service configuration

## Dev Agent Record

### Context Reference

- [2-3-qdrant-collection-initialization.context.xml](2-3-qdrant-collection-initialization.context.xml) - Generated 2025-11-21

### Agent Model Used

_To be filled during implementation_

### Debug Log

- Added `scripts/init_qdrant.py` for idempotent collection provisioning with structlog output and timeout control.
- Strengthened doctor Qdrant collection check to validate HNSW `full_scan_threshold` alongside size/distance/m/ef parameters.
- Local environment lacks pip/venv, so tests executed via `uv run` with pinned pytest 8.3.4 and dependencies instead of system pytest 7.4.4.
- Integration suite executed with `QDRANT_HOST=localhost QDRANT_PORT=6333 uv run --with pytest==8.3.4 --with qdrant-client==1.15.1 --with structlog==24.1.0 pytest -s -q -o addopts='' tests/integration/database/test_qdrant_integration.py` (7 passing, 1 warning for custom mark).
- Ran targeted unit tests via `uv run --with pytest==8.3.4 --with qdrant-client==1.15.1 --with structlog==24.1.0 pytest -s -q -o addopts='' tests/unit/database/test_qdrant.py tests/cli/test_doctor_checks.py` (all passing); integration suite skipped because Qdrant service was not running (`qdrant_running` fixture skip).

### Completion Notes List

- AC #1/#4: Provisioning command provided via `scripts/init_qdrant.py`; idempotent creation and logging implemented per architecture defaults (384-d vectors, Cosine, HNSW m=16/ef=200/full_scan_threshold=10000).
- AC #2: Doctor check now validates all Qdrant collection parameters (vector size, distance metric, HNSW m/ef/full_scan_threshold), surfacing structured results.
- AC #3: Persistence reinforced via docker-compose volume note and restart scenario covered in `tests/integration/database/test_qdrant_integration.py` (passes when pointing to running local Qdrant).
- Tests: Unit + integration suites executed via `uv run --with pytest==8.3.4 --with qdrant-client==1.15.1 --with structlog==24.1.0`; integration ran with `QDRANT_HOST=localhost QDRANT_PORT=6333` and passed.

### File List

- scripts/init_qdrant.py
- src/jarvis/cli/doctor_checks.py
- tests/cli/test_doctor_checks.py
- docker/docker-compose.yml
- docs/sprints/stories/2-3-qdrant-collection-initialization.md

### Change Log

- Added Qdrant init script and expanded health checks, including HNSW full_scan_threshold validation and persistence note in Docker Compose.
