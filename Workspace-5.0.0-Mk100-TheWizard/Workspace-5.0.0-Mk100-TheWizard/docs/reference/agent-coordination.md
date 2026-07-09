# Agent & Tool Coordination (BMAD)

This document explains how the BMAD agents, MCP server, and supporting services (Postgres, Qdrant, Redis) are coordinated in this workspace and how to operate the stack safely.

## Goals

- Provide deterministic startup/shutdown instructions so agents come up cleanly.
- Ensure DB migrations and extensions (pgcrypto) are applied before using DB-side features.
- Expose a health endpoint that indicates whether DB-side UUIDs are available.
- Keep secrets out of the repo and instruct operators how to supply them.

## Key endpoints and signals

- MCP health: `GET /mcp/health` → `{"status":"ok","pgcrypto": <true|false>}`
  - `pgcrypto: true` means server-side UUID generation is available.
  - `pgcrypto: false` means the runtime will fall back to Python `uuid.uuid4()` defaults.

- MCP ping: `GET /mcp/ping` → simple liveness check

- MCP message logging: `POST /mcp/log_message` → persists messages into the Jarvis conversation store
  - Request body:
    ```json
    {
      "agent": "codex-dev",
      "role": "assistant",
      "content": "Current diff looks good, next step is to run pytest.",
      "conversation_id": "optional-existing-uuid"
    }
    ```
  - Response body:
    ```json
    {
      "conversation_id": "uuid-of-conversation",
      "message_id": "uuid-of-message"
    }
    ```
  - If `conversation_id` is omitted, a new conversation row is created and returned.

## Startup sequence (recommended)

1. Start infrastructure: `docker compose up -d` (Postgres, Redis, Qdrant, jarvis).
2. Create db extensions and run migrations:
   - Create `pgcrypto` (if not already present):
     - `docker exec jarvis-postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"`
   - Run Alembic migrations inside the app container:
     - `docker exec jarvis-app bash -lc "cd /workspace && alembic upgrade head"`
3. Start MCP server (single instance) inside `jarvis-app`:
   - Recommended (from host):
     - `docker exec jarvis-app bash -lc "PYTHONPATH=/workspace/src python -m uvicorn src.jarvis.mcp_server:app --host 0.0.0.0 --port 8001"`
   - For quick dev convenience, use `scripts/run-mcp-server.ps1` which starts the server and prints the health endpoint.
4. Confirm health: `curl -sS http://127.0.0.1:8001/mcp/health` → expect `pgcrypto: true` after migrations and extension created.

## Shutdown / restart guidance

- To ensure a clean restart and avoid multiple MCP processes:
  - `docker restart jarvis-app` (preferred) or explicitly kill any uvicorn workers before starting a new one.
  - Avoid running multiple background uvicorn processes in the same container — prefer single process managed by the container runtime.

## Roles & responsibilities for agents

- BMAD agents (files under `.bmad/core/agents`) coordinate high-level workflows and orchestrations.
- The MCP server exposes endpoints used by agents for health, workflows, and tool execution.
- Database is authoritative storage for conversations/messages. Ensure migrations are run before agents start performing writes.

## Mandatory memory logging policy

To keep Jarvis's memory complete and consistent across tools:

- Every agent or tool (Codex, Claude, Gemini, BMAD agents, local scripts) **MUST** log significant user/assistant turns to Jarvis via `POST /mcp/log_message`.
- For each logical session:
  1. First turn: call `/mcp/log_message` **without** `conversation_id` and persist the returned `conversation_id` in the client/tool state.
  2. Subsequent turns: call `/mcp/log_message` with the same `conversation_id`, setting:
     - `agent` – stable agent identifier (e.g., `codex-dev`, `claude-dev`, `gemini-dev`, `jarvis-cli`).
     - `role` – `"user"` or `"assistant"`.
     - `content` – full message text (no truncation).
- Tools that act on the workspace (refactors, migrations, infra changes) should log a short summary message before or after execution, so Jarvis can reconstruct the reasoning behind code changes.

## Secrets

- All credentials must be provided via environment variables or your CI secret store.
- Example env var names: `POSTGRES_PASSWORD`, `OPENROUTER_API_KEY`, `TOGETHER_API_KEY`.

## Dev utilities

- `scripts/check_pgcrypto.py` — quick check from inside `jarvis-app` whether `pgcrypto` is visible.
- `scripts/force_engine_check.py` — forces the SQLAlchemy engine construction and prints cached `_pgcrypto_available`.
- `scripts/run-mcp-server.ps1` — PowerShell helper to start MCP locally and print health.

## BMAD coordination notes

- When multiple agentic processes or tools are developed in parallel, use the following practices:
  - Coordinate port usage and service names in `docker/docker-compose.yml`.
  - Each agent should register a health-check endpoint or use the MCP `/mcp/agents` listing.
  - Use `README_BMAD.md` and this `docs/agent-coordination.md` as the source-of-truth for operational steps.

## Multi-agent & multi-tool coordination (BMAD etiquette)

- Ownership: Each agent or tool working on repository changes must create a short PR or draft change note describing intent and files to change. Do not push large changes without creating a PR and notifying the BMAD channel.
- Single-writer policy for files: When multiple agents modify the same operational files (docker-compose, entrypoints, migrations), coordinate via an issue/PR so changes are reviewed and merged in sequence.
- Documentation-first: All functional changes (new endpoints, migrations, runbook changes) must be documented in `docs/` before or alongside the code change. This avoids hidden runtime behavior.
- Health and readiness: Agents must add or update health endpoints for new services and add a short note in `docs/agent-coordination.md` explaining the check.
- Secrets & vaults: No secret values in commits. Use environment variables and update `.env.example` or `config/mcp.json` (template) to document required vars.
- Communication: Use the repository issues board or PR review comments for coordination. Tag the BMAD lead (`@ABastos20`) for final approvals when infrastructure changes are involved.

These guidelines help multiple agents and tools collaborate without stepping on each other's changes. Follow them strictly for infra, migrations, and orchestration updates.

---

If you want, I can also add an example `docker-compose.override.yml` that starts the MCP server as the jarvis container's `command` so the container starts it automatically.
