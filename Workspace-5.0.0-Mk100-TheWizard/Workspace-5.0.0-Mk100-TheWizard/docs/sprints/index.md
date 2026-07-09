# Sprint & Epic Documentation

This folder contains all sprint artifacts, epic documentation, user stories, and retrospectives following BMAD Method standards.

## 📊 Sprint Status

**Current Sprint Status:** [sprint-status.yaml](sprint-status.yaml)

**Epic Progress:**
- ✅ Epic 1: Self-Hosted Foundation & Workspace Ops (DONE)
- ✅ Epic 2: Persistent Memory Backbone (DONE)
- ✅ Epic 3: Intelligent RAG Query Engine (DONE)
- ✅ Epic 4: Council of Ricks Multi-Agent Reasoning (DONE)
- ✅ Epic 4-5: ARCHES Cognitive Stabilization (DONE)
- ✅ Epic 9: Political Governance & Multi-Human Consensus (DONE)
- 🏗️ Epic 8: Autonomous Evolution & BMAD Handoff (IN PROGRESS)
- 🏗️ Epic 11: Sovereign Identity Layer (IN PROGRESS)
- 📋 Epic 5: Cost-First LLM Router (BACKLOG)
- 📋 Epic 6: Developer-Grade CLI & Automation (BACKLOG)
- 📋 Epic 7: Knowledge Expansion via Web Intake (BACKLOG)
- 📋 Epic 10: Time-Decay Memory Continuum (BACKLOG)

---

## 🎯 Epic Retrospectives (BMAD-Compliant)

### Completed Retrospectives

#### [Epic 1 Retrospective - Self-Hosted Foundation](epic-1-retro-2025-11-17.md)
**Date:** 2025-11-17 | **Status:** ✅ Done

**Summary:** Delivered production-grade Docker foundation with 100% story completion (4/4 stories). Zero blockers, zero production incidents. Exceptional code quality (A-grade) with comprehensive test coverage.

**Key Outcomes:**
- Docker Compose stack with 4 services operational
- Workspace mount with file access controls
- Configuration & secret management via pydantic-settings
- Typer bootstrap & diagnostics CLI

**Lessons Learned:**
- Unit tests necessary but not sufficient for infrastructure
- Poetry lock file critical for Docker builds
- Integration tests should be planned upfront

---

#### [Epic 2 Retrospective - Persistent Memory Backbone](epic-2-retro-2025-11-26.md)
**Date:** 2025-11-26 | **Status:** ✅ Done

**Summary:** Implemented PostgreSQL schemas, ingestion workflows, and Qdrant collections. All 5 stories delivered with robust memory persistence.

**Key Outcomes:**
- Conversation storage schema with full metadata
- Document ingestion pipeline (PDF, Markdown, HTML)
- Qdrant collection initialization (384-d vectors)
- Memory retrieval filters & API
- Scheduled memory compilation

**Architecture Decisions:**
- JSONB for flexible metadata (voting, citations, cost)
- Alembic migrations for schema evolution
- Dual storage: Qdrant (vectors) + PostgreSQL (full docs)

---

#### [Epic 3 Retrospective - Intelligent RAG Query Engine](epic-3-retro-2025-11-29.md)
**Date:** 2025-11-29 | **Status:** ✅ Done

**Summary:** Delivered full RAG loop with hybrid retrieval, query expansion, and citation-first response formatting. All 4 stories completed.

**Key Outcomes:**
- Query command & response envelope
- Hybrid retrieval toggle (semantic + keyword BM25)
- Query expansion & multi-query fusion
- Citation-first response formatting

**Performance:**
- Semantic search P95: <150ms
- Hybrid search P95: <300ms
- Query expansion overhead: ~200ms

---

#### [Epic 4 Retrospective - Council of Ricks Multi-Agent Reasoning](epic-4-retro-2025-12-09.md)
**Date:** 2025-12-09 | **Status:** ✅ Done

**Summary:** Transformed JARVIS into autonomous multi-agent platform. All 14 stories completed (8 core + 6 extended) with exceptional quality.

**Key Outcomes:**
- Persona registry with hot-reload
- Parallel agent invocation (91% faster than sequential)
- Weighted chaos voting engine
- Response aggregation & override UX
- Self-aware memory gap detection
- Autonomous research capability (MCP-based)

