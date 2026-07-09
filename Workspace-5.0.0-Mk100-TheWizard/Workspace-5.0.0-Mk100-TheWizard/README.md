# JARVIS System - Governed Cognitive Institution

**Not a chatbot. A Cognitive OS with a Parliament.**

JARVIS is a self-hosted, **governed cognitive institution** built through the BMAD method. Beyond traditional AI assistants, JARVIS combines multi-agent reasoning (Council of Ricks), autonomous research, democratic governance, and full cognitive introspection to create a truly intelligent system with constitutional constraints and multi-human oversight.

**Current Release:** `v5.0.0 Mk100 "The Wizard"` 🧙‍♂️

### What's New in v5.0.0 Mk100 "The Wizard"

**Epic 11: Sovereign Identity & Architectural Locks** ✅ COMPLETE
- **7 Architectural Locks Verified:** LLM-isolated goal derivation, math sovereignty, capability boundaries, workflow ceilings, intent drift detection, multi-human gates, append-only audit
- **Sovereign Mode:** Fail-closed cognitive security with component health tracking
- **Provenance CLI:** `jarvis provenance verify` for cryptographic integrity validation
- **Keycloak OAuth2/OIDC Integration:** Industry-standard identity management
- **User Context Propagation:** All API requests user-scoped
- **Privacy-Aware Traces:** Cognitive traces respect user permissions
- **Status:** ✅ Production-ready, all 7 Locks verified

**Epic 8-8: Governance Context Optimization** 🟢 READY
- **Mechanical Gate Passed:** `sovereign.json` declares Epic 11 stability
- **Epistemic Autonomy:** Autonomous evolution capability now unlocked
- **Status:** 🚀 Ready for activation

**Previous Epics:**

**Epic 9: Political Governance & Multi-Human Consensus** ✅
- **Machine Democracy:** Multi-human voting with proposals, quorum, and timeouts
- **Trust-Weighted Consensus:** Domain expertise matters (votes weighted by trust scores)
- **Constitutional Framework:** Core values (safety, privacy, truth, sovereignty) programmatically enforced
- **Status:** ✅ Production-ready, compliance moat (GDPR, AI Act, SOC 2)

**Epic 4-5: ARCHES Cognitive Stabilization** ✅
- **ARCHES Controller:** Centralized cognitive orchestration with session state management
- **MMR Diversity Filter:** Eliminates retrieval saturation (91% voting disagreement reduction)
- **Status:** ✅ Production-ready, A+ architectural quality

**Previous Milestones:**
- **v2.2.0:** Frontend decoupling, UI observability (`window.__JARVIS_UI_VERSION__`)
- **v2.1.0:** Council of Ricks operational, weighted chaos voting
- **v2.0.0:** Hybrid RAG, multi-agent consensus, persistent memory  

---

## Table of Contents

