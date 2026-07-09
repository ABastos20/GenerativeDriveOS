# AI Advisor - Epic Breakdown

**Author:** Ariel  
**Date:** 2025-11-17  
**Project Level:** BMAD Method (Greenfield)  
**Target Scale:** MVP → 60-Year Intelligence Roadmap

---

## Overview

This document decomposes the JARVIS/AI Advisor PRD into actionable epics and stories. The sequence follows the BMAD mandate: establish the containerized foundation, stand up the persistent memory spine, layer intelligent retrieval/orchestration, then extend into cost routing, CLI automation, and vision tracks (web intake, self-improvement, UI, 60-year memory). Each epic delivers user value (foundation exception applies to Epic 1), and every story is sized for a single dev agent session.

**Epic Flow (Value Focused):**
- **E1 – Self-Hosted Foundation & Workspace Ops (FR5)**: Docker Compose stack + workspace mounts give users a runnable system with Typer bootstrap diagnostics.
- **E2 – Persistent Memory Backbone (FR4)**: PostgreSQL schemas, document ingestion, Qdrant collections, and weekly insight compilation power long-lived knowledge.
- **E3 – Intelligent RAG Query Engine (FR1)**: CLI/API retrieval with hybrid search, query expansion, and source attribution makes stored knowledge actionable.
- **E4 – Council of Ricks Multi-Agent Reasoning (FR2)**: Persona registry, weighted chaos voting, and override controls enable consensus intelligence.
- **E5 – Cost-First LLM Router (FR3)**: Provider registry, usage tracking, and fallback logic minimize spend without manual babysitting.
- **E6 – Developer-Grade CLI & Automation (FR6)**: Shell-aware Typer experience, git context injection, and cron scaffolding keep workflows integrated with the user’s terminal.
- **E7 – Knowledge Expansion via Web Intake (FR7)**: URL fetch + refresh pipelines continually enrich the memory graph with external knowledge.
- **E8 – Autonomous Evolution & BMAD Handoff (FR8)**: Capability gap detection, BMAD invocation, and safe auto-testing let JARVIS evolve itself.
- **E9 – Insightful Web Experience & Telemetry (FR9)**: Browser dashboards and chat surfaces expose memory, monitoring, and agent management for visual control.
- **E10 – Time-Decay Memory Continuum (FR10)**: Tiered storage, migration jobs, and temporal queries preserve 60 years of intelligence.

---

## Functional Requirements Inventory

- **FR1 – RAG Query System**: Semantic, hybrid, and expanded queries that cite sources.  
- **FR2 – Multi-Agent Orchestration**: Council of Ricks personas, weighted chaos voting, and aggregated outputs.  
- **FR3 – Cost-First LLM Routing**: Provider registry, free-tier depletion logic, and usage/cost reporting.  
- **FR4 – Persistent Memory System**: Conversation storage, document ingestion, retrieval filters, and scheduled insight compilation.  
- **FR5 – Docker Containerization**: Multi-container Compose stack with workspace mounts and managed configuration.  
- **FR6 – CLI Integration**: Typer CLI that can invoke shell commands, stay context aware, and support cron jobs.  
- **FR7 – Web Scraping & Internet Integration**: URL fetching, parsing, and refresh-driven ingestion into the knowledge base.  
- **FR8 – Bootstrap Evolution & Self-Improvement**: BMAD agent invocation, capability registry, and autonomous testing loops.  
- **FR9 – Web Interface (Vision)**: Browser dashboard for memories, monitoring, and agent management.  
- **FR10 – 60-Year Memory with Time-Decay Compression**: Tiered storage strategy with automated migration and unified queries.

---

## FR Coverage Map

| Epic | User Value Delivered | FRs Covered |
|------|----------------------|-------------|
| E1 – Self-Hosted Foundation & Workspace Ops | User can run the full Docker stack locally with workspace access and diagnostics. | FR5 (baseline), supports FR6 bootstrap |
| E2 – Persistent Memory Backbone | Conversations and documents persist with searchable embeddings and insight jobs. | FR4 |
| E3 – Intelligent RAG Query Engine | Users query knowledge with semantic + hybrid retrieval and transparent sourcing. | FR1, FR4 handoffs |
| E4 – Council of Ricks Multi-Agent Reasoning | Multi-agent personas debate and produce consensus responses with overrides. | FR2 |
| E5 – Cost-First LLM Router | Platform automatically picks cheapest provider and tracks spend. | FR3 |
| E6 – Developer-Grade CLI & Automation | CLI mirrors developer workflows, surfaces git context, and schedules jobs. | FR6 |
| E7 – Knowledge Expansion via Web Intake | User can feed URLs/web data and keep them fresh automatically. | FR7 |
| E8 – Autonomous Evolution & BMAD Handoff | System notices gaps, asks for approval, and self-improves safely. | FR8 |
| E9 – Insightful Web Experience & Telemetry | Web UI visualizes memories, costs, and agent states. | FR9 |
| E10 – Time-Decay Memory Continuum | Knowledge survives decades with automated migration and temporal querying. | FR10 |

