# JARVIS System – Test & UX Design (Method Track)

**Date:** 2025-11-17  
**Owner:** Ariel (Test Architect)  
**Scope:** Implementation readiness gate for Epics 1–6 (MVP CLI) with forward-looking notes for Epics 7–10

---

## Purpose & Quality Targets

- **Controllability:** Every autonomous or long-running workflow (query engine, cost router, BMAD invocation) must expose deterministic entry/exit points plus manual override switches.  
- **Observability:** All components emit structured JSON logs (structlog) with correlation IDs, latency metrics, and provider usage to satisfy FR3/FR6/FR8 requirements.  
- **Reliability:** Critical paths (Compose bootstrap, memory ingestion, RAG queries, multi-agent aggregation) maintain ≥99% success rate under typical developer workloads; failure modes default to safe fallbacks (e.g., single-agent responses if Council fails).

Test harness references:
- CLI entry points (`jarvis doctor`, `jarvis query`, `jarvis memory`, `jarvis personas`, `jarvis cost`, `jarvis dev`).  
- API/MCP endpoints (query, memory search, cost reporting) for automated assertions.  
- Background jobs (cron templates) for ingestion and insight compilation.

---

## Environment & Tooling

| Layer | Tooling | Notes |
|-------|---------|-------|
| Container stack | Docker Compose (services: jarvis-app, PostgreSQL 18.1, Qdrant 1.15.5, Redis) | `docker compose up --build` baseline; integration tests run inside jarvis-app container. |
| Language/Test runner | Python 3.13, pytest, coverage.py | Mandatory for Stories 1.1–1.4, 2.x, 3.x, 4.x, 5.x, 6.x, 8.3. |
| Lint/Static analysis | ruff + mypy | Gate before hot-reload per Story 8.3. |
| Observability | structlog JSON logs, optional OpenTelemetry exporters | Replay tests assert log completeness (request_id, provider, latency). |
| Data fixtures | PostgreSQL + Qdrant seed scripts | Provide repeatable datasets for RAG regression suites. |

---

## Test Strategy by Capability

### 1. Foundation & Workspace Ops (Epic 1 / FR5)

- **Smoke:** `jarvis doctor` verifies Docker services, migrations, workspace mount.  
- **Negative:** Simulate missing `.env` entries; expect clear error message and non-zero exit.  
- **Security:** Validate host workspace mount respects `.gitignore` (no ingestion of restricted files).  
- **Config:** Unit-test pydantic settings schema to ensure secrets never logged.

### 2. Persistent Memory Backbone (Epic 2 / FR4)

- **Schema Tests:** Alembic migrations up/down with rollbacks.  
- **Ingestion Pipeline:** File fixtures (Markdown, PDF, HTML) run through converter; assert chunk metadata and embedding counts.  
- **Retrieval:** Query filters (persona, date range) return deterministic sets; verify <100 ms DB query latency under sample load.  
- **Cron Insights:** Mock `jarvis memory compile` weekly job; assert outputs stored to `~/.jarvis/knowledge/insights`.

### 3. RAG Query Engine (Epic 3 / FR1)

- **End-to-End:** `jarvis query "What is Qdrant?"` with seeded memory should output citations referencing known chunks.  
- **Hybrid Retrieval:** Toggle semantic vs hybrid vs keyword to ensure weighting logic works; include regression for weighting parameter validation.  
- **Latency:** Instrument response time and fail tests if >2s P95 with sample dataset (enforced via pytest markers).  
- **Query Expansion:** Validate multi-query fusion dedupes overlapping chunks and logs expansion set used.

### 4. Council of Ricks (Epic 4 / FR2)

- **Persona Registry:** CRUD commands for personas; verify weights sum to 100% and invalid configs are rejected.  
- **Parallel Invocation:** Mock providers to ensure concurrency stays within rate limits; confirm fallback to single agent if one fails.  
- **Weighted Voting:** Deterministic tests covering normal, tied, and override cases.  
- **Override Logging:** When user selects alternate persona, logs include override metadata for audit.

### 5. Cost-First LLM Router (Epic 5 / FR3)

- **Provider Registry:** Validate schema + secrets detection; simulate missing API keys.  
- **Usage Tracking:** Record tokens/costs per call; run reconciliation test matching log totals vs DB ledger.  
- **Free-Tier Failover:** Mock quota exhaustion; assert router progresses through priorities and surfaces warnings when switching to paid.  
- **Reporting:** `jarvis cost summary --period 7d` outputs JSON + Markdown table matching DB data.

### 6. Developer-Grade CLI (Epic 6 / FR6)

- **Shell Invocation:** Allowlisted commands execute; disallowed commands rejected with safe messaging.  
- **Git Context Awareness:** Tests confirm branch/status detection outputs sanitized information; add fixtures for clean vs dirty repos.  
- **Structured Output:** `--json` flag returns valid JSON (validated via schema).  
- **Cron Templates:** Installing/removing cron jobs modifies OS-specific config files and logs structured events.

