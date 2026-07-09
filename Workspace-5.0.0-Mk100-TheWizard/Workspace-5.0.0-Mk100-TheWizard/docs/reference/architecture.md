# JARVIS System - Architecture Document

**Author:** Ariel Bastos
**Date:** 2025-12-09
**Version:** 4.1.0 (Living Document - Auto-Updated by JARVIS)

**Previous Version:** 2.1.0 (2025-11-17)

**Version History:**
- **v4.1.0** (2025-12-09): Sovereign Identity Layer (Epic 11) - In Progress
- **v4.0.0** (2025-12-09): Governance Architecture & Machine Democracy (Epic 9)
- **v2.4.0**: ARCHES Controller & Cognitive Observability (Epic 4-5)
- **v2.3.0**: Autonomous Knowledge Graph (Epic 8-7)
- **v2.2.0**: Council of Ricks Multi-Agent (Epic 4)
- **v2.1.0** (2025-11-17): Intelligent RAG Query Engine (Epic 3)

---

## Executive Summary

**JARVIS is not a chatbot. It's a Governed Cognitive Institution.**

JARVIS has evolved from a self-modifying AI system into a **Cognitive Operating System** with democratic governance, constitutional constraints, and full cognitive introspection. The architecture is designed as a governed institution where multiple humans oversee a multi-agent cognitive system with complete transparency and programmatic enforcement of core values.

**Core Architectural Principles (v4.x):**

1. **ARCHES Controller (v2.4)**: Centralized cognitive orchestration with session state management, replacing distributed pattern chaos with coherent controller architecture

2. **Governance-First Design (v4.0)**: Multi-human oversight with trust-weighted voting, constitutional constraints, and democratic decision-making for all system changes

3. **Cognitive Observability (v2.4)**: Full trace replay capability (`jarvis trace replay`) with agent memory attribution - unprecedented transparency into every decision

4. **Constitutional AI (v4.0)**: Core values (safety, privacy, truth, sovereignty) enforced programmatically with red lines and violation detection

5. **Sovereign Identity (v4.1)**: Keycloak OAuth2/OIDC integration with user context propagation across all API requests (in-progress)

6. **Multi-Agent Reasoning (v2.2)**: Council of Ricks with weighted chaos voting, parallel invocation (91% faster), self-aware gap detection, autonomous research

7. **Resilient Retrieval (v2.1)**: Hybrid search (semantic + keyword BM25), MMR diversity filter, freshness enforcement (`is_latest`), query expansion with RRF fusion

8. **Self-Hosting Development**: JARVIS runs in dev == prod environment, enabling hot-reload plugins and autonomous evolution (Epic 8-8 dormant during boundary refinement)

9. **Autonomous Knowledge Graph (v2.3)**: Self-maintaining entity/relationship extraction with graph-enhanced retrieval

10. **Cost-First Intelligence**: LLM routing optimizes for free tiers (Gemini Flash, Llama 3.1) with full cost tracking

**Paradigm Shift:** JARVIS evolved from "smart RAG with personas" to **Cognitive OS with brain (ARCHES), spine (memory), black box (traces), cockpit (governance dashboard), and parliament (multi-human governance)**.

**Technology Stack:**
- **Language**: Python 3.13 (LTS support until 2029)
- **Vector DB**: Qdrant v1.15.5 (purpose-built, Docker-native)
- **Primary DB**: PostgreSQL 18.1 (relational data, conversations)
- **Time-Series**: TimescaleDB (future - metrics, knowledge levels)
- **Document Store**: MongoDB (future - unstructured data)
- **Cache**: Redis (session management, caching)
- **CLI Framework**: Typer (type-hint driven, auto-generated help)
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (local, fast, 384-dim)
- **Document Conversion**: pandoc (universal MD converter)
- **Container Orchestration**: Docker Compose (single-user deployment)

---

## Decision Summary Table

| Category | Decision | Version | Rationale | Affects FRs |
|----------|----------|---------|-----------|-------------|
| **Vector Database** | Qdrant | 1.15.5 | Purpose-built performance, context sharding support, Docker-native | FR1 (RAG), FR4 (Memory) |
| **Python Runtime** | Python | 3.13 | LTS support until 2029, modern type hints | All |
| **PostgreSQL** | PostgreSQL | 18.1 | Latest stable, proven reliability | FR3 (Costs), FR4 (Memory), FR2 (Agents) |
| **Redis Cache** | Redis | Latest | Standard caching layer | FR5 (Docker), FR4 (Memory) |
| **CLI Framework** | Typer | Latest | Type-safe, auto-documentation, modern | FR6 (CLI) |
| **Embedding Model** | sentence-transformers | all-MiniLM-L6-v2 | Local, fast (80MB), 384-dim, good balance | FR1 (RAG), FR4 (Memory) |
| **Document Converter** | pandoc + fallbacks | Latest | Universal format support → MD | FR4 (Memory), FR7 (Web Scraping) |
| **Error Handling** | Custom Exception Classes | N/A | Structured exceptions, consistent error hierarchy | All |
| **Logging** | structlog | Latest | Structured JSON logging for analysis | All |
| **DateTime** | UTC+0 (Lisbon) | Python stdlib | Always UTC internally, convert at display endpoints | All |
| **Configuration** | pydantic-settings + YAML | Latest | Type-safe config validation, YAML for structure, .env for secrets | All |
| **Testing** | pytest | Latest | Standard Python testing framework | All |
| **Code Formatting** | ruff + black | Latest | Fast linting + consistent formatting | All (dev quality) |
| **Qdrant Client** | qdrant-client | 1.15.1+ | Official Python SDK for Qdrant | FR1, FR4 |
| **Docker Compose** | Docker Compose | v2 | Multi-container orchestration | FR5 (Docker) |
| **MCP SDK** | @modelcontextprotocol/sdk | Latest | Official MCP implementation | FR6 (CLI), FR8 (Bootstrap) |
| **Web Scraping** | Playwright + requests | Latest | Hybrid: simple requests + browser automation when needed | FR7 (future) |
| **LLM Router** | Custom (litellm optional) | N/A | Cost-first routing with provider API tracking | FR3 (Cost Routing) |
| **Hot-Reload** | importlib.reload() | Python stdlib | Dynamic module loading without restart | FR8 (Self-Modification) |
| **Arches Pattern** | State/Controller Split | 2.1.0 | Decouples execution logic from persistent state; enables safe retry/rollback | All (Stability) |
| **Retrieval v2** | Modular Pipeline | 2.1.0 | Separates Filtering, Fusion, and Execution into distinct phases | FR1 (Retrieval) |

---

## Project Structure