---

## Epic 1: Self-Hosted Foundation & Workspace Ops

Deliver a runnable Docker Compose environment with workspace mounting, configuration hygiene, and a Typer bootstrap command so the rest of the stack can be deployed repeatably.

### Story 1.1: Compose Stack & Service Contracts

As a platform operator,  
I want a reproducible Docker Compose stack with PostgreSQL, Qdrant, Redis, and the Python app,  
So that I can spin up the entire system locally in one command.

**Acceptance Criteria:**  
**Given** the user clones the repo with Docker installed,  
**When** they run `docker compose up --build`,  
**Then** all core services (PostgreSQL, Qdrant, Redis, jarvis-app) start with health checks exposed,  
**And** service logs are routed to JSON via structlog as defined in architecture.md.

**Prerequisites:** None.  
**Technical Notes:** Follow architecture stack versions (Python 3.13 base image, Qdrant 1.15.5, PostgreSQL 18.1, Redis latest). Bake Poetry install + volume caching to speed rebuilds.

### Story 1.2: Workspace Mount & File Access Controls

As a developer,  
I want the container to mount my host workspace with correct permissions,  
So that JARVIS can read/write Markdown knowledge while respecting `.gitignore`.

**Acceptance Criteria:**  
**Given** the user mounts `./` into `/workspace`,  
**When** the app ingests docs,  
**Then** only files outside `.gitignore` are auto-indexed,  
**And** writing back (e.g., `status.md`, logs) happens under `.jarvis/` with host ownership preserved.

**Prerequisites:** Story 1.1.  
**Technical Notes:** Leverage Compose `volumes` with bind mounts; use Python’s `pathlib` + gitignore parser to filter ingestion; ensure SELinux/Windows path compatibility.

### Story 1.3: Configuration & Secret Management

As an operator,  
I want configuration handled via pydantic-settings + YAML + `.env`,  
So that providers, personas, and workspace paths are validated at startup.

**Acceptance Criteria:**  
**Given** a `.env` file with LLM keys and a YAML config for personas,  
**When** the app boots,  
**Then** pydantic-settings loads and validates every field (paths, API keys, ports) with helpful errors,  
**And** secrets never appear in logs or persisted config files.

**Prerequisites:** Story 1.2.  
**Technical Notes:** Mirror architecture decision table; include schema docs for `config.yaml`; enforce UTC timezone default.

### Story 1.4: Typer Bootstrap & Diagnostics

As a CLI user,  
I want a `jarvis doctor` command that checks containers, migrations, and embeddings,  
So that I know the foundation is healthy before running intelligence workflows.

**Acceptance Criteria:**  
**Given** the stack is up,  
**When** the user runs `jarvis doctor`,  
**Then** the command validates Docker services, DB connectivity, workspace mount, and prints actionable results,  
**And** exits non-zero when a dependency is down.

**Prerequisites:** Stories 1.1-1.3.  
**Technical Notes:** Implement via Typer with health probes hitting `/healthz` endpoints and verifying Qdrant collections exist; reuse structlog formatting for CLI output.

---

## Epic 2: Persistent Memory Backbone

Implement PostgreSQL schemas, ingestion workflows, and Qdrant collections so knowledge persists and is searchable for decades.

### Story 2.1: Conversation Storage Schema

As a memory engineer,  
I want normalized PostgreSQL tables for conversations, turns, costs, and personas,  
So that every interaction is queryable with metadata.

**Acceptance Criteria:**  
**Given** migrations run via Alembic,  
**When** a new conversation occurs,  
**Then** the system stores user prompts, agent responses, timestamps (UTC), persona IDs, and cost breakdown,  
**And** indices support filtering by persona, topic, and timeframe.

**Prerequisites:** Epic 1.  
**Technical Notes:** Align columns with FR4.1; include JSONB for source attributions; enforce timezone aware fields.

### Story 2.2: Document Ingestion Pipeline

As a data librarian,  
I want a pipeline that converts uploads (Markdown, PDF, HTML) into normalized Markdown chunks,  
So that the memory store is consistent and ready for embedding.

**Acceptance Criteria:**  
**Given** a user runs `jarvis memory add path/to/file.pdf`,  
**When** ingestion completes,  
**Then** the file is converted via pandoc, chunked (semantic + fixed window), embedded, and stored with metadata,  
**And** ingestion events are logged with success/failure.

**Prerequisites:** Story 2.1.  
**Technical Notes:** Use architecture’s Markdown-first pipeline; chunk using token-aware splitter; store chunk IDs referencing source path + hash.

