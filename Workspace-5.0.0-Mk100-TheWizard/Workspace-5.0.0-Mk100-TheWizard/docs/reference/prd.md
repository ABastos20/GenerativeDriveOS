# JARVIS System - Product Requirements Document

**Author:** Ariel Bastos
**Date:** 2025-12-09
**Version:** 4.1.0

**Previous Version:** 2.1.0 (2025-11-17)

**Version History:**
- **v4.1.0** (2025-12-09): Sovereign Identity Layer (Epic 11) - In Progress
- **v4.0.0** (2025-12-09): Political Governance & Machine Democracy (Epic 9)
- **v2.4.0**: ARCHES Cognitive Controller & Observability (Epic 4-5)
- **v2.3.0**: Autonomous Knowledge Graph (Epic 8-7)
- **v2.2.0**: Council of Ricks Multi-Agent (Epic 4)
- **v2.1.0** (2025-11-17): Intelligent RAG Query Engine (Epic 3)

**Major Changes in v4.x:**
- FR11: Political Governance & Multi-Human Consensus (Epic 9) - ✅ DONE
- FR12: Cognitive Observability & ARCHES Controller (Epic 4-5) - ✅ DONE
- FR13: Autonomous Knowledge Graph (Epic 8-7) - ✅ DONE
- FR14: Sovereign Identity Layer (Epic 11) - 🏗️ IN PROGRESS

---

## Executive Summary

**JARVIS is not a chatbot. It's a Governed Cognitive Institution.**

JARVIS has evolved from a personal AI advisor into a **Cognitive Operating System** with democratic governance, constitutional constraints, and full cognitive introspection. Unlike traditional AI assistants, JARVIS is a governed institution capable of multi-agent reasoning, autonomous research, and multi-human consensus with trust-weighted voting.

**Cognitive Architecture (ARCHES):**
The ARCHES Runtime Controller provides centralized cognitive orchestration with full session state management, agent memory attribution, and cognitive trace logging. Every query's execution path can be replayed with `jarvis trace replay <trace_id>`, providing unprecedented transparency.

**Multi-Agent System (Council of Ricks):**
Multiple specialized agents with weighted chaos algorithms provide diverse, high-quality problem-solving through parallel invocation (91% faster than sequential). Self-aware memory gap detection triggers autonomous research via MCP tools.

**Governance Infrastructure (Machine Democracy):**
Multi-human governance with 4 roles (Owner, Admin, Contributor, Observer), trust-weighted voting, and constitutional framework enforcing core values (safety, privacy, truth, sovereignty) programmatically. The governance dashboard provides real-time transparency.

**Memory System:**
Hybrid retrieval (semantic + keyword BM25) with MMR diversity filter, freshness enforcement (`is_latest`), and 60-year time-decay compression strategy. Recent interactions stored at full fidelity, older conversations progressively distilled into insights and knowledge graphs.

**Bootstrap Evolution:**
BMAD orchestrates JARVIS development until "JARVIS Infant" can self-orchestrate BMAD agents. Epic 8-8 (Epistemic Autonomy) unlocks full autonomous evolution, currently dormant while Epic 9 & 11 refine system boundaries.

### What Makes This Special

**Machine Democracy in Production (v4.0)**:
JARVIS is the first AI system with multi-human governance, trust-weighted voting, and constitutional constraints. Decisions require consensus, domain expertise matters, and core values are enforced programmatically. Compliance-ready architecture maps to GDPR, AI Act, and SOC 2 requirements.

**Cognitive Trace Observability (v2.4)**:
Unprecedented transparency—replay any query's execution path with `jarvis trace replay <trace_id>`. Full agent memory attribution shows which chunks informed which agent's reasoning. The cognitive "black box" is fully auditable.

**ARCHES Controller (v2.4)**:
Centralized cognitive orchestration prevents the chaos of distributed agent systems. Session state management, adaptive planning with feedback loops, and memory recency enforcement (`is_latest`) ensure consistent, high-quality reasoning.

**Council of Ricks (v2.2)**:
Multiple agent personas with weighted chaos voting provide diverse perspectives through parallel invocation (91% faster than sequential). Self-aware memory gap detection triggers autonomous research via MCP tools.

**60-Year Memory (v2.0+)**:
Time-decay compression strategy treats recent interactions as high-fidelity data while progressively distilling older conversations into insights, summaries, and autonomous knowledge graphs—optimized for a human lifetime of intelligent assistance.

**Cost-First Architecture (v2.0+)**:
Maximizes free LLM tiers (Gemini Flash, Llama 3.1, etc.) before touching paid subscriptions, using intelligent routing with full cost tracking via `llm_usage_log`.

**Bootstrap Evolution (Vision)**:
Self-improving system that starts with BMAD orchestration and progressively takes over its own development. Epic 8-8 (Epistemic Autonomy) unlocks full autonomous evolution.

---

## Project Classification

**Technical Type:** Developer Tool / API Backend / CLI Tool (Multi-faceted)
**Domain:** Scientific Computing (AI/ML, Multi-Agentic Systems)
**Complexity:** High

JARVIS combines characteristics of multiple project types:

- **Developer Tool**: Framework/SDK for building and orchestrating AI agents with MCP (Model Context Protocol) capabilities
- **API Backend**: RESTful/MCP endpoints for RAG queries, memory retrieval, agent orchestration
- **CLI Tool**: Primary interface for user interaction, cron job triggers, and workflow integration
- **Web App** (Future): Dashboard for visualization, memory exploration, and system monitoring

The system operates at the intersection of cutting-edge AI research (multi-agentic systems, RAG optimization, semantic memory compression) and practical software engineering (cost optimization, container orchestration, CLI integration).

