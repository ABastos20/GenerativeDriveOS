# BMAD Workspace Guide

This repository is fully aligned with the BMAD Method. Use this guide for BMAD-specific operations and refer to `README.md` for the corporate-facing overview.

---

## Quick Start (PowerShell)

```powershell
git clone https://github.com/ABastos20/Workspace.git
cd Workspace
powershell -ExecutionPolicy Bypass -File .\scripts\bmad\init-bmad.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\bmad\workflow-init.ps1
```

The initializer provisions:
- `.bmad/core/agents/jarvis-agent.md` – orchestration template.  
- `.bmad/integrations.yaml` – provider configuration.  
- `scripts/bmad/orchestrate-jarvis.ps1` – helper for launching agents/integrations.

Run `scripts/bmad/orchestrate-jarvis.ps1` to start handcrafted workflows once stories are ready.

---

## Agents & Integrations

| Asset | Purpose | Location |
|-------|---------|----------|
| `jarvis-agent.md` | Primary orchestrator | `.bmad/core/agents/jarvis-agent.md` |
| `bmad-greenfield.md` | Method track shepherd | `.bmad/core/agents/bmad-greenfield.md` |
| `bmad-master.md` | Master controller | `.bmad/core/agents/bmad-master.md` |
| Integrations config | LLM/API credentials and endpoints | `.bmad/integrations.yaml` |
| Chat modes | MCP/IDE shortcuts | `.github/chatmodes/*.chatmode.md` |

Update the integration file with actual API keys before orchestrating.

---

## MCP Server & Agentic Tools Setup

### 1. Start Jarvis MCP server

To install and run the local MCP server (no API keys required):

```powershell
python -m pip install -r requirements-mcp.txt
python src/jarvis/mcp_server.py
```

Or use the PowerShell script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup\run-mcp-server.ps1
```

This exposes:

- `GET http://127.0.0.1:8001/mcp/ping`
- `GET http://127.0.0.1:8001/mcp/health`

### 2. Register Jarvis MCP in client configs (Codex, Claude, Gemini)

Use `config/mcp.json` as a template for MCP-aware clients. Example snippet:

```jsonc
{
  "servers": {
    "jarvis": {
      "transport": "http",
      "url": "http://127.0.0.1:8001",
      "endpoints": {
        "ping": "/mcp/ping",
        "health": "/mcp/health"
      }
    }
  }
}
```

- **Codex / VS Code MCP** – add an equivalent `jarvis` entry to your MCP configuration (e.g. settings or config file).
- **Claude Desktop** – add a `jarvis` MCP server pointing at `http://127.0.0.1:8001` (transport `http`).
- **Gemini CLI** – when MCP support is enabled, configure a server named `jarvis` with the same URL and endpoints.

BMAD agents can also discover this server via `.bmad/integrations.yaml` under `mcp_servers`:

```yaml
mcp_servers:
  - name: jarvis-mcp
    type: http
    url: http://jarvis-app:8001
    health: /mcp/health
    ping: /mcp/ping
```

### 3. Log conversations and tool runs into Jarvis memory

To persist multi-agent conversations into Jarvis's Postgres-backed conversation store, call:

```http
POST /mcp/log_message
Content-Type: application/json

{
  "agent": "codex-dev",
  "role": "assistant",
  "content": "Explained hybrid retrieval implementation and tests.",
  "conversation_id": "optional-existing-uuid"
}
```

- If `conversation_id` is omitted, Jarvis creates a new `conversations` row and returns its UUID.
- If `conversation_id` is provided and exists, the message is appended to that conversation.
- If `conversation_id` is provided but does not exist, a new conversation is created with that ID.

Recommended pattern for Codex / Claude / Gemini agents:

1. On first turn, call `POST /mcp/log_message` without `conversation_id` and stash the returned `conversation_id`.
2. On every subsequent user or assistant message, call `POST /mcp/log_message` with the same `conversation_id`.
3. Optionally, schedule `jarvis memory compile` (Story 2.5) to summarize conversations into insights and ingest them into Qdrant for future RAG.