### Story 2.3: Qdrant Collection Initialization

As a vector engineer,  
I want a managed Qdrant collection seeded with embeddings,  
So that semantic search is consistent across restarts.

**Acceptance Criteria:**  
**Given** embeddings exist in PostgreSQL staging tables,  
**When** the provisioning command runs,  
**Then** Qdrant collections with 384-d vectors and metadata payloads are created,  
**And** health checks confirm replication parameters per architecture.

**Prerequisites:** Story 2.2.  
**Technical Notes:** Use `qdrant-client` 1.15.1; maintain configuration file for distance metric (Cosine) and write operations.

### Story 2.4: Memory Retrieval Filters & API

As an analyst,  
I want to search memories by source type, time, and persona,  
So that I can retrieve the right context for workflows.

**Acceptance Criteria:**  
**Given** stored conversations and documents,  
**When** the user runs `jarvis memory search --persona "Rickiest Rick" --since 7d`,  
**Then** the CLI returns ranked snippets with metadata filters applied,  
**And** the API exposes equivalent filters for MCP clients.

**Prerequisites:** Story 2.3.  
**Technical Notes:** Provide REST + CLI endpoints; rely on PostgreSQL for metadata filtering and join results with Qdrant IDs; ensure queries <100ms using indexes/caching.

### Story 2.5: Scheduled Memory Compilation

As a strategist,  
I want automated weekly insight jobs,  
So that I receive distilled knowledge from large conversation sets.

**Acceptance Criteria:**  
**Given** the cron job spec in docs,  
**When** `jarvis memory compile --since 7d` runs,  
**Then** it aggregates conversations, summarizes patterns via LLM, writes Markdown to `~/.jarvis/knowledge/insights`,  
**And** logs include cost + provider data for auditing.

**Prerequisites:** Story 2.4.  
**Technical Notes:** Reuse FR4.4 cron example; integrate with cost router for budget awareness; store compiled insights as ingestion-ready docs for re-query.

---

## Epic 3: Intelligent RAG Query Engine

Provide a full RAG loop so users can issue natural-language questions and receive grounded, cited answers leveraging the memory backbone.

### Story 3.1: Query Command & Response Envelope

As a knowledge worker,  
I want a `jarvis query "question"` command,  
So that I can ask anything and receive structured answers with metadata.

**Acceptance Criteria:**  
**Given** memories exist,  
**When** the user queries via CLI or MCP,  
**Then** the system embeds the query, fetches top-k context, calls the selected LLM, and returns text + cited sources,  
**And** results stream progressively to the terminal.

**Prerequisites:** Epic 2.  
**Technical Notes:** Build on Typer CLI; responses include JSON for MCP; cite chunk IDs linking back to workspace files.

### Story 3.2: Hybrid Retrieval Toggle

As a power user,  
I want to blend semantic and keyword retrieval,  
So that I can handle edge cases where BM25 outperforms pure vectors.

**Acceptance Criteria:**  
**Given** the user adds `--retriever hybrid --weight 0.7`,  
**When** the query executes,  
**Then** the system runs BM25/Postgres full-text search alongside vector search, normalizes scores, and merges results,  
**And** defaults are configurable per profile.

**Prerequisites:** Story 3.1.  
**Technical Notes:** Implement BM25 via PostgreSQL `tsvector` or Elastic fallback; include re-ranking optional step.

### Story 3.3: Query Expansion & Multi-Query Fusion

As a researcher,  
I want automatic query expansion,  
So that ambiguous prompts still retrieve relevant knowledge.

**Acceptance Criteria:**  
**Given** query expansion is enabled,  
**When** the user asks a vague question,  
**Then** the system generates alternate phrasings, retrieves for each, and fuses results with deduplication,  
**And** telemetry shows expansions used.

**Prerequisites:** Story 3.2.  
**Technical Notes:** Use cheap local LLM or heuristics for expansions; limit to configurable N to fit latency budgets (<2s P95).

### Story 3.4: Citation-First Response Formatting

As an end user,  
I want every answer to cite its sources,  
So that I can verify correctness quickly.

**Acceptance Criteria:**  
**Given** the LLM returns a response,  
**When** the CLI renders output,  
**Then** citations include filenames + line ranges + confidence,  
**And** choosing `--json` returns structured provenance for MCP tooling.

**Prerequisites:** Stories 3.1-3.3.  
**Technical Notes:** Use Markdown footnotes referencing workspace paths; store citation metadata with conversation logs for future review.

## Epic 4: Council of Ricks Multi-Agent Reasoning (COMPLETED v2.1.0)
Enable multiple personas to debate and deliver consensus answers with transparency and override controls. **(Implemented in `src/jarvis/agents/`)**

### Story 4.1: Persona Registry & Configuration CLI

