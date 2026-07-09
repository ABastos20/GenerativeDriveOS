# Story 4-9: Workspace Docs Canonical Ingestion

Status: done
Epic: 4 (ARCHES Stabilization & Cognitive Layer)
Completed: 2025-12-05

## Story

As a **Jarvis architect ensuring semantic coherence**,
I want **all workspace docs ingested with proper domain/tag/flag/semantic_family classification**,
so that **retrieval respects the hybrid plane architecture (Vision not Ultron)**.

## Acceptance Criteria

1. [x] `ingest_workspace_docs.py` script classifies all docs with domain/tags/meta
2. [x] `docs/jarvis/*` (except playbooks) marked as System Plane:
   - `domain = "jarvis-core"`
   - `jarvis_core = true`
   - `is_system = true`
   - `semantic_family = "core-memory"`
   - `priority = 1.0`
3. [x] `docs/jarvis/playbooks/*` marked as Corpus Plane:
   - `domain = "jarvis-playbooks"`
   - `is_system = false`
   - `semantic_family = "playbook"`
   - `priority = 0.8`
4. [x] `docs/archive/*` marked as stale:
   - `is_latest = false`
   - `is_system = false`
   - `semantic_family = "archive"`
   - `priority = 0.2`
5. [x] Retrieval filter (`_build_filter`) excludes `is_system=true` by default
6. [x] Domain `jarvis-core` explicit selection forces include
7. [x] `include_system_docs=True` param for meta/introspection queries
8. [x] `semantic_family` field on all classified documents

---

## Semantic Family Taxonomy

| Family | Domain(s) | Plane | Priority |
|--------|-----------|-------|----------|
| `core-memory` | jarvis-core | 🔒 SYSTEM | 1.0 |
| `playbook` | jarvis-playbooks | CORPUS | 0.8 |
| `architecture` | architecture | CORPUS | 0.9 |
| `archive` | archive | CORPUS (stale) | 0.2 |
| `feature` | features | CORPUS | 0.75 |
| `session-log` | sessions | CORPUS | 0.5 |
| `story` / `story-context` | story | CORPUS | 0.4-0.6 |
| `epic` / `process` | epic, process | CORPUS | 0.5-0.7 |
| `llm` | llm | CORPUS | 0.6 |

---

## Why semantic_family Matters

Without it, everything lives in a flat vector space with only domain/tags/is_system separation.

### Retrieval-Time Safety & Biasing

- **Default**: `semantic_family != "core-memory" AND is_system == false`
- **Meta mode**: allow core-memory, downweight unless query is introspection
- **Architecture queries**: want `architecture` + `story` more than `core-memory`

### Analytics & Coverage

- Ask Jarvis: "which semantic_family has least docs / least fresh docs?"
- Epic 4.6+ can do time-aware retrieval by semantic_family
- Current architecture docs win over older sprint stories

---

## Failure Modes to Guard Against

### 4.1 System Leakage into Normal QA

**Risk**: If `_build_filter()` forgets `must_not(is_system == true)` AND ranker treats core-memory as "super on-topic", user asks "how do you work?" and gets raw internal spec.

**Mitigations**:
- [x] Centralized filter construction in `_build_qdrant_filter`
- [ ] Unit test: for QA mode, assert is_system always excluded
- [ ] At answer composition: if top-1 from jarvis-core in normal QA, drop/downweight

### 4.2 Inability to Introspect

**Risk**: Over-filter and make it impossible to answer:
- "Summarise memory.core.md"
- "What's the operating manual for Jarvis?"
- "What epics and sprints exist?"

**Mitigations**:
- [x] `include_system_docs=True` path exists
- [x] `domain=jarvis-core` forces include
- [ ] Meta router heuristic on controller:

```python
# Pseudo-logic
if query matches (jarvis|architecture|epic|sprint|story|cognitive|council):
    if not clearly about hydrogen/finance/etc:
        mode = META
        include_system_docs = True
        prefer domains in {jarvis-core, architecture, epic, story}
```

---

## Validation Test Suite (Manual)

Run these 5 queries through web UI to validate:

### 1. Normal Domain QA
- **Filters**: none / normal
- **Ask**: "Explain the hydrogen water loop concept in GD."
- **Expect**: playbooks + GD docs, NO jarvis-core

### 2. Architecture QA  
- **Ask**: "How is Jarvis's memory architecture designed?"
- **Expect**: `docs/architecture/jarvis-memory-architecture.md`, `jarvis-knowledge-pipeline.md`, maybe epic-4.5
- **NOT**: memory.core unless meta mode on

### 3. Hard Meta: Core
- **Enable**: meta/introspection (`include_system_docs=True` or `domain=jarvis-core`)
- **Ask**: "Summarise memory.core.md in 5 bullets."
- **Expect**: only core docs; if anything else wins, priority/filters need tweaking

### 4. Historical Plan
- **Ask**: "What was the original PRD for Jarvis before Epic 4?"
- **Enable**: `allow_stale` (or equivalent)
- **Expect**: `docs/archive/prd-original.md` visible; default mode should NOT return it

### 5. Session Introspection
- **Ask**: "What happened in the BREAKTHROUGH session on 2025-12-03?"
- **Expect**: sessions domain, that specific session log, not random architecture

**If all 5 behave as designed → ingest + filters + semantic families are aligned.**

---

## Files Changed

- `scripts/ingest_workspace_docs.py` - Full classification with semantic_family
- `src/jarvis/memory/search.py` - Added `is_system` filter to `_build_filter()`

## References

- Canonical schema: `docs/datasetRules/dataSetRules.md`
- Brainstorming: `docs/sessions/brainstorming-session-improve-ingestion-core-2025-12-05.md`
- Observations: `docs/datasetRules/dataSetIngestionObservations.md`
- Refinement: `docs/datasetRules/ingest_Workspace_docs_refinement,md`

---

**Vision, not Ultron.** ✅
