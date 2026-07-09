# JARVIS AI Advisor - Documentation Hub

Welcome to the JARVIS project documentation. This is a **Cognitive OS with multi-human governance**, built following BMAD Method standards.

**Project Status:** v2.x - ARCHES Stabilized, Governance Enabled
**Architecture:** Multi-Agent RAG with Autonomous Research & Democratic Governance
**Sprint Framework:** BMAD Method (v6 Compliant)

---

## 🚀 Quick Start

**New to JARVIS?** Start here:
1. **[README](README.md)** - Project overview and quick start
2. **[LLM Setup Guide](guides/llm-setup.md)** - Configure LLM providers
3. **[Ingestion Guide](guides/ingestion-guide.md)** - Ingest your first documents
4. **[Troubleshooting](guides/troubleshooting.md)** - Common issues and fixes

**For Developers:**
1. **[Contributing Guide](guides/CONTRIBUTING.md)** - How to contribute code
2. **[Repository Guidelines](guides/repository-guidelines.md)** - Code standards
3. **[Architecture Overview](reference/architecture.md)** - System design

---

## 📁 Documentation Structure

### 🏗️ [Architecture](architecture/)
Core architectural documentation for JARVIS memory, retrieval, and cognitive systems.

**Key Documents:**
- **[JARVIS Memory Architecture](architecture/jarvis-memory-architecture.md)** - Multi-tier memory system (Qdrant, PostgreSQL, Redis)
- **[Memory Pipeline Flow](architecture/memory-pipeline-flow.md)** - Data ingestion and retrieval flow
- **[Domain Taxonomy](architecture/domain-taxonomy.md)** - Knowledge classification system
- **[Enhancements 2025-12-02](architecture/enhancements-2025-12-02.md)** - Recent architectural improvements

**→ [Full Architecture Index](architecture/index.md)**

---

### 🎨 [Features](features/)
Detailed documentation for JARVIS capabilities and user-facing features.

**Key Features:**
- **[Autonomous Knowledge Graph](features/autonomous-knowledge-graph.md)** - Self-maintaining entity/relationship graph
- **[Advanced Conversation Management](features/advanced-conversation-management.md)** - Thread-aware context preservation
- **[Conversation Pagination & Search](features/conversation-pagination-search.md)** - Fast conversation discovery
- **[UI Collapsible Panels](features/ui-collapsible-panels.md)** - Iron Man-style cognitive cockpit

**→ [Full Features Index](features/index.md)**

---

### 📊 [Performance](performance/)
Performance optimization reports, tuning guides, and benchmark analysis.

**Key Reports:**
- **[High-Performance Optimization](performance/high-performance-optimization.md)** - System-wide tuning guide
- **[Index Analysis](performance/index-analysis-final.md)** - Database index audit
- **[Docker Optimization](performance/docker-optimization.md)** - Container performance tuning
- **[Architect Audit](performance/architect-audit.md)** - Architectural performance review

**Benchmarks:**
- Parallel agent invocation: **91% faster** than sequential (2.1s vs 23s for 4 personas)
- Retrieval P95 latency: **<150ms** (semantic + MMR diversity filtering)
- Database operations: Conversation load **<100ms**, message insert **<20ms**

**→ [Full Performance Index](performance/index.md)**

---

### 🎯 [Sprints](sprints/)
Sprint artifacts, epic documentation, user stories, and retrospectives (BMAD Method compliant).

**Epic Status (11 total):**
- ✅ **6 Complete:** Epics 1, 2, 3, 4, 4-5, 9
- 🏗️ **2 In Progress:** Epics 8, 11
- 📋 **3 Backlog:** Epics 5, 6, 7, 10

**Recent Retrospectives:**
- **[Epic 4: Council of Ricks](sprints/epic-4-retro-2025-12-09.md)** - Multi-agent orchestration (14 stories, 91% faster)
- **[Epic 4-5: ARCHES Stabilization](sprints/epic-4-5-retro-2025-12-09.md)** - Cognitive controller (10 stories, A+ architecture)
- **[Epic 9: Political Governance](sprints/epic-9-retro-2025-12-09.md)** - Machine democracy (5 stories, compliance moat)

**Story Tracking:**
- Total Stories: **100+** across all epics
- Story Files: [sprints/stories/](sprints/stories/)
- Sprint Status: [sprint-status.yaml](sprints/sprint-status.yaml)

**→ [Full Sprints Index](sprints/index.md)**

---

### 📖 [Guides](guides/)
Practical guides for developers, operators, and users.

- **[Contributing](guides/CONTRIBUTING.md)** - How to contribute to the codebase
- **[LLM Setup](guides/llm-setup.md)** - Configuring LLM providers and API keys
- **[Ingestion Guide](guides/ingestion-guide.md)** - Document ingestion workflows
- **[Troubleshooting](guides/troubleshooting.md)** - Common issues and resolutions
- **[Quick Start Enhancements](guides/quick-start-enhancements.md)** - Guide for implementing features
- **[Repository Guidelines](guides/repository-guidelines.md)** - Code standards and conventions