As a PM,  
I want to manage personas via YAML + CLI commands,  
So that I can tune the Council of Ricks without editing code.

**Acceptance Criteria:**  
**Given** `personas.yaml` defines agents,  
**When** the user runs `jarvis personas list/add/update`,  
**Then** personas sync to PostgreSQL and the CLI validates weight totals,  
**And** changes hot-reload without restart.

**Prerequisites:** Epic 1 config + Epic 2 schema.  
**Technical Notes:** Use pydantic for schema validation; store persona metadata in DB for audit history.

### Story 4.2: Parallel Agent Invocation

As a researcher,  
I want each persona to run independently in parallel,  
So that consensus latency stays low even with multiple agents.

**Acceptance Criteria:**  
**Given** a query with `--agents all`,  
**When** execution starts,  
**Then** asynchronous calls invoke each persona with its system prompt and weight,  
**And** partial responses stream individually before aggregation.

**Prerequisites:** Story 4.1, Epic 3 query path.  
**Technical Notes:** Use asyncio tasks; share retrieved context; enforce rate limits per provider from Epic 5.

### Story 4.3: Weighted Chaos Voting Engine

As a decision maker,  
I want weighted chaos voting to select the final response,  
So that consensus reflects persona influence.

**Acceptance Criteria:**  
**Given** persona weights sum to 100%,  
**When** agents finish,  
**Then** the system computes weighted scores, displays contributions, and selects the highest scoring answer,  
**And** ties can optionally surface multiple responses.

**Prerequisites:** Story 4.2.  
**Technical Notes:** Implement aggregator referencing FR2.2 defaults; persist vote metadata for analytics.

### Story 4.4: Response Aggregation & Override UX

As an advanced user,  
I want to review all agent responses and override the choice,  
So that I can pick a different persona answer when needed.

**Acceptance Criteria:**  
**Given** consensus output is shown,  
**When** the user runs `jarvis query --select Supportive`,  
**Then** the CLI re-renders the Supportive Rick answer with its sources,  
**And** the decision is logged with override metadata.

**Prerequisites:** Story 4.3.  
**Technical Notes:** Provide toggles in CLI + MCP; store overrides for training future heuristics.

### Story 4.5: Conversation Analytics & Provenance Storage

As a knowledge engineer,  
I want citation metadata persisted alongside conversations,  
So that I can analyze which sources drive answers and build higher-level analytics.

**Acceptance Criteria:**  
**Given** `jarvis query` is invoked and returns cited answers,  
**When** the assistant response is persisted to PostgreSQL,  
**Then** the associated message record also stores a compact representation of the `sources[]` array (filenames, sections, domains, scores, chunk IDs and hashes),  
**And** this metadata can be queried later for conversation-level analytics (e.g., “which files are used most often?”).

**Prerequisites:** Stories 3.3 & 3.4.  
**Technical Notes:** Introduce a JSONB column (or dedicated table) on the `messages` schema for citation provenance; add Alembic migration, API plumbing, and a small CLI/API read path for analytics. Ensure the storage format mirrors the existing JSON envelope schema.

### Story 4.6: Time‑Aware Retrieval & Domain Heuristics

As a knowledge engineer,  
I want retrieval to respect both topic and temporal maturity,  
So that Jarvis feels like a brain that remembers its full history but leans on its latest, converged understanding.

**Acceptance Criteria:**  
**Given** domain and tag heuristics are applied over the `knowledge` collection,  
**When** `jarvis analytics catalog-domains` and `jarvis analytics catalog-docs` run,  
**Then** chunks carry `primary_domain`, `domains`, `tags`, and document‑level fields (`doc_primary_domain`, `doc_tags`, `doc_first_seen`, `doc_last_seen`, `doc_step_count`) derived from workspace, OneDrive and GD content.  
**And** `search_memory` uses `doc_step_count` to apply a small, configurable time weight (via `JARVIS_TIME_WEIGHT_ALPHA`) that favours later/richer iterations without hiding early assumptions.

**Prerequisites:** Stories 3.3, 3.4, 4.1, 4.5.  
**Technical Notes:** Keep heuristics in `domain_heuristics.py` and telecom/cyber mappings in `heuristics/telecom_domains.py`; keep time weighting in `search.py` as a thin layer over existing scoring so it can be tuned or disabled per environment.

### Story 4.7: Web Chat Console (BMAD Lab UI)

As a BMAD practitioner,  
I want a minimal web chat console backed by the RAG engine and conversation store,  
So that I (and Raquel/Ariel) can talk to Jarvis like an OpenAI chat while staying fully grounded in our own knowledge base.