```
jarvis/
├── .jarvis/                          # JARVIS runtime metadata
├── docker/                           # Docker configuration
├── src/jarvis/                       # Source code (v2.1.0 Arches)
│   ├── __init__.py
│   ├── __main__.py                   # CLI entry point
│   │
│   ├── arches/                       # ARCHES State/Controller Core
│   │   ├── __init__.py
│   │   ├── controller.py             # Base Controller logic
│   │   ├── state.py                  # State definitions (Pydantic)
│   │   ├── trace.py                  # Execution tracing/logging
│   │   ├── planning_controller.py    # Plan generation/validation
│   │   ├── execution_controller.py   # Step execution
│   │   └── memory_controller.py      # Memory state management
│   │
│   ├── controllers/                  # High-level Orchestration
│   │   ├── chat_controller.py        # Main Chat/RAG loop
│   │   └── chat_phases.py            # Phase definitions (Validation -> Research -> Consensus)
│   │
│   ├── memory/                       # Knowledge Engine
│   │   ├── retrieval/                # Retrieval v2
│   │   │   ├── core.py               # Search execution
│   │   │   ├── filters.py            # Dynamic filter generation
│   │   │   └── fusion.py             # RRF & Expansion fusion
│   │   ├── ingest.py                 # Document ingestion
│   │   ├── research_planner.py       # Autonomous research planning
│   │   └── critical_integrator.py    # Conflict resolution & merging
│   │
│   ├── agents/                       # Council of Ricks (Epic 4)
│   │   ├── orchestrator.py           # Multi-agent coordination
│   │   ├── personas.py               # Persona logic
│   │   ├── consensus.py              # Weighted chaos voting
│   │   └── parallel_invocation.py    # Async agent execution
│   │
│   ├── cli/                          # CLI Interface
│   │   ├── query.py                  # Thin router (Entry point)
│   │   ├── query_router.py           # Command routing
│   │   ├── query_phases.py           # CLI execution phases
│   │   └── commands/                 # Subcommands (memory, agents, doctor)
│   │
│   ├── mcp/                          # MCP Implementation
│   ├── database/                     # DB Adapters (Qdrant/Postgres/Redis)
│   └── utils/                        # Shared Utilities
│
├── tests/                            # Test Suite
│   ├── unit/                         # Fast unit tests
│   └── integration/                  # Docker-based integration tests
├── docs/                             # Documentation
└── config/                           # Configuration templates
```

---

## FR Category to Architecture Mapping

| FR Category | Architecture Components | Primary Location |
|-------------|-------------------------|------------------|
| **FR1: RAG Query System** | ChatController, Retrieval v2, Vector Store | `src/jarvis/controllers/chat_controller.py`, `src/jarvis/memory/retrieval/` |
| **FR2: Council of Ricks** | Orchestrator, Consensus, Personas | `src/jarvis/agents/` |
| **FR3: Cost-First LLM Routing** | LLM router, Provider API tracking, Usage DB | `src/jarvis/llm/` |
| **FR4: Persistent Memory** | Memory Controller, Ingest, Database Adapters | `src/jarvis/arches/memory_controller.py`, `src/jarvis/memory/ingest.py` |
| **FR5: Docker Containerization** | Docker Compose, Dockerfiles, Volume mounts | `docker/` |
| **FR6: CLI Integration** | Typer CLI, Query Router | `src/jarvis/cli/query_router.py` |
| **FR7: Web Scraping (future)** | Web scrapers, HTML→MD converter | `src/jarvis/modules/` (plugin to be developed) |
| **FR8: Bootstrap Evolution** | BMAD invoker, Hot-reload, Capability registry, Dev workflow | `src/jarvis/dev/` |
| **FR9: Web Interface (future)** | FastAPI server (plugin) | `src/jarvis/api/` |
| **FR10: 60-Year Memory (future)** | Time-decay compression, TimescaleDB, MongoDB | `src/jarvis/modules/` (to be developed) |

---

## Technology Stack Details

### Core Technologies

**Python 3.13**
- LTS support until 2029
- Modern type hints for Typer/pydantic integration
- Performance improvements in 3.13
- Install: `pyenv install 3.13` or use official Python.org installer

**Qdrant v1.15.5 (Vector Database)**
- Purpose-built vector search engine (Rust-based)
- Native context sharding for domain-specific knowledge
- Docker deployment: `docker pull qdrant/qdrant:v1.15.5`
- Python client: `qdrant-client==1.15.1+`
- Configuration: `.docker/qdrant/config.yaml`

**PostgreSQL 18.1 (Primary Database)**
- Conversations storage
- LLM provider usage tracking
- Agent persona configurations
- User preferences
- Cost summaries
- Citation provenance for answers (JSONB per message, used for analytics)
- Docker: Official `postgres:18.1` image

**Redis (Cache Layer)**
- Session management
- Temporary query caching
- Rate limiting
- Docker: Official `redis:latest` image

**sentence-transformers (Embeddings)**
- Model: `all-MiniLM-L6-v2`
- Size: 80MB (local, no API costs)
- Dimensions: 384
- Fast inference (~50ms per query)
- Upgrade path: `all-mpnet-base-v2` (768-dim) or OpenAI API (if budget allows)

**pandoc (Universal Document Converter)**
- Converts 40+ formats → Markdown
- External binary: Install via system package manager
- Python wrapper: `pypandoc`
- Fallback: Per-format libraries (pypdf, python-docx, html2text)

### Integration Points

**1. LLM Provider APIs**
- OpenRouter (free tier + paid)
- Together AI (free tier + paid)
- OpenAI (paid, future upgrade for embeddings)
- Perplexity, Gemini, Copilot (free tiers)
- Usage tracking via provider-specific APIs

**2. MCP Protocol**
- Server: JARVIS exposes MCP endpoints
- Clients: Claude Desktop, other MCP-compatible tools
- Tools: `jarvis/query`, `jarvis/memory-search`, `jarvis/add-memory`
- Resources: `jarvis/knowledge-base`

**3. BMAD CLI Integration**
- JARVIS invokes BMAD agents via subprocess
- Commands: `bmad-dev`, `bmad-architect`, `bmad-pm`, etc.
- Context passing: JSON stdin/stdout
- Output validation before code application

**4. Git Integration**
- JARVIS commits its own code changes
- Automated commit messages for self-modifications
- Testing before commit (rollback on failure)

**5. Docker Workspace Mounting**
- JARVIS container mounts `./` as `/workspace`
- Read/write access to own source code
- Respects `.gitignore` for document ingestion

---

## Novel Architectural Patterns

### Pattern 1: Self-Modifying Development Environment

**Purpose**: Enable JARVIS to manage its own development without external orchestration

**Components:**