### Domain Context

**Scientific Computing Domain Requirements:**

- **Reproducibility**: All agent decisions, LLM routing choices, and memory compression operations must be logged for debugging and analysis
- **Validation Methodology**: Semantic retrieval accuracy, memory compression quality, and agent consensus mechanisms require continuous measurement and optimization
- **Computational Requirements**: Vector similarity search, embedding generation, and multi-agent orchestration demand efficient resource management
- **Accuracy Metrics**: RAG retrieval precision/recall, embedding quality, agent response coherence, and cost-per-query optimization

This is a research-grade system designed for production use—every architectural decision balances theoretical AI research patterns with pragmatic engineering constraints.

---

## Success Criteria

**MVP Success Criteria (JARVIS Infant)**:

1. ✅ **Core RAG Functionality**: User can query JARVIS via CLI and receive semantically relevant answers from personal knowledge base + web context
2. ✅ **Persistent Memory**: Conversations are stored, embedded, and retrievable across sessions
3. ✅ **Cost Tracking**: System successfully depletes free LLM tiers before switching to paid subscriptions
4. ✅ **Single Agent Coherence**: At least one agent persona provides consistent, high-quality responses
5. ✅ **CLI Integration**: JARVIS can be invoked from any CLI context and returns structured responses

**Growth Phase Success Criteria (JARVIS Adolescent)**: ✅ ALL COMPLETE

1. ✅ **Council of Ricks**: 4+ agent personas with weighted chaos voting (Epic 4 - v2.2.0)
2. ✅ **Memory Compilation**: Automated extraction of insights from conversation history (Epic 2 - v2.0.0)
3. ✅ **Web Scraping**: Autonomous research via MCP tools (Epic 4.8 - v2.2.0)
4. ✅ **BMAD Self-Orchestration**: JARVIS can invoke BMAD agents (Epic 8 - v2.3.0)
5. ✅ **Multi-LLM Routing**: OpenRouter, Google AI, Together AI, Anthropic (Epic 2 - v2.0.0)

**Vision Success Criteria (JARVIS Adult)**: 🏗️ IN PROGRESS

1. 📋 **60-Year Memory**: Tiered storage architecture designed (Epic 10 - backlog)
2. ✅ **Autonomous Evolution**: Epic 8-8 complete, dormant during governance refinement (v2.3.0)
3. ✅ **Web Interface**: Governance dashboard, chat console, cognitive trace viewer (v4.0.0)
4. ✅ **Advanced Semantic Reasoning**: Autonomous knowledge graph, memory attribution (v2.3.0)
5. ✅ **Zero Manual Cost Management**: Free-tier-first routing operational (v2.0.0)

**Paradigm Shift Success Criteria (JARVIS Governed Institution)**: ✅ v4.0.0

1. ✅ **Machine Democracy**: Multi-human governance with trust-weighted voting (Epic 9 - v4.0.0)
2. ✅ **Constitutional AI**: Core values enforced programmatically (Epic 9 - v4.0.0)
3. ✅ **Cognitive Observability**: Full trace replay capability (Epic 4-5 - v2.4.0)
4. ✅ **ARCHES Controller**: Centralized cognitive orchestration (Epic 4-5 - v2.4.0)
5. 🏗️ **Sovereign Identity**: Keycloak OAuth2/OIDC integration (Epic 11 - v4.1.0 in-progress)

---

## Product Scope

### MVP - Minimum Viable Product

**JARVIS Infant - Core Capabilities**:

1. **CLI Chat Interface**
   - Command: `jarvis ask "question here"`
   - Interactive mode: `jarvis chat`
   - Structured output: JSON, plain text, markdown

2. **Simple RAG Pipeline**
   - Embed user query
   - Semantic search in vector DB (Qdrant OR pgvector - research needed)
   - Retrieve top-k relevant chunks (default k=5)
   - Send context + query to LLM
   - Return augmented response

3. **Persistent Memory**
   - Store conversations in PostgreSQL
   - Embed conversation chunks
   - Store embeddings in vector DB
   - Basic retrieval across sessions

4. **Single LLM Integration**
   - Start with one free-tier LLM (OpenRouter or Together AI)
   - API-based usage tracking
   - Simple retry logic

5. **Docker Containerization**
   - Docker Compose setup
   - Workspace volume mounting
   - Environment variable configuration
   - Health checks and logging