**Acceptance Criteria:**  
**Given** Docker stack is running,  
**When** I open `/chat` in a browser,  
**Then** I see a Jarvis BMAD Console with:
- A left sidebar listing recent conversations (title = last assistant message snippet, with message counts).  
- A main chat pane that replays the active conversation history.  
- An input box with `strict` and `domain` controls mapped into the RAG query (strict librarian mode + domain bias).  
- Answers that come with a `Sources:` strip under assistant messages, where hovering a chip shows a balloon with file, section, chunk id (when available), and a short preview of the chunk text.

**Prerequisites:** Epic 2, Stories 3.1–3.4, Story 4.6 (time‑aware retrieval & domain heuristics).
**Technical Notes:** Implemented via `POST /api/chat` + `GET/POST /api/conversations` and an inline HTML/JS UI in `src/jarvis/api/app.py`. Defaults bias retrieval toward `jarvis.conversations` and use slightly higher `k` + expansion for executive‑summary style chunks coming from GPT exports.

### Story 4.8: Self-Aware Memory Gap Detection & Autonomous Research

As a knowledge engineer,
I want Jarvis to autonomously detect gaps in its memory and proactively research to fill them,
So that the system evolves from passive RAG retrieval to active knowledge-seeking intelligence.

**Acceptance Criteria:**
**Given** a user query is executed against the knowledge base,
**When** Jarvis analyzes the retrieved context,
**Then** it performs a three-dimensional gap analysis:
- **Coverage Analysis**: What portion of the query is grounded vs speculative?
- **Recency Analysis**: How old is the relevant knowledge (MISSING | SPARSE | STALE)?
- **Coherence Analysis**: Do retrieved sources agree or contradict (CONTRADICTORY)?

**And** when significant gaps are detected (configurable threshold),
**Then** Jarvis enters **Research Mode**:
1. **Research Planning** (Gemini): Generate 2-5 targeted web search queries to fill the gap
2. **Multi-Query Execution**: Execute searches, fetch content, extract relevant chunks
3. **Cross-Reference Verification**: Validate findings across multiple sources
4. **Critical Integration** (Claude): Compare old vs new knowledge, detect conflicts, synthesize coherent update
5. **Temporal Memory Update**: Create versioned chunks with provenance tracking (source_type, verified_at, confidence, supersedes)
6. **User Transparency**: Present gap analysis + research summary + confidence deltas in response

**And** research activities are logged with:
- Gap type detected (MISSING | SPARSE | STALE | CONTRADICTORY)
- Queries generated and executed
- Sources evaluated and integrated
- Knowledge updates applied (with versioning)
- Cost and provider metadata

**Prerequisites:** Stories 4.5, 4.6, 4.7, Epic 3 (RAG foundation), MCP Docker server (already available).
**Technical Notes:**
- Implement `GapAnalyzer` class in `src/jarvis/memory/gap_analyzer.py` with coverage/recency/coherence scoring
- Create `ResearchPlanner` interface that leverages Gemini for query generation
- Use **MCP tooling** (`mcp__MCP_DOCKER__fetch`, `mcp__MCP_DOCKER__browser_*`) instead of building separate pipeline
- Gemini orchestrates tool calls directly - eliminates Epic 7 prerequisite!
- Add `TemporalChunkManager` for versioned memory with supersession tracking
- Integrate Claude as reasoning layer in `CriticalIntegrator` for conflict resolution
- Store research metadata in PostgreSQL for analytics (gaps detected over time, research success rate)
- Add `--enable-research` flag to CLI and `enable_research` parameter to API
- Research mode should be **opt-in** initially, with path to autonomous operation later
- Implement rate limiting and cost caps for research queries to prevent runaway spending

---

## Epic 5: Cost-First LLM Router

Give users confidence that every LLM call honors the “free-tier first” policy with transparent usage tracking and reporting.

### Story 5.1: Provider Registry & Priority Rules

As a platform admin,  
I want to configure providers with type, priority, and quota,  
So that the router knows which models to try first.

**Acceptance Criteria:**  
**Given** `providers.yaml` lists OpenRouter, Together, Gemini, etc.,  
**When** the router initializes,  
**Then** providers are validated (API keys, endpoint URLs, quotas),  
**And** missing keys disable providers gracefully.

**Prerequisites:** Epic 1 config.  
**Technical Notes:** Map schema to FR3.1; store provider metadata in DB for runtime reload.

### Story 5.2: Usage Tracking & Cost Ledger

As a finance-focused user,  
I want every API call logged with tokens and cost,  
So that I can audit spending.

**Acceptance Criteria:**  
**Given** LLM calls occur,  
**When** the router finishes,  
**Then** PostgreSQL records provider, model, tokens, estimated cost, timestamp, and request ID,  
**And** daily summaries can be generated from logs.

**Prerequisites:** Story 5.1.  
**Technical Notes:** Hook into FR4.1 tables; expose metrics to future dashboards (Epic 9).

### Story 5.3: Free-Tier Depletion Logic