1. **Capability Registry** (`~/.jarvis/capabilities.yaml`)
   ```yaml
   available:
     - rag_query
     - memory_add
     - cost_tracking

   in_development:
     - image_analysis:
         status: testing
         started: 2025-11-17T14:30:00Z
         estimated_completion: null  # No time estimates!

   backlog:
     - voice_input
     - video_analysis
   ```

2. **Development Orchestrator** (`src/jarvis/dev/dev_workflow.py`)
   - Detects capability gaps via regex/keyword matching
   - Prompts user: [1] Build now [2] Background [3] Backlog [4] Alternative
   - Invokes BMAD agents via subprocess
   - Monitors development progress
   - Hot-reloads new module on completion

3. **Hot-Reload System** (`src/jarvis/dev/hot_reload.py`)
   ```python
   import importlib
   import sys

   def reload_module(module_name: str):
       """Dynamically reload a module without restart"""
       if module_name in sys.modules:
           importlib.reload(sys.modules[module_name])
       else:
           __import__(module_name)
   ```

4. **Status Updates** (Filesystem-based, simple)
   - `~/.jarvis/status.md` updated during development
   - CLI output: `[JARVIS DEV] Image analysis: Installing deps... ✓`
   - User checks: `jarvis status`

**Data Flow:**
```
User: "Analyze this image"
  ↓
JARVIS: Capability check → image_analysis NOT in registry
  ↓
JARVIS: "I don't have image analysis. Options:
         [1] Build now (~10 min, I'll work while we chat)
         [2] Background (I'll notify when ready)
         [3] Backlog (build later)
         [4] Alternative (upload to external service?)"
  ↓
User: [1]
  ↓
JARVIS DEV Workflow:
  1. Update capabilities.yaml (status: in_development)
  2. Invoke: subprocess.run(["bmad-dev", "implement", "image-analysis"])
  3. Monitor BMAD output, update status.md
  4. On completion: Run tests
  5. If tests pass: importlib.reload('jarvis.modules.image_analysis')
  6. Update capabilities.yaml (status: available)
  7. Notify user: "Image analysis ready! Let's try again."
  ↓
User: "Analyze this image" → JARVIS uses new capability
```

**Implementation Guide for AI Agents:**
- Always check `~/.jarvis/capabilities.yaml` before adding features
- Use `importlib.reload()` for hot-reload (not `exec()` - unsafe)
- Write comprehensive docstrings → auto-generate MD via `src/jarvis/dev/auto_doc.py`
- Update capability registry atomically using file locks (`src/jarvis/utils/file_lock.py`)
- Test modules in isolation before hot-reload

**Affects FR Categories**: FR8 (Bootstrap Evolution), All FRs (plugins)

---

### Pattern 2: Markdown-First Knowledge Pipeline

**Purpose**: Unified document processing for all knowledge sources (conversations, uploads, web scraping)

**Components:**

1. **Universal Converter** (`src/jarvis/converters/pandoc.py`)
   ```python
   import pypandoc

   def convert_to_markdown(file_path: str, source_format: str = None) -> str:
       """Convert any document to markdown using pandoc"""
       return pypandoc.convert_file(
           file_path,
           'md',
           format=source_format,  # Auto-detect if None
           extra_args=['--wrap=none', '--atx-headers']
       )
   ```

2. **Markdown Storage** (`~/.jarvis/knowledge/`)
   - All docs saved as `.md` with YAML frontmatter
   ```markdown
   ---
   source: uploaded_file
   original_path: /path/to/document.pdf
   original_format: pdf
   ingested_at: 2025-11-17T14:30:00Z
   domain: vector_databases
   ---

   # Document Title

   Content here...
   ```

3. **Hybrid Chunking** (`src/jarvis/chunking/hybrid.py`)
   - Respects markdown structure (headers = semantic boundaries)
   - Falls back to fixed-size if no headers
   - Preserves code blocks and tables intact
   - Chunks: 200-500 tokens (configurable)

4. **Embedding & Indexing**
   ```python
   from sentence_transformers import SentenceTransformer

   model = SentenceTransformer('all-MiniLM-L6-v2')
   chunks = chunk_markdown(md_content)
   embeddings = model.encode(chunks)

   # Store in Qdrant with metadata
   qdrant.upsert(
       collection_name="knowledge",
       points=[
           {
               "id": uuid4(),
               "vector": embedding,
               "payload": {
                   "text": chunk,
                   "source": source_file,
                   "section": section_header,
                   "domain": domain
               }
           }
           for chunk, embedding in zip(chunks, embeddings)
       ]
   )
   ```

**Data Flow:**
```
User Upload (PDF/DOCX/HTML) OR Web Scrape (HTML)
  ↓
Detect Format → Convert to Markdown (pandoc)
  ↓
Add YAML Frontmatter (metadata)
  ↓
Save to ~/.jarvis/knowledge/{domain}/{filename}.md
  ↓
Chunk by Markdown Structure (headers, code blocks)
  ↓
Generate Embeddings (all-MiniLM-L6-v2)
  ↓
Store in Qdrant with Metadata
  ↓
Indexed for RAG Retrieval
```