Next: Add additional Jarvis tools and resources under the MCP server as implementation matures.

Coordination note for multi-agent development:

- If you're an automated agent or tool making repository changes, create a draft PR or issue describing the change before pushing code. Link the PR to `docs/agent-coordination.md` and add a one-line summary of the runtime impact.
- Update the relevant docs (`docs/full-documentation.md`, `docs/agent-coordination.md`, and `docs/sprints/*`) together with code changes. Documentation-first reduces surprise for other agents.
- Use `dev/` for developer utilities only; do not rely on them in production container setups.

---

## Security Best Practices (Local Development)

- ALWAYS store API keys and passwords in environment variables, not in repo files. Use `.env` only for local convenience and never commit it.
- Never log secrets or API keys. Log only non-sensitive context (provider name, status codes, counts).
- Use the `.env.example` file as a template (no real secrets). Example env var names used across the repo: `OPENROUTER_API_KEY`, `TOGETHER_API_KEY`, `POSTGRES_PASSWORD`.
- Run automated secret scans on PRs (GitHub Actions added) and locally with `gitleaks` or `pre-commit` hooks.
- For CI or shared environments, inject secrets via pipeline secret storage (GitHub Secrets, Actions secrets, etc.), never plaintext.

Database UUID note:

- The project prefers DB-side UUID generation using `gen_random_uuid()` (provided by the `pgcrypto` extension) to produce compact, collision-resistant UUIDs on insert.
- The Alembic migration includes `CREATE EXTENSION IF NOT EXISTS pgcrypto;` but some managed DBs deny extension creation to non-superusers. The application will attempt a best-effort enable on startup and will fall back to Python-generated UUIDs (`uuid.uuid4`) when `pgcrypto` is unavailable.
- If you run into permission errors, either create the extension as a DB admin or rely on the Python fallback — both are supported.

Example (PowerShell) to verify extension from a psql shell:

```powershell
# connect with psql and run:
psql "postgresql://user:pass@host:5432/dbname" -c "SELECT extname FROM pg_extension WHERE extname='pgcrypto';"
```

Example (PowerShell) to set environment variables for a session:

```powershell
$env:OPENROUTER_API_KEY = "<your-key-here>"
$env:POSTGRES_PASSWORD = "<strong-password>"
```

To unset in the same session:

```powershell
Remove-Item Env:\OPENROUTER_API_KEY
Remove-Item Env:\POSTGRES_PASSWORD
```

---

## Developer Shortcuts & Helpers

### Bash Aliases

For faster workspace operations, source the aliases file:

```bash
source .bmad/aliases.sh
```

Available aliases:

| Alias | Command | Purpose |
|-------|---------|---------|
| `jq` | `docker compose exec jarvis jarvis query` | Quick query (e.g., `jq "your question"`) |
| `jqs` | `docker compose exec jarvis jarvis query --strict-mode` | Query with strict mode enabled |
| `jstatus` | `./scripts/ops/workspace_status.sh` | Check workspace status (git, stories, Docker) |
| `jrefresh` | `./scripts/bmad/bmad_refresh.sh` | Reload BMAD context (READMEs + quick-reference) |
| `jclean` | `./scripts/ops/kill_background.sh` | Clean up lingering Docker processes |
| `jlogs` | `docker compose logs -f jarvis` | Tail Jarvis container logs |
| `jshell` | `docker compose exec jarvis bash` | Open shell in Jarvis container |
| `jrestart` | `docker compose restart jarvis` | Restart Jarvis container |
| `jps` | `docker compose ps` | Show Docker services status |
| `jtest` | `docker compose exec jarvis pytest` | Run tests |
| `jcov` | `docker compose exec jarvis pytest --cov` | Run tests with coverage |

### Helper Scripts

Direct script access (no aliases needed):