---

### 📚 [Reference](reference/)
Core technical documentation and specifications.

**System Architecture:**
- **[Architecture](reference/architecture.md)** - Complete system architecture with ADRs
- **[Product Requirements (PRD)](reference/prd.md)** - Functional and non-functional requirements
- **[Knowledge Pipeline](reference/knowledge-pipeline.md)** - Data ingestion and retrieval flow

**Multi-Agent System:**
- **[Agent Coordination](reference/agent-coordination.md)** - Council of Ricks orchestration
- **[Agent Guidelines](reference/agent-guidelines.md)** - Persona development guide

**LLM Infrastructure:**
- **[LLM Arsenal](reference/llm-arsenal.md)** - Available models and capabilities
- **[LLM Cost Protection](reference/llm-cost-protection.md)** - Cost management strategies
- **[Gemini Notes](reference/gemini-notes.md)** - Gemini-specific configuration

**System Primitives:**
- **[Variable Grounding](reference/variable-grounding.md)** - Context grounding system
- **[Safety Guidelines](reference/safety-guidelines.md)** - Operational boundaries
- **[Test Design](reference/test-design.md)** - Testing strategy and patterns
- **[Quick Reference](reference/quick-reference.md)** - Command reference card

---

### 📊 [Status](status/)
Project tracking, status updates, and historical records.

**Current Status:**
- **[Epic Definitions](status/epics.md)** - Complete epic breakdown with FR coverage
- **[Integration Status](status/integration.md)** - System integration state
- **[Tech Debt](status/tech-debt.md)** - Known technical debt and remediation plans
- **[Release Notes v2.0.2](status/release-notes-v2.0.2.md)** - Recent changes

**Historical Reports:**
- **[Implementation Summary v2](status/implementation-summary-v2.md)** - v2.x implementation details
- **[Readiness Report 2025-11-17](status/readiness-report-2025-11-17.md)** - Production readiness assessment
- **[Refactoring Summary](status/refactoring-summary.md)** - Code quality improvements
- **[Bug Fixes](status/bugfixes.md)** - Historical bug fix log

---

### 🏛️ [Legacy](legacy/)
Archived documentation for historical context (preserved but not maintained).

- **[Autonomous Research](legacy/AUTONOMOUS-RESEARCH.md)** - Early research concepts (superseded by Story 4.8)
- **[Research UI Walkthrough](legacy/research-ui-walkthrough.md)** - Archived UI concepts

---

### 🛠️ [Operations](operations/)
Operational guides for deployment, monitoring, and incident response.

- **[Health Checks](operations/health-checks.md)** - Service health monitoring
- **[Safe Mode](operations/safe-mode.md)** - Degraded operation procedures

---

### 💬 [JARVIS](jarvis/)
JARVIS-specific documentation, playbooks, and user exports.

**Core Documentation:**
- **[Operating Manual](jarvis/operating-manual.md)** - How to operate JARVIS
- **[Persona](jarvis/persona.md)** - JARVIS persona definition
- **[Memory Core](jarvis/memory.core.md)** - Core memory concepts
- **[GenerativeDrive Overview](jarvis/gd-overview.md)** - GD project context
- **[Integration Plan](jarvis/integration-plan.md)** - Integration roadmap

**Playbooks & Tests:**
- [jarvis/playbooks/](jarvis/playbooks/) - Operational playbooks
- [jarvis/tests/](jarvis/tests/) - Test scenarios

---

### 📝 [Sessions](sessions/)
Conversation session logs and historical dialogues.

Historical conversation exports for context and training data.

---

### 🎨 [Chat Orientations](chatOrientations/)
System prompts and chat orientations for different JARVIS modes.

- JDCRS v1 variants (original, Claude-optimized, minimal)

---

### 📊 [Dataset Rules](datasetRules/)
Data ingestion rules, observations, and refinement notes.

- **[Dataset Rules](datasetRules/dataSetRules.md)** - Ingestion rules and heuristics
- **[Ingestion Observations](datasetRules/dataSetIngestionObservations.md)** - Lessons learned
- **[Workspace Docs Refinement](datasetRules/ingest_Workspace_docs_refinement.md)** - Refinement notes

---

### 📦 [Archive](archive/)
Older documentation preserved for historical reference.

- Original PRD, task logs, sample knowledge, planning documents

---

## 🧠 System Overview

### What is JARVIS?

JARVIS is a **Cognitive OS** - not just a chatbot, but a governed cognitive institution capable of:

1. **Multi-Agent Reasoning** - Council of Ricks with weighted chaos voting
2. **Autonomous Research** - Self-aware gap detection and proactive knowledge seeking
3. **Democratic Governance** - Multi-human consensus with trust-weighted voting
4. **Cognitive Introspection** - Full trace observability (replay any query's execution)
5. **Constitutional Constraints** - Core values (safety, privacy, truth, sovereignty) enforced programmatically

### Core Capabilities

**Memory System:**
- Hybrid retrieval (semantic Qdrant + keyword PostgreSQL BM25)
- 60-year memory architecture (tiered storage with time-decay)
- Document versioning with freshness enforcement (`is_latest` filtering)
- Memory attribution per agent (know which chunks informed which decision)

**Multi-Agent System:**
- 4 personas (Rickiest Rick, Analytical Rick, Supportive Rick, Chaotic Rick)
- Parallel invocation (91% faster than sequential)
- Weighted chaos voting (confidence × weight × consistency bonus)
- Manual override control (`--select` flag)

**Governance:**
- 4 roles: Owner, Admin, Contributor, Observer
- Trust-weighted voting (domain expertise matters)
- Constitutional framework (core values + red lines)
- Governance dashboard (real-time transparency)

**Cognitive Controller (ARCHES):**
- Centralized session management
- Adaptive planning with feedback loops
- Cognitive trace logging (full observability)
- Memory attribution and freshness tracking

---

## 🎯 Current Focus

**Active Epics:**
- **Epic 8:** Autonomous Evolution & BMAD Handoff (Stories 8-1 to 8-4 ready-for-dev)
- **Epic 11:** Sovereign Identity Layer (Story 11-1 in-progress)

**Next Priorities:**
- Epic 5: Cost-First LLM Router (prep tasks identified)
- Epic 6: Developer-Grade CLI & Automation
- Epic 7: Knowledge Expansion via Web Intake (deferred - MCP tools already enable research)

---

## 📈 Key Metrics

### Delivery Metrics
- **Epics Completed:** 6/11 (55%)
- **Stories Completed:** ~70/100+ (70%+)
- **Retrospectives:** 6 BMAD-compliant retrospectives completed

### Performance Metrics
- **Retrieval P95:** <150ms (semantic + MMR filtering)
- **Agent Invocation:** 2.1s for 4 personas (91% faster than sequential)
- **Memory Attribution Overhead:** ~50ms per query
- **Database Operations:** <100ms for conversation load

### Code Quality
- **Test Coverage:** Comprehensive unit + integration tests
- **Code Quality:** A/A+ grade across epics
- **Technical Debt:** Minimal (proactive debt management)
- **Production Incidents:** 0 across all completed epics

---

## 🔗 External Resources

**BMAD Method:**
- [BMAD Core Documentation](.bmad/README.md) (if available)
- BMAD workflows: `/bmad:bmm:workflows:*`
- BMAD agents: `/bmad:bmm:agents:*`

**Project Repository:**
- README: [README.md](README.md)
- License: [LICENSE](../LICENSE) (if applicable)
- Contributing: [guides/CONTRIBUTING.md](guides/CONTRIBUTING.md)

---

## 📞 Getting Help

**Troubleshooting:**
1. Check [Troubleshooting Guide](guides/troubleshooting.md)
2. Review [Operations Health Checks](operations/health-checks.md)
3. Consult [LLM Status](status/llm.md) for provider issues

**Documentation Issues:**
- File issues in project repository
- Propose documentation improvements via PR
- Follow [Repository Guidelines](guides/repository-guidelines.md)

---

## 🎓 Learning Path

**For New Developers:**
1. Read [README](README.md) - Project overview
2. Study [Architecture](reference/architecture.md) - System design
3. Follow [LLM Setup](guides/llm-setup.md) - Environment configuration
4. Review [Contributing Guide](guides/CONTRIBUTING.md) - Development workflow
5. Read [Epic 4 Retrospective](sprints/epic-4-retro-2025-12-09.md) - Understand multi-agent system

**For Architects:**
1. Study [JARVIS Memory Architecture](architecture/jarvis-memory-architecture.md)
2. Review [Epic 4-5 Retrospective](sprints/epic-4-5-retro-2025-12-09.md) - ARCHES controller design
3. Read [Performance Optimization](performance/high-performance-optimization.md)
4. Analyze [Epic 9 Retrospective](sprints/epic-9-retro-2025-12-09.md) - Governance architecture

**For Product Managers:**
1. Read [PRD](reference/prd.md) - Product requirements
2. Review [Epic Definitions](status/epics.md) - Feature roadmap
3. Study [Epic 9 Planning](sprints/epic-9-planning.md) - Governance vision
4. Check [Sprint Status](sprints/sprint-status.yaml) - Current progress

---

*Last Updated: 2025-12-09*
*Documentation Version: v2.x (ARCHES Stabilized, Governance Enabled)*
*Total Documents: 155 markdown files across 21 directories*

**🤖 JARVIS is not a chatbot. It's a Cognitive OS with a Parliament.**