### 7. Web Intake (Epic 7 / FR7)

- **URL Fetch:** Integration tests with mocked HTTP server; ensure robots.txt enforced.  
- **Refresh TTL:** Background job triggers re-ingestion only when content changes (hash comparison).  
- **Governance:** Allowlist/blocklist enforcement with unit tests.

### 8. Self-Improvement (Epic 8 / FR8)

- **Capability Registry:** Ensure file lock prevents race; simulate concurrent requests.  
- **BMAD Invocation:** Use fake subprocess output to validate logging + status updates.  
- **Auto-Testing:** Apply dummy patch, run pytest/ruff; verify rollback on failure and hot-reload on success.

### 9. Web Interface (Epic 9 / FR9)

- **API Contracts Only (pre-UX):** For now, ensure REST endpoints respond with data required by future UI.  
- **UX Placeholder Tests:** Confirm endpoints expose metadata for conversations, cost metrics, and personas.

### 10. Time-Decay Memory (Epic 10 / FR10)

- **Schema Consistency:** Validate ORMs for PostgreSQL/MongoDB/TimescaleDB.  
- **Migration Jobs:** Dry-run data migration with sample dataset.  
- **Temporal Query API:** Unit tests verifying correct tier selection based on timestamps.

---

## Readiness Gates

| Gate | Criteria | Responsible Stories |
|------|----------|---------------------|
| G1 – Foundation Up | Compose stack + `jarvis doctor` pass locally and in CI | 1.1–1.4 |
| G2 – Memory Ready | Schema + ingestion + retrieval tests green | 2.1–2.5 |
| G3 – RAG Ready | Query/hybrid/expansion + latency metrics verified | 3.1–3.4 |
| G4 – Council Ready | Persona registry, voting, overrides tested | 4.1–4.4 |
| G5 – Cost Controls | Provider failover + reporting validated | 5.1–5.4 |
| G6 – CLI Ops | Shell invocation, git context, structured outputs tested | 6.1–6.4 |
| G7 – Autonomy Safe | Capability registry + BMAD pipeline + auto-tests verified | 8.1–8.4 |

All gates must show passing test evidence (CI logs/screenshots) before stories are marked done.

---

## Observability Requirements

- Attach `request_id`, `workflow_id`, and `persona` fields to every log entry.  
- Expose `/healthz`, `/metrics` endpoints for Compose readiness probes.  
- Emit provider usage metrics to structured log + optional Prometheus endpoint.  
- Include fail-safe log watchers for cron tasks (memory compile, web refresh).

---

## Minimal UX Reference (FR9 Seed)

Goal: Provide just enough UX direction to keep FR9 stories grounded without over-investing before MVP.

1. **Layout:** Single-page SPA resembling classic OpenAI Chat.  
   - Left column (240px) listing past conversations (no folders, filters).  
   - Main panel with chat transcript bubbles (user right-aligned, JARVIS left).  
   - Header contains project name + cost summary badge (tokens today).  
2. **Interaction Rules:**  
   - Only one conversation active at a time; no parallel chats or plugins.  
   - Input box at bottom with send button and optional “attach workspace file” toggle.  
   - Streaming responses show citation badges inline; clicking opens source pane.  
3. **Restrictions:**  
   - No plugin marketplace, no tool picker, no multi-step automation UI.  
   - Settings modal limited to persona weight sliders and provider priorities.  
4. **Accessibility:**  
   - Respect WCAG AA contrast (dark text on light background).  
   - Keyboard shortcuts: `Cmd/Ctrl+Enter` to send, `Cmd/Ctrl+K` to switch conversation.  
5. **Future Enhancements Placeholder:**  
   - Reserve right-hand drawer for upcoming dashboards (memory, cost, agent management) but keep hidden until FR9 stories execute.

This UX stub unlocks Epic 9 story grooming while keeping scope intentionally narrow.

---

## Risk Monitoring & Test Matrix

- **Latency Regression:** Daily CI job hits staging dataset; alerts if RAG >2s or Qdrant >100 ms.  
- **Cost Drift:** Compare provider ledger vs actual usage; fail CI job if mismatch exceeds 1%.  
- **Security:** Automated scans ensure `.env`/secrets never leave container logs; run Trivy/Dependabot for Docker images.  
- **Self-Improvement:** Sandbox branch tests ensure BMAD patches never bypass CI gating; store artifacts for rollback.

Appendix spreadsheets (to be stored under `.jarvis/qa/`) will track scenarios vs test cases; link once CI pipeline is live.

---

_Prepared for BMAD Method Phase 3 → 4 readiness. Update this document as UX evolves or new epics enter scope._