```bash
./scripts/ops/workspace_status.sh  # Git branch, Epic 3 stories, Docker status
./scripts/bmad/bmad_refresh.sh     # Load BMAD context into current session
./scripts/ops/kill_background.sh   # Kill lingering docker build/compose processes
```

### Quick Reference

One-page BMAD workspace guide: [.bmad/quick-reference.md](.bmad/quick-reference.md)

For comprehensive workspace review and optimization report: [.bmad/workspace-review.md](.bmad/workspace-review.md)

---

## Workflow Shortcuts

| Phase | Workflow | Command / File |
|-------|----------|----------------|
| Planning | PRD | `docs/prd.md` |
| Solutioning | Architecture | `docs/architecture.md` |
| Solutioning | Epics | `docs/epics.md` |
| Solutioning | Test Design | `docs/test-design-system.md` |
| Solutioning | Implementation Readiness | `docs/implementation-readiness-report-2025-11-17.md` |
| Implementation | Sprint Planning | `docs/sprints/sprint-status.yaml` |
| Implementation | Story creation | `.bmad/bmm/workflows/4-implementation/create-story` |

Use `.bmad/bmm/workflows/...` as the source of truth for prompts/instructions when invoking each workflow.

---

## Jarvis Web Chat (FR1/FR4/FR9 Lab UI)

For BMAD‑style experimentation, Jarvis now ships with a lightweight web chat surface:

- **URL:** `http://localhost:8000/chat` (inside the Docker stack).
- **Backed by:** the same RAG engine as `jarvis query` plus the Postgres conversation store.

### BMAD View (Business / Model / Architecture / Delivery)

- **Business**
  - Use `/chat` as a safe lab to explore Jarvis behaviour with Raquel/Ariel and other stakeholders.
  - Capture executive‑summary style GPT exports (domain `jarvis.conversations`) as first‑class memory for decision support.

- **Model**
  - Chat messages are persisted as `Conversation` + `Message` rows in Postgres (roles `user`/`assistant`/`system`).
  - Retrieval for each turn:
    - Embeds the question,
    - Runs semantic / hybrid / expanded search over Qdrant (`jarvis-core`, `jarvis.conversations`, `gd.generative_drive`, etc.),
    - Builds a context‑aware prompt and calls the cost‑routed LLM (`provider="auto"` by default).
  - Citation provenance (`sources[]`) is attached to assistant messages as `citation_provenance` (JSONB) for analytics.

- **Architecture**
  - **Endpoints:**
    - `POST /api/chat` – chat endpoint (`src/jarvis/api/chat.py`) with `ChatRequest` / `ChatResponse` schemas.
    - `POST /api/conversations` – create conversation container.
    - `GET /api/conversations/{id}` – fetch conversation with paginated messages.
    - `GET /api/conversations?limit=20` – list recent conversations for the sidebar.
  - **UI shell:** Inline HTML/CSS/JS in `src/jarvis/api/app.py`:
    - Left sidebar: conversations list + `+ New` button.
    - Main pane: chat bubbles and per‑answer citations.
    - Controls: `strict` checkbox (librarian vs creative), `domain` filter to steer retrieval.
  - **Domain bias:** When no explicit domain is provided, the default inference favours `jarvis.conversations` so GPT‑exported executive summaries are more likely to ground answers.

- **Delivery**
  - Start stack: `docker compose -f docker/docker-compose.yml up --build -d`.
  - Open `http://localhost:8000/chat` and start a conversation.
  - Use the sidebar to switch threads; history survives container restarts as long as the Postgres volume is preserved.
  - For FR9 evolution (dashboards, monitoring), extend this UI or add new routes under `src/jarvis/api/app.py` and document in `docs/epics.md` under Epic 9.

### Primary Document Viewer (Story 4-13)

- **Purpose**: Provides a persistent, navigable view of the primary source document alongside the chat.
- **Behavior**:
  - **Dominant Source**: The most relevant document (score >= 0.45) is selected as "primary" and persists across queries until a better match is found.
  - **Persistence**: The viewer state is saved to `localStorage` and restored on page reload.
  - **Idempotent Hint**: The LLM conditionally injects a hint with a "Blue Link" (`[View full ...](http://localhost:8000/api/docs/...)`) to open the viewer.
  - **Clean Links**: Links use the `/api/docs/filename.md` format for readability and shareability.


