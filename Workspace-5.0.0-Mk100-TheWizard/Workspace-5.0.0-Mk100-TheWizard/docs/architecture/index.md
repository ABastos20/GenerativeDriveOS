# Architecture Documentation

This folder contains core architectural documentation for the JARVIS AI Advisor system.

## 📐 Core Architecture

### [JARVIS Memory Architecture](jarvis-memory-architecture.md)
Complete memory system architecture covering:
- Multi-tier memory storage (Qdrant, PostgreSQL, Redis)
- Semantic + keyword hybrid retrieval
- ARCHES cognitive controller
- Temporal memory management
- Document versioning and freshness enforcement

**Key Components:**
- Qdrant vector store (384-d embeddings)
- PostgreSQL full-document storage
- Hybrid search (semantic + BM25 keyword)
- Memory attribution per agent
- Cognitive trace logging

---

### [Memory Pipeline Flow](memory-pipeline-flow.md)
Data flow architecture for document ingestion and retrieval:
- Ingestion pipeline (PDF, Markdown, HTML → normalized chunks)
- Embedding generation (sentence-transformers)
- Qdrant upsert with metadata
- PostgreSQL full-document storage
- Retrieval flow with MMR diversity filtering

**Pipeline Stages:**
1. Document upload / fetch
2. Format conversion (→ Markdown)
3. Semantic chunking (2000 chars default)
4. Embedding generation
5. Dual storage (Qdrant + PostgreSQL)
6. Metadata enrichment (domains, tags, timestamps)

---

### [Domain Taxonomy](domain-taxonomy.md)
Domain classification system for knowledge organization:
- CHAVAO domain map (core JARVIS domains)
- Domain heuristics for auto-classification
- Primary domain assignment
- Multi-domain tagging
- Domain-specific retrieval filtering

**Domains:**
- `jarvis.core`: JARVIS system knowledge
- `jarvis.conversations`: Chat history
- `jarvis.architecture`: Technical architecture
- `bmad`: BMAD methodology
- `generativedrive`: GenerativeDrive projects
- `telecom`, `cybersecurity`, `ai_ml`: Industry domains

---

### [Enhancements 2025-12-02](enhancements-2025-12-02.md)
Recent architectural enhancements and improvements:
- ARCHES cognitive stabilization
- Agent memory attribution
- Freshness enforcement (`is_latest` filtering)
- MMR diversity filter for retrieval saturation
- Cognitive trace observability

---

## 🏗️ Architecture Principles

### Async-First Design
All I/O-bound operations use `asyncio` for parallelism:
- 91% latency reduction from parallel agent invocation
- Semaphore-based rate limiting
- Thread pool for sync LLM bridges

### Modular Separation of Concerns
- **Controller** coordinates (ARCHESController)
- **Modules** execute (gap_analyzer, research_planner, parallel_invocation)
- **Storage** persists (PostgreSQL, Qdrant, Redis)
- **API** exposes (FastAPI endpoints)

### JSONB for Flexible Metadata
- `voting_metadata`: Agent consensus data
- `citation_provenance`: Source attributions
- `memory_attribution`: Per-agent chunk usage
- `trust_scores`: Domain expertise weights

### Constitutional Constraints
- Core values enforced programmatically (safety, privacy, truth, sovereignty)
- Red lines cannot be overridden by voting
- Amendment process requires supermajority (80% approval, 75% quorum, 7-day cooling period)

---

## 🔗 Related Documentation

**Technical Reference:**
- [../reference/architecture.md](../reference/architecture.md) - Full system architecture
- [../reference/knowledge-pipeline.md](../reference/knowledge-pipeline.md) - Knowledge ingestion details
- [../reference/prd.md](../reference/prd.md) - Product requirements

**Implementation Guides:**
- [../guides/ingestion-guide.md](../guides/ingestion-guide.md) - How to ingest documents
- [../guides/llm-setup.md](../guides/llm-setup.md) - LLM provider configuration

**Sprint Documentation:**
- [../sprints/epic-4-retro-2025-12-09.md](../sprints/epic-4-retro-2025-12-09.md) - Council of Ricks retrospective
- [../sprints/epic-4-5-retro-2025-12-09.md](../sprints/epic-4-5-retro-2025-12-09.md) - ARCHES stabilization retrospective

---

## 📊 Architecture Metrics

**Storage:**
- Qdrant: 384-dimensional embeddings, cosine similarity
- PostgreSQL: Full documents + metadata (JSONB)
- Redis: Session state + caching

**Performance:**
- Parallel agent invocation: ~2-3s for 4 personas (91% faster than sequential)
- Retrieval P95 latency: ~150ms (including freshness + MMR filtering)
- Memory attribution overhead: ~50ms per query

**Governance:**
- 4 roles: Owner, Admin, Contributor, Observer
- Trust-weighted voting with domain expertise
- Constitutional validation on all proposals

---

*Last Updated: 2025-12-09*
*Architecture Version: v2.x (ARCHES Stabilized, Governance Enabled)*