**Implementation Guide:**
- Install pandoc system-wide: `brew install pandoc` / `apt install pandoc` / `choco install pandoc`
- Strip non-essential HTML (navigation, ads, footers) before conversion
- Preserve formatting: code blocks (```), tables (|...|), lists (-, 1.)
- Store original file path in frontmatter for reference
- Use domain-specific collections in Qdrant for context sharding

**Affects FR Categories**: FR4 (Memory), FR7 (Web Scraping)

---

### Pattern 3: Agent Workspace Detection & Handoff Protocol

**Purpose**: Enable JARVIS to take over its own development once capable (Bootstrap Handoff)

**Components:**

1. **Workspace Marker** (`.jarvis/config.yaml`)
   ```yaml
   project: JARVIS System
   owner: jarvis-infant
   handoff_ready: false  # Set to true when JARVIS can invoke BMAD
   capabilities_manifest: .jarvis/capabilities.yaml
   bmad_cli_path: /usr/local/bin/bmad  # or auto-detect
   ```

2. **Agent Detection Logic** (BMAD agents should implement this)
   ```python
   import os
   import yaml

   def check_jarvis_workspace():
       """Check if we're in JARVIS workspace and if handoff is ready"""
       if os.path.exists('.jarvis/config.yaml'):
           with open('.jarvis/config.yaml') as f:
               config = yaml.safe_load(f)
           if config.get('handoff_ready'):
               return True, "JARVIS is operational"
           return False, "JARVIS workspace (handoff not ready)"
       return False, "Not a JARVIS workspace"
   ```

3. **JARVIS→BMAD Invocation** (`src/jarvis/dev/bmad_invoker.py`)
   ```python
   import subprocess
   import json

   def invoke_bmad_agent(agent: str, task: str, context: dict):
       """Invoke BMAD agent with structured context"""
       context_json = json.dumps(context)

       result = subprocess.run(
           ['bmad', agent, task],
           input=context_json,
           capture_output=True,
           text=True
       )

       return json.loads(result.stdout)
   ```

**Data Flow:**
```
External AI Agent Enters Workspace
  ↓
Check for .jarvis/config.yaml
  ↓
If found: Read handoff_ready flag
  ↓
If handoff_ready == true:
  ↓
  Prompt User: "JARVIS is operational. Hand off development? [y/n]"
  ↓
  If yes:
    ↓
    Invoke JARVIS CLI: jarvis dev --request "user's original request"
    ↓
    JARVIS analyzes request → Determines needed BMAD agents
    ↓
    JARVIS invokes: bmad-dev, bmad-architect, etc. (subprocess)
    ↓
    BMAD generates code → JARVIS validates → JARVIS commits → JARVIS tests
    ↓
    Report to User: "Feature implemented. Testing complete."
```

**Handoff Criteria (When to set handoff_ready = true):**
1. ✅ JARVIS can successfully invoke `bmad` CLI
2. ✅ JARVIS can parse BMAD output (JSON or structured text)
3. ✅ JARVIS can validate generated code (syntax check, linting)
4. ✅ JARVIS can run tests and commit to git
5. ✅ User manually verifies handoff works correctly

**Implementation Guide:**
- Create `.jarvis/config.yaml` in first implementation story
- Initially set `handoff_ready: false`
- Implement BMAD invocation in FR8 implementation
- Test handoff with simple feature request
- Once stable, set `handoff_ready: true`
- BMAD agents should check this at session start

**Affects FR Categories**: FR8 (Bootstrap Evolution)

---

## Implementation Patterns (Consistency Rules for AI Agents)

### Naming Conventions

**Python Code:**
- **Modules/Packages**: `lowercase_with_underscores` (e.g., `rag_engine.py`, `llm_router.py`)
- **Classes**: `PascalCase` (e.g., `RAGEngine`, `LLMRouter`, `CouncilOfRicks`)
- **Functions/Methods**: `snake_case` (e.g., `generate_embedding`, `route_to_provider`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_CHUNK_SIZE`, `MAX_RETRIES`)
- **Private**: Prefix with `_` (e.g., `_internal_method`, `_validate_config`)

**Database:**
- **Tables**: `snake_case` plural (e.g., `conversations`, `llm_providers`, `agent_personas`)
- **Columns**: `snake_case` (e.g., `user_id`, `created_at`, `token_count`)
- **Foreign Keys**: `{table}_id` (e.g., `user_id`, `conversation_id`)

**File Naming:**
- **Python files**: `snake_case.py`
- **Markdown docs**: `kebab-case.md` (e.g., `architecture.md`, `capability-reference.md`)
- **Config files**: `lowercase.yaml` / `.env`

**CLI Commands:**
- **Top-level**: `jarvis {command}` (e.g., `jarvis ask`, `jarvis chat`)
- **Subcommands**: `jarvis {noun} {verb}` (e.g., `jarvis memory add`, `jarvis agents list`)
- **Flags**: `--kebab-case` (e.g., `--max-sources`, `--output-format`)

### Code Organization

**Test Placement**: Co-located tests
```
src/jarvis/core/rag_engine.py
tests/unit/test_rag_engine.py  # Mirror source structure
```

**Component Organization**: By feature, not by type
```
✅ Good:
src/jarvis/agents/
  orchestrator.py
  personas.py
  consensus.py

❌ Bad:
src/jarvis/models/agent_models.py
src/jarvis/services/agent_service.py
src/jarvis/controllers/agent_controller.py
```

**Shared Utilities**: `src/jarvis/utils/`
- Only truly generic helpers (logging, datetime, file operations)
- Feature-specific utils stay with feature

### Error Handling

**Exception Hierarchy:**
```python
class JarvisError(Exception):
    """Base exception for all JARVIS errors"""
    pass

class CapabilityNotFoundError(JarvisError):
    """Requested capability doesn't exist"""
    pass

class VectorDBError(JarvisError):
    """Qdrant/vector DB operation failed"""
    pass

class LLMProviderError(JarvisError):
    """LLM API call failed"""
    pass

class ConfigurationError(JarvisError):
    """Invalid configuration"""
    pass
```

**Error Handling Pattern:**
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error("Operation failed", exc_info=True, context={...})
    raise JarvisError(f"User-friendly message: {e}") from e
```

**Logging Errors:**
```python
import structlog

logger = structlog.get_logger()

try:
    query_result = rag_engine.query(user_query)
except VectorDBError as e:
    logger.error(
        "RAG query failed",
        query=user_query,
        error=str(e),
        provider="qdrant",
        exc_info=True
    )
    raise
```

### Logging Strategy

**Structured Logging with structlog:**
```python
import structlog

logger = structlog.get_logger(__name__)

# Info-level events
logger.info(
    "RAG query completed",
    query="How to optimize PostgreSQL?",
    sources_found=5,
    cost_usd=0.002,
    provider="openrouter",
    duration_ms=450
)

# Error-level events
logger.error(
    "LLM provider quota exceeded",
    provider="together_ai",
    quota_limit=1000000,
    tokens_used=1000543,
    fallback="openrouter"
)
```

**Log Levels:**
- **DEBUG**: Internal state, variable values (development only)
- **INFO**: Normal operations, successful queries, feature loads
- **WARNING**: Degraded performance, fallbacks, quota approaching
- **ERROR**: Failed operations, exceptions, user-facing errors
- **CRITICAL**: System-level failures, cannot recover

**Log Storage:**
- Main log: `~/.jarvis/logs/jarvis.log` (all levels)
- Error log: `~/.jarvis/logs/errors.log` (ERROR+ only)
- Dev log: `~/.jarvis/logs/dev.log` (development workflow events)
- Rotation: Daily, keep 30 days

### DateTime Handling

**Always UTC+0 (Lisbon Timezone):**
```python
from datetime import datetime, timezone

# ALWAYS use UTC for storage
now_utc = datetime.now(timezone.utc)

# Store in database as UTC
conversation.created_at = now_utc

# Convert to user timezone ONLY at display endpoints
from zoneinfo import ZoneInfo

def format_for_display(dt: datetime) -> str:
    """Convert UTC to Lisbon time for display"""
    lisbon_tz = ZoneInfo("Europe/Lisbon")
    lisbon_time = dt.astimezone(lisbon_tz)
    return lisbon_time.isoformat()