---

## Known Issues & Fixes

### Research Mode Web Search Integration (Fixed 2025-12-03)

**Issue**: Story 4.8 (Autonomous Research Mode) was marked "done" but web search was not connected. Research executor had placeholder stubs (`search_tool=None`) instead of real Gemini web search integration.

**Fix**: Implemented complete Gemini Google Search grounding integration:
- Added `enable_search` parameter to [GoogleAIProvider](src/jarvis/llm/providers.py#L354) to enable Google Search grounding
- Created [web_search.py](src/jarvis/memory/web_search.py) module with `search_web()` and `fetch_content_from_url()` using Gemini
- Wired research executor in [chat.py](src/jarvis/api/chat.py#L603) and [query.py](src/jarvis/cli/query.py#L511) to use real Gemini web search
- Extracts grounding metadata and search URLs from Gemini responses for provenance tracking

**Requires**: `JARVIS_GOOGLE_API_KEY` or `JARVIS_GOOGLE_GENAI_API_KEY` environment variable configured.

### Null Byte Sanitization in Citation Provenance (Fixed 2025-12-03)

**Issue**: PostgreSQL JSONB fields cannot contain null bytes (`\u0000`) which may appear in web-scraped content during research mode. This caused 503 errors when storing messages with citation provenance from web sources.

**Error**: `psycopg2.errors.UntranslatableCharacter: unsupported Unicode escape sequence`

**Fix**: Added `_sanitize_null_bytes()` helper function in [chat.py](src/jarvis/api/chat.py#L52) that recursively removes null bytes from citation provenance data before database storage.

### Gemini Provider Configuration for Research Mode (Fixed 2025-12-03)

**Issue**: Research mode was routing through OpenRouter's free tier instead of using Gemini directly for web search queries, despite Gemini API key being configured.

**Root Cause**:
- `call_llm()` function in [client.py](src/jarvis/llm/client.py#L212) didn't recognize `provider="gemini"` parameter
- Research configuration defaulted to `provider="auto"` which selected OpenRouter
- GoogleAIProvider default model was invalid (`gemini-2.5` instead of `gemini-2.5-pro`)

**Fix**:
- Added "gemini" provider routing to [call_llm()](src/jarvis/llm/client.py#L303) alongside "google-ai"
- Created [ResearchConfig](src/jarvis/config/settings.py#L55) dataclass with `provider="gemini"` default
- Updated [settings.example.yaml](config/settings.example.yaml#L9) to use `provider: "gemini"`
- Fixed GoogleAIProvider default model to `"gemini-2.5-pro"` in [providers.py](src/jarvis/llm/providers.py#L338)
- Added model name sanitization to handle SDK format requirements

**Configuration**: Research mode now uses Gemini 2.5 Pro for all operations (query planning, web search, content fetch) via Google Search grounding.

### Document Viewer Dual-Mode Retrieval (Fixed 2025-12-04)

**Issue**: Document viewer failing with UUID parse error when clicking source chips in chat UI. Frontend was sending `doc_key` format but backend only accepted UUIDs.

**Error**:
```
psycopg2.errors.InvalidTextRepresentation:
invalid input syntax for type uuid: "conv::6925a61f-ab4c-832f-a139-557e89f3b910"
```

**Root Cause**: GET `/api/documents/{doc_id}` endpoint only queried by `Document.id` (UUID column), but citation provenance stores `doc_key` format with namespace prefixes (e.g., `"conv::uuid"`, `"GenerativeDrive::filename"`).

**Fix**: Implemented dual-mode document retrieval in [memory.py](src/jarvis/api/memory.py#L79):
- If `doc_id` contains `"::"` → query by `Document.doc_key`
- Otherwise → query by `Document.id` (UUID)

**Impact**: Document viewer now works for all source types (conversation citations, domain documents, ingested files).

**Epic 4.5 Context**: This issue exemplifies Story 4.5.3 (Memory Recency & Lineage Enforcement) challenges - need for unified document identification and retrieval interface across UUID and key-based systems.

### Delete Conversation Endpoint (Implemented 2025-12-04)

**Issue**: Frontend DELETE requests to `/api/conversations/{id}` returned 405 Method Not Allowed. No DELETE endpoint existed in the conversations API.

**Root Cause**: [conversations.py](src/jarvis/api/conversations.py) only implemented GET and POST endpoints. Conversation deletion functionality was missing despite frontend UI including delete buttons.

**Fix**: Implemented DELETE endpoint at [conversations.py:312](src/jarvis/api/conversations.py#L312) with:
- 200 OK status code (FastAPI requirement - 204 doesn't allow response body)
- Cascade deletion of associated messages (leverages SQLAlchemy relationship)
- Proper error handling for non-existent conversations (404)
- Returns `{"status": "deleted", "conversation_id": "..."}` for client confirmation

**Database Schema**: Cascade delete works via [Conversation.messages](src/jarvis/database/models.py#L61) relationship with `cascade="all, delete-orphan"`.

### Document 404 Errors - Qdrant/Postgres Sync Gap (Diagnosed 2025-12-04)

**Issue**: Document viewer returns legitimate 404 errors for certain doc_keys that appear in citation_provenance:
- `file::/workspace/docs/gptExportNEW/memory.core.md`
- `conv::6925a61f-ab4c-832f-a139-557e89f3b910`

**Root Cause**: Mismatch between Qdrant vector store and Postgres Document table:
- **Qdrant chunks** contain doc_keys in metadata (from old ingestions)
- **Postgres Document table** doesn't have corresponding full documents
- **citation_provenance** stores doc_keys from Qdrant search results
- When user clicks source chip, frontend requests document that doesn't exist in Postgres

**Diagnosis**:
- Conversation `6925a61f-ab4c-832f-a139-557e89f3b910` was deleted or never existed
- File `/workspace/docs/gptExportNEW/memory.core.md` exists as Qdrant chunks but was never ingested into Document table
- System is correctly returning 404 - documents genuinely don't exist

**Epic 4.5 Context**: This is a **core Epic 4.5 problem** exemplifying:
- **Story 4.5.3** (Memory Recency & Lineage Enforcement): Stale references in vector store
- **Story 4.5.4** (Retrieval Saturation Filter): Returning chunks from non-existent source documents
- **Story 4.5.6** (Cognitive Trace Log): Need for tracking document lifecycle and sync status

**Future Solutions** (post-4.5):
1. Implement document lifecycle tracking (ingestion → chunking → deletion)
2. Add Qdrant cleanup when documents are deleted from Postgres
3. Add `doc_exists` flag to citation_provenance for graceful frontend handling
4. Consider unified document/chunk store to prevent sync issues

---

## Operational TODOs

- [ ] Finalize provider entries and secrets in `.bmad/integrations.yaml`.  
- [ ] Flesh out `jarvis-agent.md` orchestration logic.  
- [ ] Extend `scripts/orchestrate-jarvis.ps1` with container orchestration + logging.  
- [ ] Follow the sprint status file to move stories through `drafted → done`.  
- [ ] Keep this README in sync with any BMAD automation changes.
 - [ ] Optimize hybrid/semantic retrieval latency (pre-warm models/Qdrant and tune default `k` for strict/hybrid modes).  
 - [ ] Wire Codex/Claude/Gemini (and any BMAD agents) to always call `POST /mcp/log_message` per turn, plus optional shell wrapper logging for workspace commands.  
 - [ ] Improve strict-mode UX: add config default for strict mode and structured JSON error shape for “insufficient context” responses.  

---

For broader context (vision, architecture, roadmap), read `README.md` and the documents referenced therein.