**Architectural Breakthroughs:**
- Async-first design (`asyncio.gather()`)
- MCP tool integration eliminates Epic 7 prerequisite
- Graceful degradation for partial failures

**Preparation for Epic 5:**
- Provider registry schema design
- Cost ledger schema design
- Refactor LLM call sites for cost tracking

---

#### [Epic 4-5 Retrospective - ARCHES Cognitive Stabilization](epic-4-5-retro-2025-12-09.md)
**Date:** 2025-12-09 | **Status:** ✅ Done

**Summary:** Transformed ARCHES from distributed pattern into coherent cognitive controller. All 10 stories completed with A+ architectural quality.

**Key Outcomes:**
- ARCHES Runtime Controller (centralized cognitive orchestration)
- Agent Memory Attribution (full per-agent traceability)
- Memory Recency & Lineage Enforcement (`is_latest` filtering)
- Retrieval Saturation Filter (MMR diversity)
- ARCHES Planner Feedback Loop (adaptive planning)
- Cognitive Trace Log (full observability)
- Primary Document Viewer & UX Authority

**Philosophical Achievement:**
- JARVIS evolved from "smart RAG with personas" to **Cognitive OS with brain, spine, black box, and cockpit**
- Self-aware, adaptive, introspective system

**Preparation for Epic 9 & 11:**
- Extend ARCHESSession with user context
- User-scoped cognitive traces

---

#### [Epic 9 Retrospective - Political Governance & Multi-Human Consensus](epic-9-retro-2025-12-09.md)
**Date:** 2025-12-09 | **Status:** ✅ Done

**Summary:** Built machine democracy - multi-human governance with trust-weighted voting and constitutional constraints. All 5 stories completed.

**Key Outcomes:**
- Multi-human governance model (4 roles: Owner, Admin, Contributor, Observer)
- Disagreement voting engine (proposals, quorum, timeouts)
- Trust-weighted consensus (domain expertise matters)
- Constitutional framework (core values, red lines, amendment process)
- Governance dashboard (real-time transparency)

**Political Achievement:**
- JARVIS is no longer a tool - it's a **governed cognitive institution**
- Machine democracy is production-ready

**Compliance Win:**
- Governance framework maps to GDPR, AI Act, SOC 2 requirements
- Audit trails, role-based access, constitutional constraints = compliance moat

**Preparation for Epic 11:**
- Map governance roles to Keycloak roles
- OAuth token validation with role claims
- User-scoped governance queries

---

## 📋 Epic Planning & Status Documents

### Epic Definitions
- [epics.md (Status Folder)](../status/epics.md) - Complete epic breakdown with FR coverage

### Epic Planning Documents
- [epic-3-prep-checklist.md](epic-3-prep-checklist.md) - Epic 3 preparation tasks
- [epic-5-prep-plan.md](epic-5-prep-plan.md) - Epic 5 Cost Router planning
- [epic-8-planning.md](epic-8-planning.md) - Epic 8 autonomous evolution planning
- [epic-9-planning.md](epic-9-planning.md) - Epic 9 governance planning
- [epic-11-planning.md](epic-11-planning.md) - Epic 11 sovereign identity planning

### Epic Completion Reports
- [epic-4-completion-report.md](epic-4-completion-report.md) - Epic 4 completion summary
- [epic-4.5-arches-stabilization.md](epic-4.5-arches-stabilization.md) - Epic 4.5 detailed planning

### Hard Cuts & Technical Decisions
- [epic-8-6-hard-cuts.md](epic-8-6-hard-cuts.md) - Epic 8 Story 6 implementation decisions

---

## 📝 User Stories (docs/sprints/stories/)

**Total Stories:** 100+ across all epics

### Story Naming Convention
Format: `{epic}-{story}-{title}.md`

Examples:
- `1-1-compose-stack-service-contracts.md`
- `4-8-self-aware-memory-gap-detection-autonomous-research.md`
- `9-5-governance-dashboard.md`
- `11-1-sovereign-identity.md`

### Story Structure (BMAD-Compliant)
Each story includes:
- **User Story:** As a [role], I want [goal], So that [value]
- **Acceptance Criteria:** Testable conditions for story completion
- **Tasks/Subtasks:** Checkbox list of implementation tasks
- **Dev Notes:** Architecture patterns, technical guidance
- **Learnings from Previous Story:** Context from last completed story