```

**Database Storage:**
- PostgreSQL: `TIMESTAMP WITH TIME ZONE` (stores UTC)
- Application: Always pass `datetime.now(timezone.utc)`

### Configuration Management

**YAML + Environment Variables + pydantic:**
```python
from pydantic_settings import BaseSettings
from pydantic import Field

class JarvisConfig(BaseSettings):
    """JARVIS configuration with validation"""

    # From .env (secrets)
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")

    # From config.yaml (structure)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 500

    class Config:
        env_file = ".env"
        yaml_file = "~/.jarvis/config.yaml"
```

**Config Files:**
- **`.env`**: Secrets (API keys, passwords) - NEVER commit to git
- **`~/.jarvis/config.yaml`**: Structure (paths, models, thresholds)
- **`.env.example`**: Template for users (no actual secrets)

### Testing Strategy

**pytest with Clear Structure:**
```python
# tests/unit/test_rag_engine.py
import pytest
from jarvis.core.rag_engine import RAGEngine

@pytest.fixture
def rag_engine():
    """Fixture for RAGEngine instance"""
    return RAGEngine(config=test_config)

def test_query_returns_sources(rag_engine):
    """RAG query should return relevant sources"""
    result = rag_engine.query("test query")

    assert result.sources is not None
    assert len(result.sources) > 0
    assert result.sources[0].relevance_score > 0.5
```

**Test Types:**
- **Unit**: Pure functions, business logic (fast, no external deps)
- **Integration**: Database ops, Qdrant queries (requires Docker)
- **E2E**: Full CLI commands (requires running JARVIS)

**Test Running:**
```bash
# Unit tests only (fast)
pytest tests/unit

# All tests
pytest

# With coverage
pytest --cov=jarvis --cov-report=html
```

---

## Consistency Rules (Cross-Cutting)

### API Response Format

**CLI Output:**
```python
# Default: Human-readable
$ jarvis ask "What is RAG?"
RAG (Retrieval-Augmented Generation) is...

[Sources: docs/rag-notes.md, web/pinecone.io/rag]
Cost: $0.00 (OpenRouter free tier)

# JSON: Machine-readable
$ jarvis ask "What is RAG?" --json
{
  "query": "What is RAG?",
  "response": "RAG (Retrieval-Augmented Generation) is...",
  "sources": [
    {"file": "docs/rag-notes.md", "score": 0.92},
    {"file": "web/pinecone.io/rag", "score": 0.87}
  ],
  "cost_usd": 0.0,
  "provider": "openrouter"
}
```

**MCP Tool Response:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "RAG query result: ..."
    }
  ],
  "metadata": {
    "sources": [...],
    "cost": 0.0,
    "provider": "openrouter"
  }
}
```

### Data Exchange Formats

**Dates in JSON**: ISO 8601 UTC
```json
{"created_at": "2025-11-17T14:30:00Z"}
```

**Money/Costs**: USD as float with 4 decimals
```json
{"cost_usd": 0.0023}
```

**Booleans**: `true/false` (lowercase) in JSON

**Null Values**: `null` in JSON, `None` in Python

### Lifecycle Patterns

**Loading States:**
```python
# CLI: Simple progress indicator
print("[JARVIS] Searching knowledge base...")

# Programmatic: Return status
{"status": "searching", "progress": 0.6}
```

**Error Recovery:**
```python
# Retry with exponential backoff
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_llm_api():
    ...
```

**Graceful Degradation:**
```python
# If Qdrant fails, fallback to keyword search
try:
    results = vector_search(query)
except VectorDBError:
    logger.warning("Vector search failed, falling back to keyword search")
    results = keyword_search(query)
```

---

## Data Architecture

### PostgreSQL Schema

**Conversations Table:**
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),  -- Future: multi-user support
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    agent_persona VARCHAR(100),  -- Which Rick responded (if applicable)
    cost_usd DECIMAL(10, 6),
    provider VARCHAR(100),
    model VARCHAR(100),
    token_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
