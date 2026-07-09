# JARVIS Full Documentation

This document collects the operational, development, and architecture notes for the JARVIS project.

## Overview
- BMAD-driven multi-agent architecture with MCP server as local orchestration gateway.
- Persistent store: PostgreSQL (conversations/messages via SQLAlchemy + Alembic).
- Vector store: Qdrant (for embeddings, retrieval).
- Cache: Redis (session state and ephemeral caches).

## Architecture Documentation

For comprehensive architectural references, see:

- **[JARVIS Memory Architecture](architecture/jarvis-memory-architecture.md)** - Complete cognitive knowledge system architecture including:
  - 4 Memory Arches (knowledge atoms, domain taxonomy, pipeline, retrieval)
  - 6 Cognitive Patterns (how JARVIS thinks)
  - Iteration timeline and learnings (what worked, what didn't)
  - Cross-links between domain taxonomy and memory
  - 8 Operational runbooks
  - Future enhancement roadmap

- **[Memory Pipeline Flow Diagrams](architecture/memory-pipeline-flow.md)** - Visual representations including:
  - Complete knowledge flow (ingestion → retrieval → answer)
  - Domain classification decision tree
  - Document profiling (majority vote)
  - Retrieval strategy comparison (semantic, keyword, hybrid, expanded)
  - Cognitive pattern visualizations
  - 6-layer architecture stack
  - Evolution timeline and cost/quality trade-offs

- **[Domain Taxonomy](architecture/domain-taxonomy.md)** - Complete domain classification framework:
  - 166 domains across 12 disciplines
  - 881 keyword heuristics
  - Hierarchical breakdown by category
  - Validation rules and maintenance guidelines
  - Coverage analysis and statistics

- **[Production Enhancements (2025-12-02)](architecture/enhancements-2025-12-02.md)** - 10 production-grade improvements:
  - #1: Auto-Learning Heuristics (reduce LLM costs 50%)
  - #2: Domain Relationship Graph (smarter retrieval)
  - #3: Interactive Memory Dashboard (real-time visibility)
  - #4: Automated Health Monitoring (proactive alerts)
  - #5: Domain Evolution Tracking (knowledge growth over time)
  - #6: Enrichment Quality Scoring (optimize LLM spend)
  - #7: Smart Re-ingestion (automatic file watching)
  - Complete integration architecture and CLI commands

These documents provide the foundational understanding of JARVIS memory system - how knowledge is ingested, classified, stored, and retrieved to produce intelligent, citation-backed answers.

## Running the stack
1. Ensure Docker is available and you have the project checked out.
2. Start the stack:

```powershell
cd <repo-root>
docker compose -f docker/docker-compose.yml up -d --build
```

3. Confirm services are healthy:

```powershell
docker ps --filter "name=jarvis" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

4. Apply DB extension and migration if needed:

```powershell
# create pgcrypto if missing
docker exec jarvis-postgres psql -U ${POSTGRES_USER:-jarvis} -d ${POSTGRES_DB:-jarvis} -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
# run migrations
docker exec jarvis-app bash -lc "cd /workspace && alembic upgrade head"
```

## MCP server
- The container runs the MCP server (Uvicorn) as the `jarvis` service command. This ensures a single managed process.
- Health endpoints:
  - `GET /mcp/ping` — liveness
  - `GET /mcp/health` — returns `{ "status": "ok", "pgcrypto": <bool> }`

## DB UUID strategy
- Models use `server_default=func.gen_random_uuid()` and `default=uuid.uuid4` as a fallback.
- The app attempts to enable `pgcrypto` on engine creation; if it cannot, it logs and falls back.
- Alembic migration includes `CREATE EXTENSION IF NOT EXISTS pgcrypto;` for fresh DBs.

## Development utilities
- Dev scripts (moved to `dev/`):
  - `dev/check_pgcrypto.py` — check extension visibility from app container
  - `dev/force_engine_check.py` — force engine create and check cache
  - `dev/test_mcp_health.py` — a TestClient harness for the MCP server
  - `dev/run-mcp-server.ps1` — dev helper to run MCP locally

## CI and deployment notes
- Add a CI job to run `alembic upgrade head` on a dedicated DB and then curl `/mcp/health` to assert `pgcrypto` availability if required by tests.
- Inject secrets via CI secret store (GitHub Actions secrets) only, never in code.

## Logging and observability
- Startup logs indicate whether DB-side UUIDs are active.
- Consider exporting logs with a structured logger and configuring retention/forwarding to your observability stack.

## Next story (implementation tasks)
See docs/next_story.md for the next development story and acceptance criteria.

## Query Results & Citations

The query CLI and API expose retrieval provenance so downstream tools and MCP clients can reason about where answers came from.

### SearchResult Shape

Core retrieval functions (`search_memory`, `keyword_search`, `hybrid_search`, `expanded_search`) return `SearchResult` objects with:

- `text: str` – chunk text
- `score: float` – retrieval score (semantic or fused)
- `source_file: Optional[str]` – workspace‑relative path when available
- `section: Optional[str]` – logical section/heading
- `domain: Optional[str]` – logical domain (`jarvis-core`, `jarvis-conversations`, `jarvis-insights`, etc.)
- `metadata: dict` – additional fields such as:
  - `chunk_id`
  - `hash`
  - per‑mode scores (`semantic_score_norm`, `keyword_score_norm`)
  - fusion metadata (`rrf_score`, `fusion_strategy`, `expansion_count`)

### CLI JSON Envelope

`jarvis query --json-output` returns:

```json
{
  "query": "...",
  "response": "...",
  "sources": [
    {
      "id": 1,
      "content": "...chunk text...",
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

This schema is the contract for MCP tooling and other automation:
- Use `sources[]` to reconstruct the context window used by the LLM.
- Use `chunk_id`/`hash` for deep links into the underlying memory store.
- Use `relevance_score`/`score` for ranking, filtering, or thresholding in downstream workflows.

### Conversation Provenance Storage

When MCP clients or API consumers persist assistant messages, they can attach the same `sources[]` array as
`citation_provenance` on the `messages` table (JSONB column). This allows Jarvis to answer questions like:

- Which files are cited most often over a given period?
- Which domains (`jarvis-core`, `jarvis-insights`, etc.) drive most answers?

The `jarvis analytics citations` CLI command reads recent messages with non‑null `citation_provenance` and
aggregates counts by `source_file` or `domain`, returning a JSON payload suitable for dashboards or further
automation.

## Web Chat UI & /api/chat (FR9 Slice)

Jarvis now exposes a simple web chat interface and a corresponding REST endpoint that reuse the same RAG engine as the CLI, while persisting conversations into Postgres.

### /api/chat – Chat Endpoint

- **Path:** `POST /api/chat`
- **Code:** `src/jarvis/api/chat.py`, schemas in `src/jarvis/api/schemas.py` (`ChatRequest`, `ChatResponse`).
- **Request (`ChatRequest`):**
  - `message: str` – user message.
  - `conversation_id: Optional[UUID]` – existing conversation id (new conversation is created when omitted).
  - `user_id: Optional[str]` – logical user label (the web UI uses `"web-ui"`).
  - `provider: str` – LLM provider (`"auto"` by default, uses cost-first router).
  - `source: Optional[str]` – optional domain hint (e.g. `jarvis-core`, `jarvis.conversations`, `gd.generative_drive`).
  - `k: int` – top-k context chunks (1–20, defaults to 10).
  - `max_tokens: int` – LLM max output tokens.
  - `retriever: Optional[str]` – `semantic` \| `keyword` \| `hybrid` (defaults from `settings.query`).
  - `weight: Optional[float]` – semantic weight for hybrid.
  - `strict_mode: bool` – when `true`, disables creative fallback and only answers from retrieved context.
  - `expand: Optional[int]` – query expansion count (0–5). When >0, uses `expanded_search`.

Endpoint behaviour:

- Loads query defaults from `jarvis.config.load_settings()` (`default_retriever`, `default_weight`, expansion flags).
- Resolves effective parameters (k, retriever, weight, expand, strict) similar to `jarvis query`.
- Calls retrieval:
  - When `expand > 0`, uses `expanded_search` (multi-query + RRF fusion).
  - Else uses `search_memory` \| `keyword_search` \| `hybrid_search` depending on `retriever`.
- Builds the same system + user prompt as the CLI, including strict-mode rules.
- Calls `call_llm` with the cost-first router (`provider="auto"` by default).
- Constructs `sources[]`:
  - Each entry carries `id`, `content`, `source_file`, `section`, `domain`, `relevance_score`/`score`, and optional `chunk_id`/`hash` from Qdrant payload metadata.
- Persists conversation:
  - Ensures a `Conversation` row exists (either the provided `conversation_id` or a new one for the current user).
  - Writes a `Message` row for the user (`role="user"`).
  - Writes a `Message` row for the assistant (`role="assistant"`) with:
    - `content` = LLM answer,
    - `provider`, `model`, `token_count`, `cost_usd`,
    - `citation_provenance` = JSON copy of `sources[]`.
- **No-context behaviour:**
  - Always logs the user message.
  - If `strict_mode=true` and retrieval returns no results:
    - Returns `status="insufficient_context"`, `response=None`, `sources=[]`.
  - If `strict_mode=false`:
    - Enters "creative mode": builds a dialog-only prompt from recent conversation history (up to ~8 turns), calls LLM with a lighter system prompt, and returns an answer not bound to RAG snippets (no citations).

### /chat – Web Chat UI

- **Path:** `GET /chat`
- **Code:** inline HTML/CSS/JS in `src/jarvis/api/app.py`.
- **Purpose:** BMAD-flavoured chat console for live interaction with Jarvis over local memory.

Key UI elements:

- **Conversation list (left sidebar):**
  - Uses `GET /api/conversations?limit=20` (implemented in `src/jarvis/api/conversations.py`) to list recent conversations, ordered by `updated_at`.
  - Each item shows:
    - Last message snippet (title),
    - Message count,
    - Active conversation highlighting.
  - A `+ New` button clears the active conversation id and starts a new thread (DB rows are kept intact).

- **Chat pane (main panel):**
  - Replays history for the active conversation via `GET /api/conversations/{id}?page_size=100`.
  - Renders messages as:
    - `system` → dashed bubble,
    - `user` → right-aligned green bubble,
    - `assistant` → left-aligned dark bubble.
  - When assistant messages include `citation_provenance`, a `Sources:` strip is rendered under the bubble using that JSON.

- **Input controls:**
  - A `textarea` plus `Send` button.
  - `strict` checkbox and `domain` text field wired into the `/api/chat` payload as `strict_mode` and `source` respectively.
  - Conversation id is kept in `localStorage` (`jarvis_conversation_id`); on reload the UI re-attaches to the same thread.

- **Citation balloon:**
  - Below each assistant message, `Sources:` chips are rendered from either:
    - `data.sources` (for live `/api/chat` responses), or
    - `msg.citation_provenance` (when reloading history).
  - Each chip displays `[id] domain s=score` (or file path when no domain).
  - On hover, a small fixed-position balloon shows:
    - `source_file` and `section` when available, optionally with `chunk_id` hint,
    - A short preview of the chunk text.

### Domain Bias for Conversations (`jarvis.conversations`)

To better surface GPT export–style executive summaries and long-form context, `search_memory` has a heuristic bias:

- When no explicit `source` domains are passed:
  - `infer_query_domains()` now defaults to `["jarvis.conversations"]` as the primary hub, rather than a generic conversations domain.
  - This ensures questions like "mosquitoes", "Ella Al-Shamahi", or "executive summary" preferentially search the GPT export domain, where high-level summaries are stored.

Together with the slightly higher `k` + `expand` defaults for the web chat, this makes the `/chat` console feel like it is "speaking from" your own GPT history and architectural exports, not just raw documentation.