1. [Vision & Goals](#vision--goals)  
2. [Architecture Snapshot](#architecture-snapshot)  
3. [Requirements & Setup](#requirements--setup)  
4. [Repository Layout](#repository-layout)  
5. [Jarvis Core & Memory](#jarvis-core--memory)  
6. [Key Documents & Status](#key-documents--status)  
7. [Delivery Workflow](#delivery-workflow)  
8. [Sprint Tracking](#sprint-tracking)  
9. [Quality & Test Strategy](#quality--test-strategy)  
10. [Roadmap & Next Steps](#roadmap--next-steps)  

---

## Vision & Goals

JARVIS is a **Governed Cognitive Institution** - not just an AI assistant, but a complete cognitive operating system with democratic governance, constitutional constraints, and full cognitive introspection.

**Core Capabilities:**
- **Multi-Agent Reasoning:** Council of Ricks with weighted chaos voting (91% faster than sequential)
- **Autonomous Research:** Self-aware gap detection and proactive knowledge seeking
- **Democratic Governance:** Multi-human consensus with trust-weighted voting and constitutional constraints
- **Cognitive Introspection:** Full trace observability - replay any query's execution with `jarvis trace replay`
- **60-Year Memory:** Hybrid retrieval (semantic + keyword) with freshness enforcement and MMR diversity
- **Self-Modification:** Runs in dev == prod environment, evolves autonomously via BMAD workflows
- **Cost Optimization:** Free-tier-first LLM routing with transparent telemetry

**What Makes This Special:**
- **Machine Democracy in Production:** Trust-weighted voting, constitutional framework, governance dashboard
- **Cognitive Trace Observability:** See exactly how every decision was made (unprecedented transparency)
- **Constitutional AI:** Core values (safety, privacy, truth, sovereignty) enforced programmatically
- **Agent Memory Attribution:** Know which chunks informed which agent's reasoning
- **Compliance-Ready:** GDPR, AI Act, SOC 2 alignment through governance infrastructure

**Documentation:**
- **Master Hub:** [docs/index.md](docs/index.md) - Complete navigation for all 155 documentation files
- **PRD:** [docs/reference/prd.md](docs/reference/prd.md) - Functional requirements (FR1–FR14)
- **Architecture:** [docs/reference/architecture.md](docs/reference/architecture.md) - System design and ADRs
- **Retrospectives:** [docs/sprints/](docs/sprints/) - BMAD-compliant epic retrospectives

---

## Architecture Snapshot

Built from the decisions in [docs/reference/architecture.md](docs/reference/architecture.md):

**Cognitive Controller (ARCHES):**
- **ARCHES Runtime Controller:** Centralized cognitive orchestration managing session state, planning, and memory attribution
- **Cognitive Trace Logging:** Full observability - replay any query's execution path with `jarvis trace replay <trace_id>`
- **Agent Memory Attribution:** Track which chunks informed which agent's reasoning (per-agent provenance)
- **Adaptive Planning:** Feedback loops allow ARCHES to refine plans based on execution results

**Multi-Agent System:**
- **Council of Ricks:** 4 personas (Rickiest Rick, Analytical Rick, Supportive Rick, Chaotic Rick)
- **Weighted Chaos Voting:** Confidence × weight × consistency bonus determines final answer
- **Parallel Invocation:** 91% faster than sequential (2.1s vs 23s for 4 personas)
- **Autonomous Research:** Self-aware memory gap detection triggers MCP-based research

**Governance Infrastructure:**
- **Multi-Human Governance:** 4 roles (Owner, Admin, Contributor, Observer) with clear authority structures
- **Trust-Weighted Voting:** Domain expertise matters - votes weighted by trust scores
- **Constitutional Framework:** Core values (safety, privacy, truth, sovereignty) programmatically enforced
- **Governance Dashboard:** Real-time transparency at `/governance` (proposals, votes, trust leaderboard)

**Data Layer:**
- **Runtime:** Python 3.13 + FastAPI + Typer CLI + structlog
- **Databases:** PostgreSQL 18.1 (conversations + governance), Qdrant 1.15.5 (vectors), Redis (cache)
- **Memory Retrieval:** Hybrid search (semantic + keyword BM25), MMR diversity filter, freshness enforcement (`is_latest`)
- **Future:** MongoDB/Timescale tiers for 60-year memory continuum

**LLM Infrastructure:**
- **Cost Router:** Prioritizes free-tier models (Gemini Flash, Llama 3.1)
- **Provider Telemetry:** Full cost tracking via `llm_usage_log` table
- **Model Arsenal:** OpenRouter, Anthropic Direct, Google AI, Together AI

**Observability:**
- **Structured Logging:** JSON logs with trace IDs, latency metrics, memory attribution
- **Health Checks:** `/healthz` endpoints for all services
- **Cognitive Traces:** Full query execution replay capability
- **Memory Attribution:** Per-agent chunk provenance tracking

---

## Requirements & Setup

| Need | Description |
| ---- | ----------- |
| OS | Windows 11 + PowerShell (primary), works in WSL/Linux with equivalent commands. |
| Tooling | Git, Docker Desktop, Python 3.13+, Poetry (future code stages), PowerShell 7+ for scripts. |
| Scripts | `scripts/bmad/init-bmad.ps1`, `scripts/bmad/workflow-init.ps1`, `scripts/bmad/orchestrate-jarvis.ps1`. |

### Quick Start

```powershell
git clone https://github.com/ABastos20/Workspace.git
cd Workspace
# Optional: copy .env.example if you want to override defaults
Copy-Item .env.example .env

powershell -ExecutionPolicy Bypass -File .\scripts\bmad\init-bmad.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\bmad\workflow-init.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\bmad\orchestrate-jarvis.ps1
```

Then follow the sprint status file to pick the first story.

### Running the Docker Stack

```powershell
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f jarvis
docker compose -f docker/docker-compose.yml down
```

All secrets are pre-defined for local development (Postgres defaults to `jarvis-dev-password`); `.env` overrides are optional. Services provisioned:
- `jarvis-app` (Python 3.13 base, workspace mount, structlog health check)
- `jarvis-postgres` (18.1 with init SQL + health probe)
- `jarvis-qdrant` (v1.15.5)
- `jarvis-redis` (append-only persistence)

> **Upgrade note:** Postgres 18 expects its data volume mounted at `/var/lib/postgresql`.
> If you previously ran an older compose version, remove the old volume first:
> `docker compose -f docker/docker-compose.yml down -v && docker volume rm workspace_postgres-data || true`

If you want container-created files to match your host UID/GID (Linux), start compose with:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f docker/docker-compose.yml up --build -d
```

The entrypoint script will chown `/workspace/.jarvis` accordingly.

### Web Chat UI (Jarvis BMAD Console)

Once the stack is up, Jarvis exposes a minimal web chat surface:

- **URL:** `http://localhost:8000/chat`
- **Purpose:** Talk to Jarvis over your local knowledge base (docs, GPT exports, conversations) using the same RAG engine as `jarvis query`.

Features:

- **Conversations sidebar**
  - Lists recent conversations from Postgres (title = last assistant message snippet + message count).
  - `+ New` button starts a fresh conversation without deleting older ones.

- **Chat panel**
  - Simple chat UI:
    - Type a message and press Enter or click `Send`.
    - Jarvis replies with a grounded answer, reusing the CLI RAG loop.
  - Controls under the input:
    - `strict` – when enabled, forces librarian mode (no creative fallback if memory is empty).
    - `domain` – optional domain hint (e.g. `jarvis-core`, `jarvis.conversations`, `gd.generative_drive`) to bias retrieval toward a specific domain.

- **Citations & context**
  - Under each assistant reply, a `Sources:` strip renders when citations are present:
    - Chips like `[1] jarvis.conversations s=0.82` or `[2] docs/jarvis-knowledge-pipeline.md s=0.93`.
    - Hovering a chip opens a small balloon with:
      - File path and section (when available).
      - Optional chunk identifier.
      - A short preview of the chunk text used to ground the answer.

Under the hood this UI talks to:

- `POST /api/chat` – RAG + LLM chat endpoint (see below).
- `POST /api/conversations` – create conversation container if none exists.
- `GET /api/conversations/{id}?page_size=100` – reload conversation history.

### Configuration & Secrets

1. Copy `config/settings.example.yaml` → `config/settings.yaml` and adjust values as needed.  
   - File uses JSON syntax (valid YAML) to stay dependency-free.  
   - Define project metadata, workspace paths, and provider entries referencing env vars (e.g., `api_key_env`).  
2. Populate `.env` (optional) with secrets referenced in the config (already ignored by git).  
3. At runtime, `jarvis.config.load_settings()` loads `.env`, then `config/settings.yaml`, falling back to the example file if a custom config is missing.  
4. Additional overrides: set `WORKSPACE_ROOT` / `WORKSPACE_PRIVATE_DIR` environment variables to customize paths without editing the config file.

See `docs/sprints/stories/1-3-configuration-secret-management.md` for the implementation plan and verification notes.

### Epistemic Audit Configuration (Story 11-5)

The Knowledge Sovereignty system logs all epistemic events (promotions, demotions, freezes, violations) to configurable sinks:

```bash
# Environment variable (comma-separated)
EPISTEMIC_AUDIT_SINKS=memory,stdout,postgres

# Options:
# - memory: In-memory storage for queries (default, always included)
# - stdout: JSON logs to stdout via structlog (Graylog/ELK integration)
# - postgres: PostgreSQL persistence (requires session factory configuration)
```

**Default behavior:** If not set, only in-memory storage is used.

**Production deployment example:**
```yaml
# docker-compose.yml
services:
  jarvis:
    environment:
      EPISTEMIC_AUDIT_SINKS: memory,stdout
    logging:
      driver: gelf
      options:
        gelf-address: "udp://graylog:12201"
```

**Database setup (for postgres sink):**
```bash
# Run Alembic migration to create epistemic_events table
alembic upgrade head
```

See [Story 11-5.3](docs/sprints/stories/11-5.3-stdout-observability-sink.md) for observability integration details.

---

## LLM Client Activation (Story 2.5)

**Status:** LLM infrastructure built in Epic 2, ready for activation in Epic 3.

The memory compilation service (`jarvis memory compile`) uses LLM calls to generate insights from conversation history. The LLM client is built and tested with mocked responses, but requires API key configuration for live operation.

### Prerequisites

1. **OpenRouter API Key** (recommended free-tier provider)
   - Sign up at [openrouter.ai](https://openrouter.ai/)
   - Generate an API key from your dashboard
   - OpenRouter provides access to multiple models including Claude, GPT-4, and free-tier options

2. **Alternative Providers** (for future)
   - Anthropic Direct (`ANTHROPIC_API_KEY`)
   - OpenAI Direct (`OPENAI_API_KEY`)
   - Together AI (`TOGETHER_API_KEY`)

### Setup Instructions

1. **Add API Key to Environment:**

   Create or update `.env` in the project root:
   ```bash
   # LLM Provider Configuration
   OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
   ```

2. **Verify Configuration:**
   ```bash
   # Check that .env is loaded
   docker compose -f docker/docker-compose.yml config
   ```

3. **Test Memory Compilation (First Live LLM Call):**
   ```bash
   # Run compilation on last 7 days of conversations
   docker compose -f docker/docker-compose.yml run --rm jarvis \
     jarvis memory compile --since 7d
   ```

   **Expected Output:**
   ```
   📚 Compiling memories from 2025-11-19 to now...
      Auto-ingest: Yes

   ✅ Compilation completed successfully!

   📊 Summary:
      Conversations: 12
      Messages: 48
      Provider: openrouter
      Model: anthropic/claude-3.5-sonnet
      Tokens: 1234 in + 567 out
      Cost: $0.0234

   📄 Output file: ~/.jarvis/knowledge/insights/2025-11-19_to_2025-11-26-insights.md

   🔍 Auto-ingested: 3 chunks, 3 points written
      Search with: jarvis memory search --source jarvis-insights "your query"
   ```

4. **Verify Cost Tracking:**
   ```bash
   # Query PostgreSQL to verify cost was logged
   docker compose -f docker/docker-compose.yml exec postgres psql -U jarvis -d jarvis \
     -c "SELECT p.name AS provider, l.model, l.cost_usd, l.created_at \
FROM llm_usage_log l \
JOIN llm_providers p ON p.id = l.provider_id \
ORDER BY l.created_at DESC \
LIMIT 5;"
   ```

5. **Verify Insights Ingested:**
   ```bash
   # Search for compiled insights
   docker compose -f docker/docker-compose.yml run --rm jarvis \
     jarvis memory search --source jarvis-insights "patterns"
   ```

### Cost Management

**FREE MODELS AVAILABLE** (recommended for cost-conscious users):

OpenRouter provides access to many **completely free models** that work well for memory compilation:

- **Meta Llama 3.2 (3B)** - `meta-llama/llama-3.2-3b-instruct:free` (FREE, fast, good quality)
- **Meta Llama 3.1 (8B)** - `meta-llama/llama-3.1-8b-instruct:free` (FREE, better quality)
- **Google Gemini Flash** - `google/gemini-flash-1.5:free` (FREE, excellent quality)
- **Mistral 7B** - `mistralai/mistral-7b-instruct:free` (FREE, reliable)

**To use a free model**, update [client.py:40](src/jarvis/llm/client.py#L40):
```python
model: str = "meta-llama/llama-3.1-8b-instruct:free"  # FREE MODEL
```

**Paid Models** (only if you need best quality):
- **Default Model:** `anthropic/claude-3.5-sonnet` (via OpenRouter)
- **Estimated Cost:** ~$0.02-0.05 per week of conversations compiled
- **Cost Tracking:** All LLM calls logged to `llm_usage_log` table with provider, model, tokens, and cost_usd

### Troubleshooting

**"OPENROUTER_API_KEY not found":**
- Verify `.env` file exists in project root
- Check `docker-compose.yml` has `env_file: [".env"]` (already configured)
- Restart Docker Compose: `docker compose down && docker compose up -d`

**"Memory compilation failed: API error":**
- Check API key is valid: [openrouter.ai/keys](https://openrouter.ai/keys)
- Verify network connectivity: `curl -I https://openrouter.ai/api/v1/chat/completions`
- Check rate limits: Free tier may have request/minute caps

**Cost concerns:**
- Use `--no-ingest` flag to skip auto-ingestion during testing
- Monitor costs via: `SELECT SUM(cost_usd) FROM llm_usage_log WHERE created_at > NOW() - INTERVAL '30 days';`
- Switch to cheaper model in `src/jarvis/llm/client.py` (default_model parameter)

### Architecture Details

**Files:**
- `src/jarvis/llm/client.py` - LLM client with OpenRouter integration
- `src/jarvis/memory/compile.py` - Compilation service using LLM client
- `src/jarvis/cli/memory.py` - CLI command `jarvis memory compile`

**Tests:**
- `tests/unit/llm/test_client.py` - Unit tests with mocked HTTP responses
- `tests/unit/memory/test_compile.py` - Compilation service tests

**Database Schema:**
- `llm_providers` - Provider registry (openrouter, anthropic, etc.)
- `llm_usage_log` - Cost tracking per LLM call

**See:** `docs/sprints/stories/2-5-scheduled-memory-compilation.md` for full implementation details.

---

## Repository Layout

```
.
├── README.md                     # Corporate-ready overview (this file)
├── README_BMAD.md                # BMAD-specific workspace quick links
├── .env.example                  # Template for docker/.env secrets
├── docs/                         # Planning + governance artifacts
│   ├── index.md                  # Master Documentation Index
│   ├── guides/                   # User and Developer Guides
│   ├── reference/                # Core Reference (PRD, Architecture, Agents)
│   ├── status/                   # Project Status and Tracking
│   ├── legacy/                   # Archived Documentation
│   ├── sprints/                  # Sprint plans & status files
│   ├── jarvis/                   # Jarvis persona, operating manual, and imports
│   └── bmm-workflow-status.yaml  # Workflow tracker (method track)
├── scripts/                      # PowerShell helpers
│   ├── bmad/                     # BMAD orchestration
│   ├── setup/                    # Initialization scripts
│   ├── ops/                      # Operational scripts
│   └── ingestion/                # Data pipeline scripts
├── docker/                       # Docker Compose stack + service configs
│   ├── docker-compose.yml
│   ├── Dockerfile.jarvis
│   ├── postgres/init-db.sql
│   ├── qdrant/config.yaml
│   └── redis/redis.conf
├── .bmad/                        # BMAD engine config, agents, integrations
└── .vscode/                      # Recommended editor settings
```

---

## Jarvis Core & Memory

Jarvis has a small set of **constitutional docs** and a Qdrant-backed memory store that every agent is expected to respect:

- Core docs (identity + operation), under `docs/jarvis/`:
  - `persona.md` – who Jarvis is, values, defaults.
  - `operating-manual.md` – how Jarvis behaves in this workspace.
  - `gd-overview.md` – GenerativeDrive high-level design.
  - `playbooks/` – reusable flows (e.g. architect meeting prep, GD energy threads).
- GPT export integration:
  - `scripts/ingestion/import_gpt_export.py` – extracts core threads from `docs/gpt export/conversations.json` and builds:
    - `docs/jarvis/conversation-index.md`
    - `docs/jarvis/user-export-snapshot.md`
  - `docs/gptExportNEW/memory.core.md` – consolidated long-horizon GPT history and configuration for Jarvis+you, ingested as `domain="jarvis-core"` and treated as primary core memory.

### Memory ingestion (Qdrant `knowledge` collection)

The memory system is built around a single Qdrant collection:

- Ingestion core:
  - `src/jarvis/memory/ingest.py` – format detection, markdown normalization, chunking, embeddings, and Qdrant upsert.
  - Supported formats:
    - Markdown / text: `.md`, `.markdown`, `.txt` (read directly and chunked).
    - PDF: `.pdf` (text extracted via PyPDF2, then treated as markdown).
    - HTML and other formats via `pypandoc` when available.
  - Sources and scripts:
    - `scripts/ingestion/ingest_jarvis_docs.py` – ingests core docs as `domain="jarvis-core"`.
    - `scripts/setup/bootstrap_jarvis_memory.py` – master script to initialize Qdrant and ingest core docs + GPT exports (`domain="jarvis-core"` and `domain="jarvis-conversations"`).
    - `scripts/ingestion/ingest-all-docs.sh` – bulk-ingests repo documentation (`docs/**.md` and `.bmad/bmm/**.md`) into the knowledge collection.
    - Host workspace and OneDrive:
      - Docker mounts the repo at `/workspace` and OneDrive at `/mnt/onedrive:ro`.
      - You can ingest personal notes and PDFs from OneDrive with:
        - `find /mnt/onedrive -type f \( -name '*.md' -o -name '*.markdown' -o -name '*.txt' -o -name '*.pdf' \) … | xargs python -m jarvis.cli.main memory add`.
    - Gemini-powered catalog + enrichment:
      - `scripts/ingestion/run_gemini_catalog_enrichment.sh` orchestrates a full run that:
        1. Classifies chunks into domains/personas (`catalog-domains` via `google-ai` / Gemini).
        2. Enriches chunks with `summary`, `facts`, `tags`, and `doc_type` (`enrich-chunks`).
      - Run inside `jarvis-app`:
        - `docker exec -it jarvis-app bash -lc "bash scripts/ingestion/run_gemini_catalog_enrichment.sh"`
      - Tunable via env:
        - `JARVIS_ENRICH_MODEL` (e.g. `gemini-2.5-pro`, `gemini-2.5-flash` once configured),
        - `JARVIS_CATALOG_LIMIT`, `JARVIS_ENRICH_LIMIT`, `JARVIS_ENRICH_DOMAINS`, etc.
- Retrieval core:
  - `src/jarvis/memory/search.py` – embeds queries and searches Qdrant, returning ranked `SearchResult` objects with metadata and structured logging (latency, filter info).
  - Keyword + hybrid retrieval:
    - `keyword_search` uses PostgreSQL full-text search (`to_tsvector`, `plainto_tsquery`, `ts_rank_cd`) over `messages.content` for BM25-like scoring.
    - `hybrid_search` combines semantic (Qdrant) and keyword (Postgres) results, normalizes scores per modality and merges with a configurable weight.
    - Optional cross-encoder reranking:
      - When `JARVIS_RERANK_ENABLED` is set to `1`/`true`/`yes`, `search_memory` reranks the top-N candidates using a MS MARCO-trained MiniLM cross-encoder, enriching payloads with `rerank_score` and `original_score` while preserving the simple vector-first behavior when disabled.

### Query CLI (RAG + hybrid retrieval)

- CLI (Typer), `src/jarvis/cli/query.py`:
  - `jarvis query "your question"` – RAG query with semantic retrieval by default.
  - `jarvis query "what did we learn last week?" --source jarvis-insights` – restricts retrieval to compiled insights.
  - `jarvis query "vector search edge cases" --retriever keyword` – keyword-only retrieval (Postgres FTS / BM25-like).
  - `jarvis query "vector search edge cases" --retriever hybrid --weight 0.7` – hybrid retrieval (70% semantic, 30% keyword).
  - `jarvis query "what did we build in Epic 3?" --json-output` – returns a machine-readable envelope with answer, structured citations, and provider/cost metadata (used by MCP agents and analytics).

Retriever defaults can be configured in `config/settings.yaml`:

```json
{
  "query": {
    "default_retriever": "semantic",
    "default_weight": 0.7
  }
}
```

If CLI flags are omitted, `jarvis query` uses these defaults; flags always override config.

### CLI & API

- CLI (Typer), `src/jarvis/cli/memory.py`:
  - `jarvis memory add PATH` – ingest a single document.
  - `jarvis memory search "query" --source jarvis-core --k 5` – semantic search with domain filters.
- API (FastAPI):
  - `POST /api/memory/search` – request body includes `query`, optional `persona`, `source`, `since`, `k`; response returns ranked snippets with `text`, `score`, `source_file`, `section`, `domain`, and payload metadata.

For detailed commands and expected outputs, see `JARVIS_INGESTION_GUIDE.md`.

---

## Key Documents & Status

| Artifact | Purpose | Location | Status |
| -------- | ------- | -------- | ------ |
| **Master Documentation Hub** | Complete navigation for all docs | [docs/index.md](docs/index.md) | ✅ Production-ready |
| **PRD** | Vision, FR1–FR14, NFRs | [docs/reference/prd.md](docs/reference/prd.md) | ⚠️ v2.1.0 (needs v2.5 update) |
| **Architecture** | Stack, patterns, ADRs | [docs/reference/architecture.md](docs/reference/architecture.md) | ⚠️ v2.1.0 (needs v2.5 update) |
| **Epics & Stories** | Execution backlog | [docs/status/epics.md](docs/status/epics.md) | ✅ Complete (11 epics) |
| **Sprint Status** | Dev tracking | [docs/sprints/sprint-status.yaml](docs/sprints/sprint-status.yaml) | ✅ Current |
| **Retrospectives** | BMAD-compliant epic retros | [docs/sprints/](docs/sprints/) | ✅ 6 retros complete |
| **Architecture Index** | Architecture documentation hub | [docs/architecture/index.md](docs/architecture/index.md) | ✅ Production-ready |
| **Features Index** | Features documentation hub | [docs/features/index.md](docs/features/index.md) | ✅ Production-ready |
| **Performance Index** | Performance optimization hub | [docs/performance/index.md](docs/performance/index.md) | ✅ Production-ready |
| **Sprints Index** | Sprint & epic documentation hub | [docs/sprints/index.md](docs/sprints/index.md) | ✅ Production-ready |
| **Project Audit** | Comprehensive project assessment | [docs/PROJECT-AUDIT-2025-12-09.md](docs/PROJECT-AUDIT-2025-12-09.md) | ✅ Complete (A- grade) |

**Completed Retrospectives:**
- [Epic 1: Self-Hosted Foundation](docs/sprints/epic-1-retro-2025-11-17.md) - ✅ Done (100% story completion)
- [Epic 2: Persistent Memory Backbone](docs/sprints/epic-2-retro-2025-11-26.md) - ✅ Done (5/5 stories)
- [Epic 3: Intelligent RAG Query Engine](docs/sprints/epic-3-retro-2025-11-29.md) - ✅ Done (4/4 stories)
- [Epic 4: Council of Ricks Multi-Agent](docs/sprints/epic-4-retro-2025-12-09.md) - ✅ Done (14/14 stories, 91% speedup)
- [Epic 4-5: ARCHES Cognitive Stabilization](docs/sprints/epic-4-5-retro-2025-12-09.md) - ✅ Done (10/10 stories, A+ architecture)
- [Epic 9: Political Governance](docs/sprints/epic-9-retro-2025-12-09.md) - ✅ Done (5/5 stories, machine democracy)

All supporting brainstorming/research notes live under [docs/archive/](docs/archive/).

---

## Delivery Workflow

The repo follows the BMAD method (Method track):
1. **Analysis & Planning:** Completed via brainstorming → PRD → architecture.  
2. **Solutioning:** Epics, test-design, implementation readiness.  
3. **Implementation:** Sprint tracking plus `create-story`, `story-ready`, `dev-story`, `code-review`, `story-done` workflows.  
4. **Autonomy:** Capability registry + BMAD invocation ensures new features are scoped, implemented, and hot-reloaded safely.

Use `.bmad/bmm/workflows/...` to rerun any stage. The workflow status YAML keeps the single source of truth for what’s done vs. pending.

---

## Sprint Tracking

`docs/sprints/sprint-status.yaml` enumerates:
- `epic-{n}` entries with status (`backlog`, `contexted`).  
- Story keys (e.g., `1-1-compose-stack-service-contracts`) with BMAD state machine values.  
- Retrospective placeholders per epic.

Update the file by running the sprint-planning workflow or editing statuses as stories progress (never downgrade).

---

## Quality & Test Strategy

Outlined in `docs/test-design-system.md`:
- **Gates:** G1 (foundation) through G7 (autonomy) with mandatory test evidence.  
- **Automation:** Pytest + coverage, ruff/mypy, structured logging assertions, provider ledger reconciliation, cron job monitoring.  
- **Latency & Cost SLOs:** 2s RAG P95, 100ms retrieval, provider ledger accuracy ±1%.  
- **UX Baseline:** Minimal OpenAI-style single chat pane ready for FR9 stories.  

These requirements must be met before marking any story “done”.

### Boot Diagnostics (`jarvis doctor`)

Install CLI dependencies locally:

```bash
pip install typer rich
```

Run diagnostics:

```bash
python -m jarvis.cli.doctor run
python -m jarvis.cli.doctor run --json
```

The command checks Docker services, Postgres readiness, Qdrant HTTP health, and workspace mount writes, exiting non-zero when issues are detected.

---

## Roadmap & Next Steps

### Active Development (v2.5.x)

**Epic 11: Sovereign Identity Layer** (In Progress)
- Story 11-1: Keycloak OAuth2/OIDC integration
- User context propagation across all API endpoints
- Privacy-aware cognitive traces
- Role-based access control mapping (governance roles → Keycloak roles)
- **Status:** 🏗️ Story 11-1 in-progress

**Epic 8-8: Epistemic Autonomy** (Dormant - Refinement Phase)
- Autonomous evolution capability unlocked
- Intentionally paused while Epic 9 & 11 refine system boundaries
- Will resume post-Epic 11 completion to enable full automation
- **Status:** ⏸️ Dormant (strategic pause)

### Backlog Priorities

**Epic 5: Cost-First LLM Router**
- Dynamic provider selection based on cost + availability
- Free-tier exhaustion detection and fallback
- Cost SLO enforcement (default: $0.50/day)
- Prep tasks identified in [docs/sprints/epic-5-prep-plan.md](docs/sprints/epic-5-prep-plan.md)

**Epic 6: Developer-Grade CLI & Automation**
- Enhanced CLI with shell completion, history, and aliases
- Automation-friendly output formats (JSON, YAML, CSV)
- Scriptable workflows for CI/CD integration

**Epic 7: Knowledge Expansion via Web Intake**
- MCP tools already enable research (Epic 4.8 delivered this early)
- May consolidate into Epic 6 or deprioritize

**Epic 10: Time-Decay Memory Continuum**
- 60-year memory architecture with tiered storage
- MongoDB/Timescale integration for historical data
- Automatic memory archival and retrieval

### Documentation Priorities (This Week)

**Critical Updates:**
- ⚠️ Update PRD to v2.5 (add FR11-FR14, mark Growth Phase items DONE)
- ⚠️ Update Architecture to v2.5 (add ARCHES, Governance, Observability sections)
- 📋 Deprecate docs/README.md → redirect to docs/index.md

**Code Quality:**
- 🏗️ Refactor governance_legacy.py (1,994 LOC → split into 5 modules)
- 📁 Move root scripts to organized folders (bootstrap_governance.py, simulate_governance_v1.py, etc.)

### Sprint Replanning

- Review [docs/PROJECT-AUDIT-2025-12-09.md](docs/PROJECT-AUDIT-2025-12-09.md) for detailed assessment
- Update sprint plans based on Epic 9 & 11 learnings
- Reassess Epic 8 vs Epic 5 priority post-Epic 11

For BMAD-specific automation guidance, see [README_BMAD.md](README_BMAD.md).

---

## Query Command & Citations (Epic 3)

`jarvis query` implements a RAG loop over Qdrant + PostgreSQL and returns both a human‑readable answer and a machine‑readable JSON envelope.

### Human Output

```bash
jarvis query "How does hybrid retrieval work?"
```

Produces:

```text
================================================================================
📝 ANSWER
================================================================================
...LLM answer text with [1], [2] style references...

--------------------------------------------------------------------------------
📚 SOURCES
--------------------------------------------------------------------------------
[1] score=0.950
    docs/architecture.md (section: Hybrid Retrieval Strategy)

[2] score=0.873
    /root/.jarvis/knowledge/insights/2025-11-20_to_2025-11-27-insights.md

--------------------------------------------------------------------------------
🔧 openrouter (google/gemini-2.0-flash-exp:free) | 512 tokens | $0.0000
```

Each citation line includes:
- A numbered id `[n]`
- A filename (workspace‑relative where possible)
- Optional logical section
- The retrieval score (semantic / hybrid fused score)
- Domain information when no file is present (e.g. `domain: jarvis-conversations`)

If no context is retrieved, the CLI prints:
- `⚠️  No relevant context found in memory.`
- A tip on using `jarvis memory add` instead of fabricating citations.

### JSON Envelope

```bash
jarvis query "How does hybrid retrieval work?" --json-output
```

Returns a JSON object:

```json
{
  "query": "How does hybrid retrieval work?",
  "response": "...LLM answer...",
  "sources": [
    {
      "id": 1,
      "content": "This document describes a hybrid retrieval edge case with BM25 and vector search.",
      "source_file": "docs/architecture.md",
      "section": "Hybrid Retrieval Strategy",
      "domain": "jarvis-core",
      "relevance_score": 0.95,
      "score": 0.95,
      "chunk_id": "chunk-123",
      "hash": "0c74cbd3a8bb2543..."
    }
  ],
  "metadata": {
    "llm_provider": "openrouter",
    "model": "google/gemini-2.0-flash-exp:free",
    "total_tokens": 512,
    "cost_usd": 0.0
  }
}
```

The `sources[]` array provides structured provenance for MCP tools and other automation:
- `id`: Citation index (1‑based)
- `source_file`: Workspace‑relative path when available
- `section`: Logical section / heading
- `domain`: Retrieval domain (`jarvis-core`, `jarvis-conversations`, `jarvis-insights`, etc.)
- `relevance_score` / `score`: Retrieval score (float)
- Optional `chunk_id` and `hash` for linking back to stored chunks