As an operator,  
I want automatic failover from exhausted free tiers to backups,  
So that sessions never fail silently.

**Acceptance Criteria:**  
**Given** a provider hits its quota,  
**When** the router tries to use it,  
**Then** it marks the provider as depleted, switches to the next free-tier provider, and finally to paid providers,  
**And** emits warnings when falling back to paid options.

**Prerequisites:** Story 5.2.  
**Technical Notes:** Poll provider usage APIs; support manual override env var `JARVIS_NO_FREE_LLMS` per PRD scenario.

### Story 5.4: Cost Reporting CLI/API

As a stakeholder,  
I want commands like `jarvis cost summary --period 30d`,  
So that I can see spend trends without external spreadsheets.

**Acceptance Criteria:**  
**Given** usage logs exist,  
**When** the user requests a summary,  
**Then** the CLI renders totals by provider, free vs paid ratios, and alerts for anomalies,  
**And** the MCP resource exposes equivalent JSON for dashboards.

**Prerequisites:** Story 5.3.  
**Technical Notes:** Provide CSV export; integrate with structlog to push metrics to Observability (Epic 9).

---

## Epic 6: Developer-Grade CLI & Automation

Elevate the Typer CLI beyond queries: command invocation, git-aware context, cron scaffolding, and log-friendly outputs.

### Story 6.1: Shell Command Invocation Tooling

As a developer,  
I want `jarvis shell "git status"` style commands,  
So that JARVIS can execute and summarize shell output for me.

**Acceptance Criteria:**  
**Given** the CLI receives a shell command,  
**When** it runs inside the workspace,  
**Then** stdout/stderr are captured, summarized, and optionally attached to memory,  
**And** commands respect allowlists/denylists for safety.

**Prerequisites:** Epics 1 & 5 (for provider logging).  
**Technical Notes:** Reuse existing CLI harness; parse outputs into Markdown for ingestion if flagged.

### Story 6.2: Workspace & Git Context Awareness

As a user,  
I want JARVIS to know repo status, branch, and recent commits,  
So that responses auto-include relevant diffs.

**Acceptance Criteria:**  
**Given** the CLI runs in a git repo,  
**When** I execute queries,  
**Then** context includes current branch, dirty files, and last commit summary,  
**And** this metadata is available to workflows (e.g., create-story).

**Prerequisites:** Story 6.1.  
**Technical Notes:** Use `gitpython` or subprocess; store sanitized output in memory entries.

### Story 6.3: Structured Command Outputs

As an engineer,  
I want CLI commands to return structured JSON or Markdown tables,  
So that I can pipe them into other tools.

**Acceptance Criteria:**  
**Given** I run `jarvis query --json`,  
**When** output is produced,  
**Then** it can be parsed by `jq` (valid JSON) or as Markdown table for human view,  
**And** exit codes follow POSIX spec.

**Prerequisites:** Story 6.2.  
**Technical Notes:** Align with NFR-I2/Observability; share schema definitions for MCP compatibility.

### Story 6.4: Cron & Background Task Templates

As an ops engineer,  
I want scaffolding for cron jobs and headless execution,  
So that I can schedule queries or memory tasks safely.

**Acceptance Criteria:**  
**Given** sample cron manifests,  
**When** I run `jarvis jobs install --type memory-compile`,  
**Then** the CLI writes cron entries/log locations and ensures background commands respect logging format,  
**And** tasks can emit structured success/failure events.

**Prerequisites:** Story 6.3.  
**Technical Notes:** Provide templates for Linux/macOS/Windows Task Scheduler; integrate with Observability.

---

## Epic 7: Knowledge Expansion via Web Intake

Augment the knowledge base with external URLs and keep them fresh automatically.

### Story 7.1: URL Fetch & Parse Pipeline

As a researcher,  
I want to ingest URLs,  
So that JARVIS can reason over web articles or docs.

**Acceptance Criteria:**  
**Given** the user runs `jarvis web add https://example.com/post`,  
**When** ingestion completes,  
**Then** the system fetches the HTML (Playwright fallback), extracts the main content, cleans it to Markdown, and stores metadata (URL, fetched_at),  
**And** respects robots.txt.

**Prerequisites:** Epic 2 ingestion pipeline.  
**Technical Notes:** Use Readability-like extraction; tie into FR7.1 requirements.

### Story 7.2: Automatic Refresh & Diffing

As a maintainer,  
I want stale URLs refreshed automatically,  
So that knowledge stays current.

**Acceptance Criteria:**  
**Given** URLs have TTL metadata,  
**When** TTL expires,  
**Then** the refresh job re-fetches content, diffs old vs new chunks, updates embeddings, and logs updates,  
**And** only changed sections trigger re-embedding.

**Prerequisites:** Story 7.1.  
**Technical Notes:** Schedule via cron templates from Epic 6; store history for traceability.