```

**LLM Provider Tracking:**
```sql
CREATE TABLE llm_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,  -- 'openrouter', 'together_ai', etc.
    type VARCHAR(50) NOT NULL,  -- 'free_tier' | 'paid'
    priority INTEGER DEFAULT 100,  -- Lower = higher priority
    quota_limit BIGINT,  -- Tokens per month (if known)
    tokens_used BIGINT DEFAULT 0,
    last_reset TIMESTAMP WITH TIME ZONE,
    api_key_env VARCHAR(100),  -- ENV variable name
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE llm_usage_log (
    id BIGSERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES llm_providers(id),
    message_id UUID REFERENCES messages(id),
    model VARCHAR(100),
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd DECIMAL(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_usage_log_provider ON llm_usage_log(provider_id);
CREATE INDEX idx_usage_log_created_at ON llm_usage_log(created_at DESC);
```

**Agent Personas:**
```sql
CREATE TABLE agent_personas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,  -- 'Rickiest Rick', etc.
    system_prompt TEXT NOT NULL,
    weight DECIMAL(3, 2),  -- 0.40, 0.20, 0.10, 0.30
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Qdrant Collections

**Knowledge Collection:**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

client.create_collection(
    collection_name="knowledge",
    vectors_config=VectorParams(
        size=384,  # all-MiniLM-L6-v2
        distance=Distance.COSINE
    )
)

# Point structure:
{
    "id": "uuid-here",
    "vector": [0.123, -0.456, ...],  # 384 dimensions
    "payload": {
        "text": "chunk content",
        "source_file": "docs/postgres-notes.md",
        "section": "Performance Tuning",
        "domain": "databases",
        "ingested_at": "2025-11-17T14:30:00Z"
    }
}
```

**Context Sharding (Future):**
- Separate collections per domain: `knowledge_databases`, `knowledge_ai`, `knowledge_energy`
- Enables targeted search with domain filters

### Redis Data Structures

**Session Cache:**
```
jarvis:session:{session_id} → Hash
  {
    "user_id": "ariel",
    "conversation_id": "uuid",
    "last_activity": "2025-11-17T14:30:00Z"
  }
  TTL: 1 hour
```

**Rate Limiting:**
```
jarvis:ratelimit:{api_key}:{hour} → String (counter)
  TTL: 1 hour
```

**Query Cache (Optional):**
```
jarvis:cache:query:{hash(query)} → JSON
  {
    "response": "...",
    "sources": [...],
    "cost": 0.0
  }
  TTL: 5 minutes (short, since knowledge changes)
```

---

## Security Architecture

### API Key Management

**Storage:**
- LLM provider API keys: `.env` file (local) → Environment variables
- JARVIS API keys (future): PostgreSQL, hashed with bcrypt

**Access:**
```python
import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Never log API keys or secrets. Keep examples safe and show the right pattern:
logger.info("Calling OpenRouter", provider="openrouter")  # ✅
# DO NOT log secret values, e.g. NEVER do: logger.info(f"API key: {OPENROUTER_API_KEY}")
# If you need to debug authorization failures, log non-sensitive context only (provider, status code).
```

**Validation:**
- pydantic-settings validates env vars on startup
- Missing API keys → clear error message, not crash

### Data Privacy

**Local-First Architecture:**
- All user data stays on user's machine (Docker containers)
- No telemetry sent to external services
- Only LLM API calls leave the system

**Audit Trail:**
- All LLM API calls logged with query + cost + provider
- User can inspect: `jarvis costs --detailed`

**No External Analytics:**
- No Google Analytics, Sentry, etc.
- Errors logged locally only

### Input Validation

**Query Sanitization:**
```python
from bleach import clean

def sanitize_query(query: str) -> str:
    """Remove HTML, limit length"""
    query = clean(query, tags=[], strip=True)
    query = query[:5000]  # Max 5k chars
    return query
```

**Command Injection Prevention:**
```python
import shlex

# Safe subprocess calls
def run_git_command(cmd: list[str]):
    """Run git command safely"""
    # Use list, not string
    result = subprocess.run(
        ["git"] + cmd,
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.stdout
```

**File Path Validation:**
```python
from pathlib import Path

def validate_knowledge_path(path: str) -> Path:
    """Ensure path is within knowledge directory"""
    knowledge_dir = Path.home() / ".jarvis" / "knowledge"
    target = (knowledge_dir / path).resolve()

    if not target.is_relative_to(knowledge_dir):
        raise SecurityError("Path outside knowledge directory")

    return target
```

---

## Performance Considerations

### Query Latency Optimization

**Target: < 2s (P95) for RAG queries**

**Optimizations:**
1. **Embedding Caching**: Cache query embeddings for identical queries (Redis, 5 min TTL)
2. **Qdrant Tuning**: HNSW index with `m=16`, `ef_construct=200`
3. **Parallel LLM Calls**: Council of Ricks agents invoked in parallel (asyncio)
4. **Database Connection Pooling**: SQLAlchemy pool with 5-10 connections

### Vector Search Optimization

**Target: < 100ms for vector search**

**Qdrant Configuration:**
```yaml
# docker/qdrant/config.yaml
service:
  max_request_size_mb: 32

storage:
  # In-memory for speed (dev), disk for production
  storage_path: /qdrant/storage
  on_disk_payload: false  # Keep payloads in memory

collection:
  # HNSW parameters
  hnsw_config:
    m: 16  # Number of edges per node
    ef_construct: 200  # Construction time quality
    full_scan_threshold: 10000
```

**Query Optimization:**
```python
# Limit results
results = qdrant.search(
    collection_name="knowledge",
    query_vector=embedding,
    limit=5,  # Only top 5 sources
    score_threshold=0.7  # Filter low-quality matches
)
```

### Embedding Generation Batching

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Batch process documents (much faster than one-by-one)
chunks = [chunk1, chunk2, ..., chunk100]
embeddings = model.encode(chunks, batch_size=32)
```

### Background Task Optimization

**Memory Compilation** (future):
- Run during off-peak hours (configurable via cron)
- Process in batches (1000 conversations at a time)
- Write progress to avoid re-processing on failure

---

## Deployment Architecture

### Docker Compose Setup

**`docker/docker-compose.yml`:**
```yaml
version: '3.8'

services:
  jarvis:
    build:
      context: ..
      dockerfile: docker/Dockerfile.jarvis
    container_name: jarvis-app
    volumes:
      - ../:/workspace  # Mount entire project (self-modification)
      - jarvis-home:/root/.jarvis  # Persistent JARVIS data
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - TOGETHER_API_KEY=${TOGETHER_API_KEY}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    depends_on:
      - postgres
      - qdrant
      - redis
    networks:
      - jarvis-network
    command: jarvis chat

  postgres:
    image: postgres:18.1
    container_name: jarvis-postgres
    environment:
      - POSTGRES_DB=jarvis
      - POSTGRES_USER=jarvis
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./postgres/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    networks:
      - jarvis-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jarvis"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:v1.15.5
    container_name: jarvis-qdrant
    volumes:
      - qdrant-data:/qdrant/storage
      - ./qdrant/config.yaml:/qdrant/config/config.yaml
    ports:
      - "6333:6333"  # Expose for debugging
    networks:
      - jarvis-network

  redis:
    image: redis:latest
    container_name: jarvis-redis
    volumes:
      - redis-data:/data
    networks:
      - jarvis-network
    command: redis-server --appendonly yes

volumes:
  jarvis-home:
  postgres-data:
  qdrant-data:
  redis-data:

networks:
  jarvis-network:
    driver: bridge
```

### Container Health Checks

**PostgreSQL**: `pg_isready` command
**Qdrant**: HTTP health endpoint
**Redis**: `redis-cli ping`
**JARVIS**: Custom health check script

### Restart Policies

**Production:**
- `restart: unless-stopped` (auto-restart on failure)

**Development:**
- `restart: no` (manual restart for debugging)

---

## Development Environment

### Prerequisites

**System Requirements:**
- Docker Desktop or Docker Engine + Docker Compose
- Python 3.13+ (pyenv recommended)
- Git
- pandoc (`brew install pandoc` / `apt install pandoc` / `choco install pandoc`)

**Optional:**
- Poetry or uv (Python package managers)
- VS Code with Python extension

### Setup Commands

```bash
# 1. Clone repository
git clone <jarvis-repo-url>
cd jarvis

# 2. Install Python dependencies
# Option A: Poetry
poetry install

# Option B: pip + venv
python3.13 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Copy environment template
cp .env.example .env
# Edit .env with your API keys

# 4. Start Docker containers
docker compose -f docker/docker-compose.yml up -d

# 5. Initialize database
docker compose -f docker/docker-compose.yml exec postgres psql -U jarvis -d jarvis -f /docker-entrypoint-initdb.d/init-db.sql

# 6. Create Qdrant collection
python scripts/init_qdrant.py

# 7. Run tests
pytest

# 8. Start JARVIS CLI
jarvis chat
```

### Development Workflow

**Typical Dev Session:**
```bash
# 1. Activate virtual environment
source venv/bin/activate  # or: poetry shell

# 2. Start containers (if not running)
docker compose -f docker/docker-compose.yml up -d

# 3. Make code changes
# ... edit src/jarvis/...

# 4. Run tests
pytest tests/unit  # Fast unit tests
pytest tests/integration  # Requires Docker

# 5. Test CLI
jarvis ask "test query"

# 6. Check logs
tail -f ~/.jarvis/logs/jarvis.log

# 7. Stop containers (when done)
docker compose -f docker/docker-compose.yml down
```

---

## Architecture Decision Records (ADRs)

### ADR-001: Qdrant over pgvector for Vector Database

**Date**: 2025-11-17
**Status**: Accepted
**Decision**: Use Qdrant v1.15.5 as the vector database

**Context**:
- Need high-performance vector search (< 100ms latency)
- Context sharding for domain-specific knowledge
- Docker-native deployment

**Options Considered**:
1. **Qdrant**: Purpose-built, Rust-based, native sharding
2. **pgvector**: PostgreSQL extension, simpler stack

**Decision**: Qdrant

**Rationale**:
- Superior performance for pure vector operations
- Native context sharding support
- Already Docker-based, one more container is negligible
- Can migrate to pgvector later if needed (abstraction layer in code)

**Consequences**:
- Additional container in Docker Compose
- Need to learn Qdrant API (well-documented)
- Performance gains justify added complexity

---

### ADR-002: Python 3.13 for LTS Support

**Date**: 2025-11-17
**Status**: Accepted
**Decision**: Use Python 3.13 as the runtime

**Context**:
- Need modern type hints for Typer/pydantic
- LTS support desired (60-year vision)
- Performance improvements in 3.13

**Decision**: Python 3.13

**Rationale**:
- LTS support until 2029 (5 years of bugfixes + 3 years security)
- Modern type hints align with Typer's design
- Performance improvements in 3.13 benefit embedding generation

**Consequences**:
- Requires Python 3.13 installation (not yet default on all systems)
- Some libraries may not have 3.13 wheels yet (compile from source)

---

### ADR-003: Typer for CLI Framework

**Date**: 2025-11-17
**Status**: Accepted
**Decision**: Use Typer for CLI command parsing

**Context**:
- Need user-friendly CLI with auto-generated help
- Plugin architecture requires flexible command registration
- Self-documenting system benefits from type hints

**Options Considered**:
1. **Typer**: Modern, type-hint driven
2. **Click**: Proven, more verbose
3. **argparse**: Stdlib, manual setup

**Decision**: Typer

**Rationale**:
- Type hints auto-generate help text
- Clean, modern API aligns with Python 3.13
- Built on Click (mature foundation)
- Perfect for plugin-based architecture

**Consequences**:
- Dependency on Typer library
- Learning curve for contributors (minimal due to type hints)

---

### ADR-004: Markdown-Only Knowledge Base

**Date**: 2025-11-17
**Status**: Accepted
**Decision**: Convert all documents to Markdown before storage

**Context**:
- Need unified chunking strategy
- Git-friendly storage
- LLM-native format

**Decision**: All knowledge stored as Markdown

**Rationale**:
- Single chunking strategy (simpler, more maintainable)
- Git diffs work on Markdown (version control for knowledge)
- Embedding models perform well on structured text
- Human-readable (debugging, inspection)

**Consequences**:
- Requires pandoc installation (system dependency)
- Conversion step adds latency (acceptable for background ingestion)
- Some formatting loss (tables, complex layouts)

---

### ADR-005: Self-Modifying Development Environment

**Date**: 2025-11-17
**Status**: Accepted
**Decision**: JARVIS runs in same environment as development (dev == prod)

**Context**:
- Bootstrap evolution requires JARVIS to modify its own code
- Hot-reload plugin architecture for dynamic features
- User-choice development workflows

**Decision**: Unified dev/prod environment with workspace mounting

**Rationale**:
- Simplifies architecture (no deployment pipeline)
- Enables true self-modification
- Docker workspace mounting provides isolation + access

**Consequences**:
- Security risk if JARVIS is compromised (mitigated by local-only deployment)
- Rollback mechanism critical (git + tests)
- Careful validation before applying self-modifications

---

### ADR-006: Cost-First LLM Routing

**Date**: 2025-11-17
**Status**: Accepted
**Decision**: Optimize LLM routing for cost (free tiers first) rather than latency or quality

**Context**:
- 60-year operational cost projection
- Multiple free-tier LLM providers available
- User (Ariel) prioritizes budget optimization

**Decision**: "Run until depleted, switch" strategy

**Rationale**:
- Simple implementation (track usage via provider APIs)
- Maximizes free resources (OpenRouter, Together AI, etc.)
- Quality acceptable for most queries (can override for critical queries)

**Consequences**:
- Variable latency (switching providers adds overhead)
- Provider API dependency (tracking quotas)
- Need fallback to paid tiers (OpenAI, etc.)

---

### ADR-007: UTC+0 (Lisbon) for All Timestamps

**Date**: 2025-11-17
**Status**: Accepted
**Decision**: Store all timestamps in UTC (Lisbon timezone = UTC+0), convert only at display

**Context**:
- Need consistent time handling
- Avoid timezone bugs
- User preference: Lisbon timezone

**Decision**: UTC everywhere internally, `Europe/Lisbon` at endpoints

**Rationale**:
- UTC eliminates DST bugs
- Database compatibility (PostgreSQL `TIMESTAMP WITH TIME ZONE`)
- Lisbon = UTC+0 most of year (simple)

**Consequences**:
- Must remember to convert at display
- All datetime objects must have `timezone.utc`

---

### ADR-008: ARCHES Controller Pattern (v2.4)

**Date**: 2025-12-09
**Status**: Accepted (Epic 4-5 complete)
**Decision**: Centralize cognitive orchestration via ARCHESRuntime controller

**Context**:
- Distributed agent pattern caused coordination chaos
- Need session state management across retrieval, agents, voting
- Cognitive traces required centralized execution tracking
- Memory attribution needed per-agent chunk provenance

**Options Considered**:
1. **Distributed Pattern**: Each agent independently queries memory and votes
2. **ARCHES Controller**: Centralized orchestration with session state
3. **Event Bus**: Message-based coordination

**Decision**: ARCHES Controller

**Rationale**:
- Prevents cognitive chaos of distributed systems
- Enables session state management (conversation_id, user context)
- Facilitates cognitive trace logging (single execution path)
- Supports agent memory attribution (controller tracks which chunks → which agents)
- Allows adaptive planning with feedback loops

**Consequences**:
- Single controller must handle all orchestration (potential bottleneck)
- Benefits: Coherent architecture, full observability, easier testing
- Breaking change from v2.1 distributed pattern (migration required)
- Location: `src/jarvis/arches/runtime.py`

**Related**:
- FR12.1: ARCHES Runtime Controller
- Epic 4-5: ARCHES Cognitive Stabilization

---

### ADR-009: Governance Architecture with Machine Democracy (v4.0)

**Date**: 2025-12-09
**Status**: Accepted (Epic 9 complete)
**Decision**: Multi-human governance with trust-weighted voting and constitutional constraints

**Context**:
- Single-user AI assistant model insufficient for production use
- Need democratic oversight for system changes
- Compliance requirements (GDPR, AI Act, SOC 2) demand governance infrastructure
- Trust calibration needed (domain expertise should matter)

**Options Considered**:
1. **Single Owner Model**: One user has full control
2. **Role-Based Access Control (RBAC)**: Static roles without voting
3. **Machine Democracy**: Trust-weighted voting with constitutional framework

**Decision**: Machine Democracy

**Rationale**:
- Multi-human oversight prevents single points of failure
- Trust-weighted voting (domain expertise matters) improves decision quality
- Constitutional framework (core values + red lines) programmatically enforced
- Compliance-ready: GDPR (consent), AI Act (transparency), SOC 2 (access control)
- Governance dashboard provides real-time transparency

**Architecture Components**:
- 4 Roles: Owner (full authority), Admin (system config), Contributor (proposals), Observer (read-only)
- Voting Engine: Proposals with quorum, timeouts, approval/rejection
- Trust System: Domain-specific trust scores (security, AI/ML, governance)
- Constitutional Framework: Core values (safety, privacy, truth, sovereignty)
- Dashboard: `/governance` - proposals, votes, trust leaderboard

**Consequences**:
- Database schema expansion: `governance_users`, `proposals`, `votes`, `constitution`
- System changes require consensus (intentional friction)
- Benefits: Compliance moat, multi-human oversight, programmatic value enforcement
- Location: `src/jarvis/governance/` (split from `governance_legacy.py`)

**Related**:
- FR11: Political Governance & Multi-Human Consensus
- Epic 9: Political Governance & Multi-Human Consensus

---

### ADR-010: Autonomous Knowledge Graph (v2.3)

**Date**: 2025-12-09
**Status**: Accepted (Epic 8-7 complete)
**Decision**: Self-maintaining entity/relationship graph with MCP integration

**Context**:
- RAG retrieval limited to document chunks (misses entity relationships)
- Need to answer "who worked with X on Y?" type queries
- Graph should auto-update on document ingestion (no manual curation)

**Options Considered**:
1. **Manual Graph Curation**: Human-maintained entity/relationship database
2. **LLM-Extracted Graph**: One-time extraction, static
3. **Self-Maintaining Graph**: Auto-extraction on ingestion with MCP tools

**Decision**: Self-Maintaining Graph

**Rationale**:
- Zero manual curation (autonomy goal)
- Graph updates automatically on document ingestion
- MCP tools provide standardized graph operations
- Supports graph-enhanced retrieval (traverse relationships for context)

**Architecture Components**:
- Entity Extraction: Automatic entity discovery from documents
- Relationship Discovery: Connections between entities
- Observation Attachment: Facts, attributes, context per entity
- MCP Integration: `create_entities`, `create_relations`, `open_nodes`, `search_nodes`

**Consequences**:
- Graph quality depends on LLM extraction accuracy
- Benefits: Relationship-aware retrieval, zero manual work
- Graph operations add latency (~50-100ms per query if used)
- Location: MCP-based (no direct code location, uses MCP Docker tools)

**Related**:
- FR13: Autonomous Knowledge Graph
- Epic 8-7: Autonomous Knowledge Graph

---

### ADR-011: Sovereign Identity with Keycloak (v4.1)

**Date**: 2025-12-09
**Status**: In Progress (Epic 11 - Story 11-1)
**Decision**: Keycloak OAuth2/OIDC for industry-standard identity management

**Context**:
- Current governance system uses custom user table (not scalable)
- Need industry-standard authentication (OAuth2/OIDC)
- Privacy-aware traces require user context propagation
- Multi-tenancy requires user-scoped database operations

**Options Considered**:
1. **Custom Auth**: Roll our own JWT + user management
2. **Auth0/Okta**: Managed SaaS (vendor lock-in, cost)
3. **Keycloak**: Open-source, self-hosted, Docker-native

**Decision**: Keycloak

**Rationale**:
- Industry-standard OAuth2/OIDC implementation
- Self-hosted (aligns with JARVIS philosophy)
- Docker-native deployment
- Role-based access control (RBAC) with JWT role claims
- Token refresh and session management built-in

**Architecture Components**:
- Keycloak Server: Docker Compose service
- OAuth2 Authorization Code Flow: Standard web flow
- JWT Token Validation: RS256 signature verification
- User Context Middleware: Extract user from `Authorization: Bearer` header
- Role Mapping: Governance roles (owner, admin, contributor, observer) → Keycloak roles

**Consequences**:
- Additional container in Docker Compose (Keycloak + PostgreSQL for Keycloak DB)
- All API endpoints must validate JWT tokens (breaking change)
- Benefits: Industry-standard auth, multi-tenancy, privacy-aware traces
- Migration: Existing governance users → Keycloak realm import
- Location: `config/keycloak/`, `src/jarvis/api/dependencies.py`

**Related**:
- FR14: Sovereign Identity Layer
- Epic 11: Sovereign Identity Layer

---

## Next Steps (For Implementation Phase)

**After Architecture is Complete:**

1. **Epic Breakdown** - Run `/bmad:bmm:workflows:create-epics-and-stories-final`
   - Break down FRs into implementation stories
   - Prioritize epics (MVP first)

2. **Implementation Readiness Check** - Run `/bmad:bmm:workflows:implementation-readiness`
   - Validate PRD + Architecture alignment
   - Ensure no gaps or contradictions

3. **Sprint Planning** - Run `/bmad:bmm:workflows:sprint-planning`
   - Create sprint tracking file
   - Begin development with Story 1: Project setup

**First Epic (Project Setup - MVP Foundation):**
- Story 1: Project initialization (Python, Poetry, Docker Compose)
- Story 2: Database schema setup (PostgreSQL init scripts)
- Story 3: Qdrant collection creation
- Story 4: Basic CLI with Typer (`jarvis --help`)
- Story 5: Configuration management (pydantic-settings + YAML)

**Development Priority:**
1. **MVP Core** (FR1, FR4 basics): RAG query + memory
2. **Cost Routing** (FR3): LLM provider management
3. **CLI** (FR6): Polished command interface
4. **Self-Modification** (FR8): Hot-reload + BMAD invocation (Bootstrap Handoff)
5. **Council of Ricks** (FR2): Multi-agent orchestration
6. **Future Features** (FR7, FR9, FR10): Web scraping, web interface, 60-year memory

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Living Document - JARVIS will auto-update as capabilities expand_
_Last Updated: 2025-11-17 by Architect Agent (Ariel + Claude)_