### Story Status Workflow
1. **backlog:** Story exists in epic file only
2. **drafted:** Story file created in stories/ folder
3. **ready-for-dev:** Draft approved + story context created
4. **in-progress:** Developer actively working
5. **review:** Under review
6. **done:** Story completed ✅

---

## 🎯 Sprint Workflow (BMAD Method)

### Phase 1: Product Brief
Create product vision document defining goals, users, and success criteria.
- **Workflow:** `/bmad:bmm:workflows:product-brief`
- **Output:** `product-brief.md`

### Phase 2: PRD (Product Requirements Document)
Transform brief into detailed functional and non-functional requirements.
- **Workflow:** `/bmad:bmm:workflows:prd`
- **Output:** `prd.md` or `prd/` (sharded)

### Phase 3: Architecture
Design technical architecture with ADRs (Architecture Decision Records).
- **Workflow:** `/bmad:bmm:workflows:architecture`
- **Output:** `architecture.md` or `architecture/` (sharded)

### Phase 4: Epic & Story Breakdown
Decompose PRD into actionable epics and user stories.
- **Workflow:** `/bmad:bmm:workflows:create-epics-and-stories`
- **Output:** `epics.md`, `stories/*.md`

### Phase 5: Implementation
Execute stories sequentially with context propagation.
- **Create Story:** `/bmad:bmm:workflows:create-story`
- **Story Context:** `/bmad:bmm:workflows:story-context`
- **Dev Story:** `/bmad:bmm:workflows:dev-story`

### Phase 6: Code Review
Senior developer code review on completed stories.
- **Workflow:** `/bmad:bmm:workflows:code-review`
- **Output:** Review notes appended to story file

### Phase 7: Retrospective
After epic completion, review success and extract learnings.
- **Workflow:** `/bmad:bmm:workflows:retrospective`
- **Output:** `epic-{N}-retro-{date}.md`

---

## 📚 BMAD Templates

### Story Template
```markdown
# Story {epic}-{story}: {Title}

Status: {backlog|drafted|ready-for-dev|in-progress|review|done}

## Story
As a {role},
I want {goal},
So that {value}.

## Acceptance Criteria
1. **Given** {context}, **When** {action}, **Then** {outcome}

## Tasks / Subtasks
- [ ] Task 1
  - [ ] Subtask 1a
  - [ ] Subtask 1b

## Dev Notes
{Architecture patterns, technical guidance, references}

## Learnings from Previous Story
{Context from last completed story}
```

### Retrospective Template
```markdown
# Epic {N} Retrospective - {Title}

**Date:** {YYYY-MM-DD}
**Epic:** {Epic Title}
**Facilitator:** Bob (Scrum Master)
**Participants:** {Team members}

## Executive Summary
{High-level outcomes, metrics, business impact}

## Team Retrospective Discussion

### What Went Well
{Successes, wins, breakthroughs}

### Challenges & Growth Areas
{Struggles, learnings, improvements}

### Key Insights & Learnings
{Patterns, discoveries, principles}

## Epic {N} Story Analysis
{Story-by-story breakdown}

## Preparation for Epic {N+1}
{Dependencies, readiness, prep tasks}

## Action Items & Commitments
{Concrete next steps with owners and deadlines}

## Retrospective Closure
{Summary, key takeaways, next steps}
```

---

## 🔗 Related Documentation

**Project Status:**
- [../status/epics.md](../status/epics.md) - Epic definitions and FR coverage
- [sprint-status.yaml](sprint-status.yaml) - Current sprint tracking

**Architecture:**
- [../architecture/index.md](../architecture/index.md) - Architecture documentation
- [../reference/architecture.md](../reference/architecture.md) - Full system architecture

**Guides:**
- [../guides/CONTRIBUTING.md](../guides/CONTRIBUTING.md) - How to contribute
- [../guides/repository-guidelines.md](../guides/repository-guidelines.md) - Code standards

---

*Last Updated: 2025-12-09*
*Sprint Framework: BMAD Method (v6 Compliant)*
*Total Epics: 11 | Completed: 6 | In Progress: 2 | Backlog: 3*