### Story 7.3: Web Source Governance

As a user,  
I want controls for allowed domains and provenance,  
So that ingestion remains trustworthy.

**Acceptance Criteria:**  
**Given** allowlist/blocklist configs,  
**When** ingestion requests arrive,  
**Then** enforcement happens before fetching, and metadata clearly labels origin + refresh cadence,  
**And** the CLI warns when content violates policy.

**Prerequisites:** Story 7.2.  
**Technical Notes:** Manage lists via YAML + CLI; integrate with Observability to flag failures.

---

## Epic 8: Autonomous Evolution & BMAD Handoff

Empower JARVIS to detect missing capabilities, invoke BMAD workflows, and safely adopt the results.

### Story 8.1: Capability Registry & Gap Detection

As a self-improving agent,  
I want a capabilities.yaml registry with statuses,  
So that I can detect when a requested feature is missing.

**Acceptance Criteria:**  
**Given** the registry tracks available/in-development/backlog capabilities,  
**When** a user asks for something unimplemented,  
**Then** the system surfaces options (build now, background, backlog, workaround) with clear prompts,  
**And** selections update the registry atomically.

**Prerequisites:** Epic 6 CLI context.  
**Technical Notes:** Follow architecture Pattern 1; use file locks to avoid race conditions.

### Story 8.2: BMAD Invocation Pipeline

As a bootstrapper,  
I want JARVIS to call BMAD agents via CLI,  
So that it can request new features autonomously.

**Acceptance Criteria:**  
**Given** a capability enters “in_development”,  
**When** the user approves building now,  
**Then** JARVIS packages context (PRD, architecture, code references) and invokes `bmad-dev`/`bmad-architect`,  
**And** captures outputs under `~/.jarvis/status.md`.

**Prerequisites:** Story 8.1.  
**Technical Notes:** Stream subprocess logs; ensure errors bubble back to the user.

### Story 8.3: Auto-Testing & Safe Hot-Reload

As a guardian,  
I want automated tests + rollback before loading BMAD output,  
So that self-modifications stay safe.

**Acceptance Criteria:**  
**Given** BMAD returns patches,  
**When** they are applied in a sandbox branch,  
**Then** unit tests + linting run, failures trigger rollback, and success triggers `importlib.reload`,  
**And** results append to dev logs with success metrics.

**Prerequisites:** Story 8.2.  
**Technical Notes:** Use pytest + ruff/black; keep telemetry for success rate targets.

### Story 8.4: Improvement Tracking & Notifications

As a user,  
I want progress updates on autonomous improvements,  
So that I can trust the system.

**Acceptance Criteria:**  
**Given** improvements run in background,  
**When** states change (installing deps, running tests, completed),  
**Then** notifications stream via CLI + `jarvis status`,  
**And** transcripts (context, diffs) are archived for auditing.

**Prerequisites:** Story 8.3.  
**Technical Notes:** Reuse `.jarvis/status.md` plus CLI watchers; integrate with Observability events.

### Story 8.5: Domain Mining from Emerging Client Tags

As a System Architect,  
I want JARVIS to autonomously analyze clusters of 'GD-tags' from client interactions,  
So that I can proactively identify and suggest new client archetypes, domains, and market opportunities.

**Acceptance Criteria:**  
**Given** that JARVIS has access to a stream of "GD-tags" from client interactions,  
**When** the domain mining job runs,  
**Then** it identifies statistically significant clusters of new or co-occurring tags that do not map to existing domains,  
**And** generates a "New Archetype Suggestion" report for each cluster, including tag frequency, growth rate, and a suggested domain name,  
**And** flags these suggestions on the Epic 9 dashboard for human review and approval,
**And** a human operator can approve, reject, or modify the suggestion to create a new formal domain.

**Prerequisites:** Story 8.1 (for capability detection), Epic 9 (for dashboard integration).  
**Technical Notes:** The "keyword miner" can be a dedicated persona or a scheduled background job. Leverage existing clustering algorithms (e.g., DBSCAN, K-Means) on tag vectors. The feedback loop for approval should update the capability registry from Story 8.1.

---

## Epic 9: Insightful Web Experience & Telemetry

Provide a browser-based dashboard for memories, monitoring, and agent management built on the same APIs.

### Story 9.1: Memory Dashboard (MVP)

As a visual analyst,  
I want a web UI listing conversations, documents, and embeddings,  
So that I can explore knowledge without the CLI.

**Acceptance Criteria:**  
**Given** the user visits `http://localhost:8080`,  
**When** the dashboard loads,  
**Then** it shows searchable conversations with filters (persona, time range) and detail panes with citations,  
**And** data is served by the existing memory API.

**Prerequisites:** Epic 2 APIs.  
**Technical Notes:** Implement with a lightweight SPA (e.g., Svelte/React); reuse REST endpoints.