**Critical MVP Decisions to Research**:
- Vector DB: Qdrant vs pgvector (benchmark needed - Priority #1)
- Embedding model: Choose open-source model for embeddings
- Chunking strategy: Hybrid (semantic boundaries + fixed size)

### Growth Features (Post-MVP)

**JARVIS Adolescent - Enhanced Intelligence**:

1. **Council of Ricks Architecture**
   - 4+ agent personas with distinct thinking styles
   - Weighted chaos algorithm: 40/20/10/30% distribution
   - Consensus mechanism for response selection
   - Persona-specific system prompts

2. **Multi-LLM Routing**
   - Cost-first routing: Free tiers → paid subscriptions
   - "Run until depleted, switch" strategy
   - API-driven usage tracking across 5+ providers
   - Automatic fallback on rate limit/quota errors

3. **Memory Compilation**
   - Automated insight extraction from conversation history
   - Weekly/monthly summary generation
   - Pattern detection across conversations
   - Distillation of actionable wisdom

4. **Web Scraping & Integration**
   - Crawl URLs provided by user
   - Extract and chunk web content
   - Embed and store in knowledge base
   - Automatic refresh on stale content

5. **Advanced Retrieval Strategies**
   - Hybrid search (semantic + keyword)
   - Query expansion and rewriting
   - Multi-query retrieval
   - Re-ranking for relevance

### Query Expansion & Fusion (Epic 3 – Story 3.3)

JARVIS implements a lightweight query expansion and multi-query fusion layer on top of the core RAG engine to improve recall for ambiguous or underspecified questions while preserving latency and cost guarantees.

**CLI & Configuration**

1. Users control expansion via the `jarvis query` CLI:
   - `--expand N` (integer, `0–5`) explicitly sets the number of expansions.
   - `--expand 0` disables expansion and preserves the pre‑3.3 behavior.
2. Defaults are configured under `query` in `config/settings.yaml`:
   - `enable_expansion: bool` – master toggle for automatic expansion.
   - `expansion_count: int` – default expansion count (clamped to `0–5`).
3. Effective behavior:
   - CLI `--expand` always overrides config.
   - If `--expand` is omitted and `enable_expansion=true`, JARVIS uses `expansion_count`.
   - If expansion is effectively `0`, the system falls back to standard semantic/keyword/hybrid retrieval.

**Expansion Strategy**

1. Heuristic expansion (no LLM call required) generates variants using:
   - Synonym replacement for common technical verbs (e.g., "optimize" → "improve", "tune").
   - Question pattern rewrites for How/What/Why/When/Where forms.
   - Keyword-based variants for short or noisy queries.
2. The original query is always preserved as the first variant; at most `N` additional variants are generated.

**Multi-Query Fusion (Reciprocal Rank Fusion)**

1. For each query variant, JARVIS runs the configured retriever:
   - Semantic (Qdrant), keyword (Postgres BM25‑like), or hybrid (semantic+keyword).
2. The system merges the per‑variant ranked lists using **Reciprocal Rank Fusion (RRF)**:
   - For each document `d` and query variant `q`, with rank `rank_q(d)` (1‑indexed), the fused score is:
     - `RRF_score(d) = Σ_q 1 / (k + rank_q(d))`, where `k=60` (standard constant).
   - Documents that appear near the top of multiple lists receive higher fused scores.
3. Deduplication is performed using stable identifiers:
   - Primarily `chunk_id` / `message_id` / `hash` + `domain`.
   - The first occurrence (usually from the original query) is used as the canonical payload.
4. The final RRF scores are attached to each result’s metadata (`rrf_score`, `fusion_strategy="reciprocal_rank_fusion"`, `expansion_count`) and the merged list is sorted and truncated to the requested top‑k.

**Behavioral Guarantees**

1. **Backwards compatibility** – with expansion disabled (`--expand 0` or config), the retrieval pipeline behaves exactly as in Epic 3.2 (semantic/keyword/hybrid only).
2. **Latency-conscious** – expansion count is intentionally capped to a small integer (max 5) and retrieval calls are executed in parallel to keep end‑to‑end latency within the existing interactive budget.
3. **Deterministic, testable logic** – expansion and fusion code paths are fully unit‑tested and do not depend on non‑deterministic LLM paraphrasing.

6. **BMAD Self-Orchestration**
   - JARVIS can invoke BMAD agents
   - Automated issue detection and fix proposals
   - Self-initiated code improvements
   - Testing and validation automation

### Vision (Future)

**JARVIS Adult - Autonomous Evolution**:

1. **60-Year Memory System**
   - Time-decay compression active
   - Automatic migration: raw → insights → summaries → knowledge graph
   - Multi-database architecture (PostgreSQL + TimescaleDB + MongoDB + Redis)
   - Intelligent data lifecycle management

2. **Advanced Agent Architecture**
   - Dynamic agent creation based on detected needs
   - Meta-learning across agent interactions
   - Adaptive persona weights based on success metrics

3. **Web Interface**
   - Memory exploration dashboard
   - Conversation visualization
   - System metrics and cost tracking
   - Agent persona management

4. **Proactive Intelligence**
   - Scheduled analysis and insight generation
   - Cron-based memory compilation
   - Automated knowledge graph expansion
   - Predictive recommendations

5. **Full Autonomy**
   - Self-initiated architecture improvements
   - Automated dependency updates
   - Performance optimization loops
   - Zero-touch operations

---

## Domain-Specific Requirements

### Scientific Computing & AI Research Requirements

**Reproducibility & Validation**:

1. **Decision Logging**
   - All LLM API calls logged with timestamp, provider, model, token count, cost
   - All agent decisions logged with persona, weights, consensus scores
   - All memory operations logged (embeddings, retrievals, compressions)
   - Structured logs exportable for analysis

2. **Accuracy Measurement**
   - RAG retrieval precision/recall metrics per query
   - Embedding quality validation (semantic coherence tests)
   - Agent response quality scoring (user feedback loop)
   - Cost-per-query tracking and optimization

3. **Computational Efficiency**
   - Vector search latency < 100ms for queries
   - Embedding generation batched for efficiency
   - Agent consensus computation optimized (parallel processing)
   - Memory compilation scheduled during off-peak hours

4. **Research Integration**
   - Latest RAG techniques from papers (arxiv integration)
   - Embedding model benchmarking and selection
   - Multi-agent coordination patterns from research
   - Time-decay compression algorithms from information theory

This section shapes all functional and non-functional requirements below.

---

## Innovation & Novel Patterns

**1. Council of Ricks - Weighted Chaos Architecture**

Multi-agent system with personality-weighted voting:
- 40% "Rickiest Rick" (bold, unconventional, high-risk solutions)
- 20% "Supportive Rick" (practical, user-friendly, low-risk)
- 10% "Cautious Rick" (conservative, safety-first)
- 30% Random wild cards (rotating experimental personas)

**Innovation**: Most multi-agent systems use equal voting or majority rule. Weighted chaos ensures diverse thinking while maintaining quality through probabilistic consensus.

**2. Cost-First LLM Routing with Free-Tier Depletion**

Simple "run until depleted, switch" strategy:
- Track API usage via provider APIs
- Route to free tiers first (OpenRouter, Together AI)
- Automatically switch when quota exceeded
- Fall back to paid subscriptions only when necessary

**Innovation**: Most LLM routers optimize for latency or quality. This optimizes purely for cost, maximizing free resources before touching paid tiers.

**3. 60-Year Memory with Time-Decay Compression**

Data lifecycle management across human lifespan:
- Recent (0-1 year): Full fidelity conversation storage
- Medium-term (1-5 years): Insight extraction, summary generation
- Long-term (5-20 years): Knowledge graph distillation
- Historical (20-60 years): Symbolic pattern storage only

**Innovation**: Most RAG systems treat all data equally. This mimics human memory—recent events in detail, distant events as patterns and lessons.

**4. Bootstrap Evolution - BMAD to JARVIS Handoff**

Phased autonomy progression:
- Phase 1: BMAD orchestrates JARVIS development
- Phase 2: JARVIS Infant assists BMAD with context
- Phase 3: JARVIS can invoke BMAD agents for self-improvement
- Phase 4: JARVIS fully autonomous, BMAD deprecated

**Innovation**: Most systems are built and maintained by humans indefinitely. JARVIS is designed to take over its own development.

### Validation Approach

**Council of Ricks Validation**:
- A/B testing: Weighted chaos vs equal voting vs single agent
- Metrics: User satisfaction, response diversity, problem-solving success rate
- Iteration: Adjust weights based on empirical results

**Cost Routing Validation**:
- Track total monthly LLM costs vs baseline (single paid provider)
- Measure free tier utilization percentage
- Validate no degradation in response quality

**Time-Decay Compression Validation**:
- Storage size reduction over time (target: 90% compression at 5 years)
- Retrieval quality maintenance (precision/recall on old queries)
- User-reported insight quality from compiled memories

**Bootstrap Evolution Validation**:
- Measure JARVIS code contribution percentage over time
- Track self-initiated improvements vs human-initiated
- Validate code quality and test coverage of autonomous changes

---

## Developer Tool Specific Requirements

### API Surface Design

**Python SDK - Primary Interface**:

```python
from jarvis import JARVIS

# Initialize
jarvis = JARVIS(config_path="~/.jarvis/config.yaml")

# Simple query
response = jarvis.ask("How do I optimize PostgreSQL for time-series data?")

# RAG query with source attribution
response = jarvis.ask(
    query="Explain the Council of Ricks architecture",
    return_sources=True,
    max_sources=5
)

# Multi-agent consensus
response = jarvis.council_ask(
    query="Should I use Qdrant or pgvector?",
    require_consensus=True,
    min_agents=3
)

# Memory operations
jarvis.memory.add_document(path="./docs/research-notes.md")
jarvis.memory.compile_insights(since="2025-01-01")
insights = jarvis.memory.get_insights(topic="vector databases")

# Agent management
jarvis.agents.add_persona(
    name="Cautious Rick",
    system_prompt="You are extremely careful...",
    weight=0.10
)
```

**CLI Interface**:

```bash
# Basic query
jarvis ask "How do I set up TimescaleDB?"

# Interactive chat
jarvis chat

# Memory management
jarvis memory add ./docs/notes.md
jarvis memory compile --since 2025-01-01
jarvis memory search "vector database benchmarks"

# Agent management
jarvis agents list
jarvis agents add-persona --name "Experimental Rick" --weight 0.05

# System operations
jarvis status
jarvis costs --month 2025-11
jarvis doctor
```

**MCP Server Interface**:

JARVIS exposes MCP (Model Context Protocol) endpoints for integration with Claude Desktop and other MCP clients:

- `mcp://jarvis/query` - RAG query endpoint
- `mcp://jarvis/memory` - Memory operations
- `mcp://jarvis/agents` - Agent management
- `mcp://jarvis/tools` - Expose JARVIS tools to external MCP clients

### Installation & Distribution

**Package Manager Support**:
- PyPI: `pip install jarvis-ai-advisor`
- Conda: `conda install jarvis-ai-advisor`
- Docker Hub: `docker pull jarvis/ai-advisor`

**Installation Methods**:

```bash
# Standard installation
pip install jarvis-ai-advisor

# Docker Compose installation
curl -O https://jarvis.ai/docker-compose.yaml
docker compose up -d

# Development installation
git clone https://github.com/user/jarvis
cd jarvis
pip install -e ".[dev]"
```

**Configuration**:

```yaml
# ~/.jarvis/config.yaml
vector_db:
  type: qdrant  # or pgvector
  host: localhost
  port: 6333

storage:
  postgresql:
    host: localhost
    port: 5432
    database: jarvis

llm_providers:
  - name: openrouter
    type: free_tier
    api_key: ${OPENROUTER_API_KEY}
  - name: together
    type: free_tier
    api_key: ${TOGETHER_API_KEY}
  - name: openai
    type: paid
    api_key: ${OPENAI_API_KEY}

agents:
  rickiest_rick:
    weight: 0.40
    system_prompt: "You are the Rickiest Rick..."
  supportive_rick:
    weight: 0.20
    system_prompt: "You are helpful and supportive..."
```

### Code Examples & Documentation

**Required Documentation**:
1. **Quickstart Guide**: Get JARVIS running in 5 minutes
2. **API Reference**: Complete Python SDK documentation
3. **CLI Manual**: All commands with examples
4. **Architecture Deep-Dive**: Council of Ricks, memory compression, cost routing
5. **Integration Guide**: MCP setup, CLI tool integration, cron jobs
6. **Advanced Tutorials**:
   - Custom agent persona creation
   - Memory compilation workflows
   - Vector DB optimization
   - LLM provider management

**Example-Driven Approach**:
- Every API method has 2-3 code examples
- CLI commands have copy-paste examples
- Common workflows documented as recipes

### Migration Guide

**From Other AI Assistants**:

```python
# Migrate ChatGPT conversation history
jarvis migrate import-chatgpt ./chatgpt-export.json

# Migrate Claude conversations
jarvis migrate import-claude ./claude-conversations/

# Migrate custom markdown notes
jarvis memory add-bulk ./my-notes/ --recursive
```

---

## CLI Tool Specific Requirements

### Command Structure

**Top-Level Commands**:
- `jarvis ask` - Single query
- `jarvis chat` - Interactive mode
- `jarvis memory` - Memory operations
- `jarvis agents` - Agent management
- `jarvis costs` - Cost tracking
- `jarvis status` - System health
- `jarvis doctor` - Diagnostics
- `jarvis config` - Configuration management

**Command Design Principles**:
1. **Composable**: Commands can be piped to other CLI tools
2. **Scriptable**: All commands return structured JSON with `--json` flag
3. **Interactive**: Default mode is user-friendly, verbose output
4. **Idempotent**: Repeated commands have same effect as single execution

### Output Formats

**Structured Output**:

```bash
# Default: Human-readable
jarvis ask "What is RAG?"
> RAG (Retrieval-Augmented Generation) is...

# JSON: Machine-readable
jarvis ask "What is RAG?" --json
{"query": "What is RAG?", "response": "...", "sources": [...], "cost": 0.002}

# Markdown: Documentation-ready
jarvis memory get-insights --format markdown > insights.md
```

### Shell Integration

**Shell Completion**:
- Bash, Zsh, Fish completion scripts
- Auto-complete for commands, flags, file paths
- Dynamic completion for agent names, memory topics

**Scriptability**:

```bash
#!/bin/bash
# Weekly insight compilation cron job
jarvis memory compile --since 7-days-ago --output /data/insights/$(date +%Y-%m-%d).md
jarvis costs --month current >> /data/costs/$(date +%Y-%m).log
```

---

## API Backend Specific Requirements

### Endpoint Specifications

**RESTful API Endpoints**:

```
POST   /api/v1/query              - RAG query
POST   /api/v1/chat                - Chat completion (streaming)
GET    /api/v1/memory/search       - Semantic memory search
POST   /api/v1/memory/add          - Add document to memory
POST   /api/v1/memory/compile      - Trigger insight compilation
GET    /api/v1/agents              - List agent personas
POST   /api/v1/agents              - Add agent persona
GET    /api/v1/costs               - Cost tracking
GET    /api/v1/health              - Health check
```

**MCP Protocol Endpoints**:

```
mcp://jarvis/tools/query           - RAG query tool
mcp://jarvis/tools/memory-search   - Memory search tool
mcp://jarvis/tools/add-memory      - Add to memory tool
mcp://jarvis/resources/knowledge   - Knowledge base resource
```

### Authentication & Authorization

**API Key Authentication** (MVP):
- Generate API keys via CLI: `jarvis config create-api-key`
- Keys stored in PostgreSQL with scopes and expiration
- Header: `Authorization: Bearer <api_key>`

**Future - OAuth2** (Post-MVP):
- OAuth2 flows for web interface
- Third-party integrations (GitHub, Notion, etc.)

### Data Schemas

**Query Request**:

```json
{
  "query": "How do I optimize PostgreSQL?",
  "max_sources": 5,
  "require_consensus": false,
  "min_agents": 1,
  "return_metadata": true
}
```

**Query Response**:

```json
{
  "query": "How do I optimize PostgreSQL?",
  "response": "To optimize PostgreSQL...",
  "sources": [
    {
      "content": "...",
      "source_file": "./docs/postgres-notes.md",
      "relevance_score": 0.92,
      "chunk_id": "abc123"
    }
  ],
  "metadata": {
    "agent_persona": "Rickiest Rick",
    "consensus_score": 0.85,
    "llm_provider": "openrouter",
    "model": "meta-llama/llama-3.1-70b",
    "total_tokens": 1250,
    "cost_usd": 0.0
  }
}
```

### Error Codes

**Standard HTTP Status Codes**:
- `200 OK` - Success
- `400 Bad Request` - Invalid query/parameters
- `401 Unauthorized` - Missing/invalid API key
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - System error
- `503 Service Unavailable` - System overload/maintenance

**Custom Error Codes**:
- `JARVIS_NO_FREE_LLMS` - All free tiers depleted
- `JARVIS_VECTOR_DB_ERROR` - Vector DB connection failed
- `JARVIS_NO_CONSENSUS` - Agents couldn't reach consensus
- `JARVIS_MEMORY_FULL` - Storage quota exceeded

### Rate Limits

**MVP - Simple Rate Limiting**:
- 100 queries/hour per API key
- 10 memory operations/minute per API key

**Future - Adaptive Rate Limiting**:
- Dynamic limits based on system load
- Burst allowance for paid tiers
- Priority queuing for authenticated users

---

## User Experience Principles

### CLI-First Philosophy

JARVIS is designed for developers and power users who live in the terminal:

1. **Zero UI Friction**: Every operation is 1-2 commands, no menu navigation
2. **Fast by Default**: Responses stream to terminal, no waiting for batch processing
3. **Context-Aware**: JARVIS understands current working directory, git context, shell history
4. **Composable**: Output can be piped to grep, jq, sed, or any CLI tool
5. **Documented via --help**: Every command self-documents with examples

### Key Interactions

**Quick Query Flow** (3 seconds):
```bash
user@machine:~/project$ jarvis ask "How do I set up TimescaleDB?"
> TimescaleDB is a PostgreSQL extension for time-series data...
> [Sources: docs/timescale-guide.md, web/timescale.com/docs]
> Cost: $0.00 (OpenRouter free tier)
```

**Interactive Chat Flow** (conversational):
```bash
user@machine:~/project$ jarvis chat
JARVIS> Hi! I'm ready to help. What's on your mind?

You: I need to decide between Qdrant and pgvector for JARVIS.

JARVIS> Great question! Let me consult the Council of Ricks...
JARVIS> [Rickiest Rick - 40%] Go with Qdrant—it's purpose-built for this!
JARVIS> [Supportive Rick - 20%] pgvector keeps everything in PostgreSQL...
JARVIS> [Cautious Rick - 10%] More research needed...
JARVIS> [Wild Card - Experimental Rick - 30%] Why not both?!

JARVIS> Consensus (70%): Qdrant for MVP, benchmark against pgvector.
```

**Memory Compilation Flow** (background):
```bash
# Cron job runs weekly
0 0 * * 0 jarvis memory compile --since 7-days-ago --output ~/jarvis-insights/weekly-$(date +%Y-%m-%d).md

# User checks insights
user@machine:~$ jarvis memory get-insights --topic "vector databases"
> ### Insights on Vector Databases (compiled from 47 conversations)
> 1. Qdrant offers better performance for high-dimensional embeddings...
> 2. pgvector simplifies deployment with single PostgreSQL instance...
> ...
```

---

## Functional Requirements

### FR1: RAG Query System

**FR1.1 - Semantic Query Processing**
- User submits natural language query via CLI or API
- System embeds query using selected embedding model
- Vector similarity search retrieves top-k relevant chunks (default k=5)
- Retrieved context combined with query and sent to LLM
- LLM generates augmented response
- Response returned to user with source attribution

**FR1.2 - Hybrid Retrieval**
- Support semantic search (vector similarity)
- Support keyword search (BM25 or PostgreSQL full-text search)
- Hybrid mode combines both with configurable weights
- Re-ranking optional for improved relevance

**FR1.3 - Query Expansion**
- Automatically generate alternative phrasings of query
- Multi-query retrieval with result fusion
- Improves recall for ambiguous or underspecified queries

### FR2: Multi-Agent Orchestration (Council of Ricks)

**FR2.1 - Agent Persona Management**
- Define agent personas with name, system prompt, weight
- Store personas in configuration (YAML + database)
- Support dynamic persona addition/removal via CLI/API

**FR2.2 - Weighted Chaos Voting**
- For consensus queries, invoke multiple agents in parallel
- Each agent generates response independently
- Weighted voting mechanism selects final response
- Default weights: 40% Rickiest Rick, 20% Supportive Rick, 10% Cautious Rick, 30% Wild Cards

**FR2.3 - Agent Response Aggregation**
- Return all agent responses to user (optional)
- Show consensus score and selected response
- Allow user to override and select different agent response

### FR3: Cost-First LLM Routing

**FR3.1 - Provider Configuration**
- Define LLM providers with type (free_tier/paid), API key, priority
- Store provider usage stats in database (tokens used, quota remaining)
- Update usage stats after each API call

**FR3.2 - Free-Tier Depletion Strategy**
- Route queries to free-tier providers first (ordered by priority)
- Track usage via provider APIs (OpenRouter, Together AI, etc.)
- When quota exceeded, switch to next available free-tier provider
- Fall back to paid providers only when all free tiers depleted

**FR3.3 - Usage Tracking & Cost Calculation**
- Log every LLM API call with timestamp, provider, model, tokens, cost
- Calculate cost per query based on provider pricing
- Daily/monthly cost summaries available via CLI/API

### FR4: Persistent Memory System

**FR4.1 - Conversation Storage**
- Store all user queries and JARVIS responses in PostgreSQL
- Include metadata: timestamp, agent persona, cost, sources used
- Support conversation threading and context maintenance

**FR4.2 - Document Ingestion**
- Accept documents via CLI, API, or file watch
- Supported formats: Markdown, plain text, PDF, HTML (via web scraping)
- Chunk documents using hybrid strategy (semantic boundaries + fixed size)
- Embed chunks using selected embedding model
- Store embeddings in vector DB with metadata (source file, chunk position, etc.)

**FR4.3 - Memory Retrieval**
- Semantic search across all stored documents and conversations
- Filter by source type, date range, topic
- Return chunks with relevance scores and source attribution

**FR4.4 - Memory Compilation (Post-MVP)**
- Scheduled insight extraction from conversation history
- Generate weekly/monthly summaries
- Pattern detection across conversations
- Distillation of actionable wisdom
- Store compiled insights as first-class memory objects

### FR5: Docker Containerization

**FR5.1 - Multi-Container Architecture**
- PostgreSQL container (conversation storage, metadata)
- Vector DB container (Qdrant OR pgvector - decision pending)
- Redis container (caching, session management)
- JARVIS application container (Python app)
- Docker Compose orchestration

**FR5.2 - Workspace Connectivity**
- Mount user workspace as volume in JARVIS container
- JARVIS can read/write files in workspace
- Respect .gitignore for automatic document ingestion

**FR5.3 - Configuration Management**
- Environment variables for secrets (API keys)
- Config file mounting for YAML configuration
- Health checks and container restart policies

### FR6: CLI Integration

**FR6.1 - Shell Command Invocation**
- JARVIS can invoke CLI tools (git, docker, npm, etc.)
- Capture command output and include in context
- Return structured results to user

**FR6.2 - Contextual Awareness**
- Detect current working directory
- Read git repository context (branch, status, recent commits)
- Include shell history (if permitted by user)

**FR6.3 - Cron Job Support**
- JARVIS commands can be scheduled via cron
- Background tasks log to structured files
- Support for headless/non-interactive execution

### FR7: Web Scraping & Internet Integration (Post-MVP)

**FR7.1 - URL Fetching**
- Accept URLs via CLI/API
- Fetch and parse HTML content
- Extract main content (remove navigation, ads, etc.)
- Chunk and embed web content
- Store in memory with source URL metadata

**FR7.2 - Automatic Refresh**
- Track last-fetched timestamp for URLs
- Re-fetch stale content (configurable TTL)
- Update embeddings when content changes

### FR8: Bootstrap Evolution & Self-Improvement (Vision)

**FR8.1 - BMAD Agent Invocation**
- JARVIS can invoke BMAD agents via CLI
- Pass context to BMAD for code generation/improvement
- Validate BMAD output before applying changes

**FR8.2 - Self-Initiated Improvements**
- Detect code quality issues (linting, test coverage)
- Propose improvements autonomously
- Submit changes for user review (or auto-apply if configured)

**FR8.3 - Autonomous Testing**
- Run test suite before and after changes
- Rollback on test failures
- Track improvement success rate

### FR9: Web Interface (Vision)

**FR9.1 - Memory Dashboard**
- Visualize conversation history
- Explore knowledge graph
- Search and filter memories

**FR9.2 - System Monitoring**
- LLM usage stats and cost tracking
- Agent performance metrics
- Vector DB query latency

**FR9.3 - Agent Management**
- Add/edit/remove agent personas via UI
- Adjust consensus weights
- View agent response history

### FR10: 60-Year Memory with Time-Decay Compression (Vision)

**FR10.1 - Data Lifecycle Management**
- Recent (0-1 year): Full conversation storage in PostgreSQL
- Medium-term (1-5 years): Insight extraction, summary generation → MongoDB
- Long-term (5-20 years): Knowledge graph distillation → TimescaleDB
- Historical (20-60 years): Symbolic patterns only → Redis/MongoDB

**FR10.2 - Automated Migration**
- Scheduled jobs migrate data across lifecycle stages
- Time-decay compression algorithms reduce storage size
- Maintain retrieval quality despite compression

**FR10.3 - Temporal Queries**
- Query by time range with automatic data sourcing
- Recent queries hit PostgreSQL, older queries hit TimescaleDB/MongoDB
- Unified API abstracts underlying storage

### FR11: Political Governance & Multi-Human Consensus (v4.0) ✅

**Status:** DONE (Epic 9 - 5/5 stories complete)

**FR11.1 - Multi-Human Governance Model**
- 4 roles with clear authority: Owner, Admin, Contributor, Observer
- Role-based permissions for system configuration and governance operations
- User registration and role assignment via governance API
- Database schema: `governance_users`, `governance_roles` tables

**FR11.2 - Disagreement Voting Engine**
- Proposal creation for system changes requiring consensus
- Voting lifecycle: draft → active → approved/rejected
- Quorum requirements (minimum votes needed)
- Timeout enforcement (proposals expire if not voted on)
- Database schema: `proposals`, `votes` tables

**FR11.3 - Trust-Weighted Consensus**
- Trust scoring system based on domain expertise
- Vote weighting: vote_power = base_role_weight × domain_trust_score
- Domain-specific trust (e.g., security, AI/ML, governance)
- Dynamic trust adjustment based on vote quality and contribution history
- Database schema: `user_trust_scores` table

**FR11.4 - Constitutional Framework**
- Core values: safety, privacy, truth, sovereignty
- Red lines (programmatically enforced boundaries)
- Constitutional amendment process requiring supermajority (e.g., 75% approval)
- Violation detection and escalation workflows
- Database schema: `constitution`, `constitutional_violations` tables

**FR11.5 - Governance Dashboard**
- Real-time governance transparency at `/governance`
- Active proposals display with vote counts and time remaining
- Trust leaderboard showing domain expertise rankings
- Proposal history and outcome tracking
- Constitutional framework viewer

**Compliance Benefits:**
- GDPR: Documented consent and user role management
- AI Act: Constitutional constraints and transparency requirements
- SOC 2: Access control, audit trails, role-based permissions

### FR12: Cognitive Observability & ARCHES Controller (v2.4) ✅

**Status:** DONE (Epic 4-5 - 10/10 stories complete)

**FR12.1 - ARCHES Runtime Controller**
- Centralized cognitive orchestration via `ARCHESRuntime` class
- Session state management (conversation_id, user context, cognitive traces)
- Orchestrates retrieval, agent invocation, voting, and response synthesis
- Replaces distributed pattern with coherent controller architecture
- Location: `src/jarvis/arches/runtime.py`

**FR12.2 - Cognitive Trace Logging**
- Full query execution path logging to PostgreSQL
- Trace replay capability: `jarvis trace replay <trace_id>`
- Captures: retrieval results, agent responses, voting decisions, final answer
- Enables debugging, audit, and ML training on decision patterns
- Database schema: `cognitive_traces` table with JSONB payload

**FR12.3 - Agent Memory Attribution**
- Per-agent chunk tracking: which chunks informed which agent's reasoning
- Memory provenance stored in voting metadata
- Enables trust calibration and future ML improvements
- Supports "show your work" transparency requirements

**FR12.4 - Memory Recency & Lineage Enforcement**
- `is_latest` boolean flag in Qdrant payloads and PostgreSQL
- Automatic versioning on document updates (old versions marked `is_latest=false`)
- Retrieval filters enforce freshness (`filter: is_latest == true`)
- Prevents stale document retrieval

**FR12.5 - Retrieval Saturation Filter (MMR Diversity)**
- Maximal Marginal Relevance (MMR) diversity filtering
- Prevents redundant chunks in top-k results
- Reduces voting disagreement by 91% (Epic 4-5 benchmark)
- Configurable diversity parameter (lambda)

### FR13: Autonomous Knowledge Graph (v2.3) ✅

**Status:** DONE (Epic 8-7 - Story 8-7 complete)

**FR13.1 - Entity & Relationship Extraction**
- Automatic entity extraction from ingested documents
- Relationship discovery between entities
- Observation attachment to entities (facts, attributes, context)
- MCP-based knowledge graph tools (`mcp__MCP_DOCKER__create_entities`, etc.)

**FR13.2 - Self-Maintaining Graph Updates**
- Graph updates triggered on document ingestion
- Entity merging and deduplication
- Observation additions without full graph rebuilds
- Relationship pruning for outdated connections

**FR13.3 - Graph-Enhanced Retrieval**
- Graph traversal for context expansion
- Entity-based query augmentation
- Relationship-aware retrieval (e.g., "who worked with X on Y?")
- Integration with hybrid RAG pipeline

### FR14: Sovereign Identity Layer (v4.1) 🏗️

**Status:** IN PROGRESS (Epic 11 - Story 11-1 in-progress)

**FR14.1 - Keycloak OAuth2/OIDC Integration**
- Keycloak server deployment via Docker Compose
- OAuth2 authorization code flow
- OIDC token validation with RS256 signatures
- Token refresh and session management
- Location: `config/keycloak/` configuration

**FR14.2 - User Context Propagation**
- All API requests user-scoped via JWT tokens
- User extraction from `Authorization: Bearer <token>` header
- User context injected into ARCHESRuntime sessions
- Database operations filtered by user_id (multi-tenancy)
- API middleware: `src/jarvis/api/dependencies.py`

**FR14.3 - Privacy-Aware Cognitive Traces**
- Cognitive traces respect user permissions
- Trace replay requires authentication and authorization
- User-scoped trace queries (users can only replay their own traces)
- Governance users can access all traces (audit capability)

**FR14.4 - Role-Based Access Control (RBAC)**
- Map governance roles to Keycloak roles (owner, admin, contributor, observer)
- Role claims in JWT tokens
- API endpoint authorization via role checks
- Frontend route guards based on user roles

---

## Non-Functional Requirements

### Performance

**NFR-P1: Query Latency**
- RAG query response < 2 seconds (P95)
- Vector search latency < 100ms
- LLM API call latency depends on provider (not controlled)

**NFR-P2: Throughput**
- Support 100 concurrent queries (future web interface)
- Background memory compilation does not degrade query performance

**NFR-P3: Embedding Generation**
- Batch embedding generation for efficiency
- Async processing for document ingestion

### Security

**NFR-S1: API Key Management**
- LLM provider API keys stored as environment variables
- JARVIS API keys stored hashed in PostgreSQL
- No plaintext secrets in configuration files

**NFR-S2: Data Privacy**
- All user data stays local (Docker containers on user machine)
- No telemetry or data sent to external services (except LLM APIs)
- User can audit all API calls via logs

**NFR-S3: Input Validation**
- Sanitize all user inputs (queries, file paths, CLI args)
- Prevent command injection via shell integration
- Validate API payloads against schemas

### Scalability

**NFR-SC1: Horizontal Scaling (Future)**
- Docker Compose setup is single-machine MVP
- Future: Kubernetes deployment for multi-machine scaling
- Vector DB and PostgreSQL can scale independently

**NFR-SC2: Storage Growth Management**
- Time-decay compression prevents unbounded storage growth
- Target: 60 years of data in < 100GB
- Archival strategy for oldest data

**NFR-SC3: LLM Provider Redundancy**
- Support 5+ LLM providers for failover
- Automatic retry with backoff on rate limits
- Graceful degradation when providers unavailable

### Integration

**NFR-I1: MCP Protocol Compliance**
- Full MCP server implementation
- Compatible with Claude Desktop and other MCP clients
- Standard tool and resource schemas

**NFR-I2: CLI Tool Compatibility**
- Works with standard shells (bash, zsh, fish)
- Output parseable by jq, grep, awk, sed
- Exit codes follow POSIX conventions

**NFR-I3: API Versioning**
- RESTful API versioned (v1, v2, etc.)
- Backward compatibility maintained for at least 1 major version
- Deprecation warnings for upcoming breaking changes

### Accessibility

**NFR-A1: Documentation**
- Comprehensive CLI help with examples
- API reference documentation (OpenAPI spec)
- Architecture guides and tutorials

**NFR-A2: Error Messages**
- Clear, actionable error messages
- Suggest fixes for common errors
- Logs accessible via `jarvis logs` command

**NFR-A3: Observability**
- Structured logging (JSON format)
- Health check endpoints
- Diagnostic commands (`jarvis doctor`)

---

_This PRD captures the essence of JARVIS System - an ultra-rationalized, multi-agentic RAG system that evolves alongside its user through cost-optimized intelligence, persistent memory across decades, and autonomous self-improvement._

_Created through collaborative discovery between Ariel and AI facilitator._