### Story 9.2: System Monitoring View

As an operator,  
I want to see provider usage, LLM costs, and latency metrics,  
So that I can spot anomalies early.

**Acceptance Criteria:**  
**Given** cost + telemetry data exist,  
**When** I open the monitoring tab,  
**Then** charts display token usage by provider, quota depletion timelines, and query latency trends,  
**And** alerts highlight threshold breaches.

**Prerequisites:** Epic 5 logging, Epic 3 metrics.  
**Technical Notes:** Pull data from PostgreSQL views; use WebSockets/SSE for live updates.

### Story 9.3: Agent Management Console

As a PM,  
I want to adjust personas and weights from the web UI,  
So that I can manage the Council visually.

**Acceptance Criteria:**  
**Given** persona APIs exist,  
**When** I edit a persona in the UI,  
**Then** changes validate weights, persist to DB, hot-reload the council, and log the change history,  
**And** UI prevents invalid totals.

**Prerequisites:** Epic 4 personas.  
**Technical Notes:** Reuse CLI validation logic; secure with local auth (basic token) for now.

---

## Epic 10: Time-Decay Memory Continuum

Implement the 60-year storage model with automated migration and unified temporal queries.

### Story 10.1: Tiered Storage Schema

As a data architect,  
I want schemas for PostgreSQL (recent), MongoDB (medium-term), TimescaleDB (long-term), and Redis summaries,  
So that each horizon has a home.

**Acceptance Criteria:**  
**Given** the storage strategy,  
**When** I review database schemas,  
**Then** each tier has clearly defined tables/collections/keys plus retention durations,  
**And** migrations/documentation explain when data moves.

**Prerequisites:** Epics 2 & 5.  
**Technical Notes:** Define connectors + ORM models; include infrastructure as code (Compose/K8s) placeholders.

### Story 10.2: Automated Migration Jobs

As an ops engineer,  
I want scheduled jobs that move data across tiers,  
So that storage stays optimized without manual work.

**Acceptance Criteria:**  
**Given** retention policies,  
**When** data hits thresholds,  
**Then** background jobs copy/transform it to the next tier (e.g., summarize to MongoDB), verify integrity, and delete/mark old records,  
**And** failures alert via Observability.

**Prerequisites:** Story 10.1, Epic 6 cron scaffolding.  
**Technical Notes:** Use airflow-like orchestrator or cron + Python tasks; include hashing to ensure fidelity.

### Story 10.3: Temporal Query API

As a historian,  
I want to query by timeframe without caring where the data lives,  
So that 60-year knowledge feels seamless.

**Acceptance Criteria:**  
**Given** multi-tier storage,  
**When** I run `jarvis memory temporal --from 2030 --to 2035 --topic "vector DB"`,  
**Then** the API fan-outs to the right tier(s), merges results, and annotates provenance,  
**And** CLI + web UI show the timeline and storage source.

**Prerequisites:** Stories 10.1-10.2.  
**Technical Notes:** Gateway service determines tier via metadata; caching via Redis for recent queries.

---

## FR Coverage Matrix

| FR | Description | Epic / Stories |
|----|-------------|----------------|
| FR1 | RAG Query System | Epic 3 – Stories 3.1-3.4 |
| FR2 | Multi-Agent Orchestration | Epic 4 – Stories 4.1-4.4 |
| FR3 | Cost-First LLM Routing | Epic 5 – Stories 5.1-5.4 |
| FR4 | Persistent Memory System | Epic 2 – Stories 2.1-2.5 (foundation for FR1/FR7/FR10) |
| FR5 | Docker Containerization | Epic 1 – Stories 1.1-1.4 |
| FR6 | CLI Integration | Epic 6 – Stories 6.1-6.4 (plus Story 1.4 bootstrap) |
| FR7 | Web Scraping & Internet Integration | Epic 7 – Stories 7.1-7.3 |
| FR8 | Bootstrap Evolution & Self-Improvement | Epic 8 – Stories 8.1-8.4 |
| FR9 | Web Interface | Epic 9 – Stories 9.1-9.3 |
| FR10 | 60-Year Memory | Epic 10 – Stories 10.1-10.3 |

---

## Summary

The epic plan now covers every FR from the PRD, maps prerequisites so implementation can progress incrementally, and infuses architecture decisions (stack versions, Typer CLI, Qdrant, pydantic-settings, BMAD orchestration) into each story’s technical notes. With epics.md created, the next BMAD steps are:
1. Run `/bmad:bmm:workflows:implementation-readiness` to validate traceability before coding.
2. Feed prioritized epics/stories into `/bmad:bmm:workflows:sprint-planning` for Phase 4 execution.

_Use the `create-story` workflow per story when ready to enter implementation._

---
