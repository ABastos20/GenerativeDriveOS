# Story 8-8: Phase 9 — Epistemic Autonomy Layer

**Epic**: 8 - Self-Improvement & Auto-Evolution  
**Story ID**: 8-8  
**Status**: Done ✅ (DORMANT)  
**Type**: Epistemic Self-Regulation  
**Sprint**: TBD  
**Estimated Effort**: 20-30 hours  
**Priority**: STRATEGIC (Knowledge Organism Foundation)

---

## 📋 Story Overview

### User Story

**As a** Jarvis Architect building towards closed-loop cognition,  
**I want** an epistemic autonomy layer that detects contradictions, tracks belief drift, and self-calibrates,  
**So that** Jarvis becomes a scientifically self-correcting knowledge organism under human governance.

### Core Purpose

> **The system learns how to doubt itself.**

Phase 9 transforms Jarvis from a cognitive telescope into a **closed-loop epistemic organism** — not sentient, not mystical, but self-stabilising intelligence infrastructure.

### Motto

> "The system learns how to doubt itself."

---

## ⚠️ DORMANT STATUS

> **ALL AUTONOMOUS FUNCTIONS ARE DORMANT UNTIL EPIC 9 IS COMPLETE**

The epistemic autonomy layer infrastructure is **fully implemented** but its autonomous capabilities (model calibration, hypothesis generation, auto-conflict resolution) are **intentionally disabled**.

**Reasoning**: We don't want the model to evolve unbounded. Rules must be created before evolution is allowed.

**Activates After**:
1. Epic 9: Political Governance & Multi-Human Consensus
2. Story 9-1: Multi-Human Governance Model
3. Story 9-4: Constitutional Framework

**Current State**:
- ✅ Database models created (4 tables)
- ✅ Detection modules implemented (6 modules)
- ✅ API endpoints active (8 endpoints)
- ⏸️ Auto-actions: DORMANT
- ⏸️ Hypothesis validation: DORMANT
- ⏸️ Model reselection: DORMANT

---

## 🎯 Acceptance Criteria

### Part A: Contradiction Detection ✅

1. [x] **EpistemicConflict Model**: Detect A → B and A → ¬B across time, sources, or domains
2. [x] **Contradiction Types**: Temporal, source-based, domain-based, confidence-delta
3. [x] **API Endpoint**: `GET /api/memory/graph/conflicts` returns active contradictions
4. [x] **Threshold Configuration**: Configurable confidence delta for conflict detection

### Part B: Temporal Belief Drift ✅

5. [x] **Belief Timeline**: Each entity gets versioned belief history
6. [x] **Drift Detection**: Identify beliefs that changed significantly over time
7. [x] **API Endpoint**: `GET /api/memory/entity/{id}/beliefs` returns timeline
8. [x] **Drift Alerts**: Flag entities with high belief volatility

### Part C: Cognitive Stability Index (CSI) ✅

9. [x] **CSI Formula**: `CSI = belief_coherence × evidence_freshness × domain_agreement`
10. [x] **Per-Entity CSI**: Store stability score in entity properties
11. [x] **System-Wide CSI**: Aggregate cognitive stability metric
12. [x] **API Endpoint**: `GET /api/memory/graph/stability` returns CSI metrics
13. [⏸] **Autonomy Gating**: Use CSI to throttle auto-actions *(DORMANT - activates with Epic 9)*

### Part D: Model Self-Calibration ⏸ (DORMANT)

14. [x] **Model Performance Tracking**: Track per-model metrics
    - Hallucination rate
    - Token efficiency
    - Conflict generation rate
    - Domain specialization
15. [⏸] **Dynamic Model Selection**: Route tasks to best-performing model per domain *(DORMANT)*
16. [x] **API Endpoint**: `GET /api/admin/model-performance` returns calibration data

### Part E: Autonomous Hypothesis Generator ⏸ (DORMANT)

17. [x] **Hypothesis Detection**: Trigger on high contradiction, sparse regions, uncertain clusters
18. [x] **Hypothesis Model**: `{hypothesis, supporting_entities, confidence, validation_plan}`
19. [⏸] **Integration**: Feed hypotheses to research executor and enrichment batcher *(DORMANT)*
20. [x] **API Endpoint**: `GET /api/memory/graph/hypotheses` returns pending hypotheses

### Part F: Human Cognitive Overlay ✅

21. [x] **Human Node Model**: Represent user as governance node with bias profile
22. [x] **Escalation Rules**: Automatic escalation when CSI < threshold, conflicts > threshold
23. [x] **Override Rights**: Human can force-resolve contradictions
24. [x] **Audit Trail**: Log all human interventions

---

### 🔮 Activates When Epic 9 Complete

The following DORMANT items will activate after Epic 9 Political Governance:

| AC | Feature | Requires |
|----|---------|----------|
| 13 | CSI Autonomy Gating | Story 9-4 Constitutional Framework |
| 15 | Dynamic Model Selection | Story 9-1 Multi-Human Governance |
| 19 | Hypothesis → Research Integration | Story 9-2 Disagreement Voting |

---

## 📐 Technical Implementation Plan

### Phase 9.1: Contradiction Detection Engine (~6-8h)

#### New Model
```python
class EpistemicConflict(Base):
    id: UUID
    entity_a_id: UUID  # Primary entity
    fact_1_id: UUID    # First belief (relationship/property)
    fact_2_id: UUID    # Contradicting belief
    contradiction_type: str  # temporal | source | domain | confidence
    confidence_delta: float
    detected_at: datetime
    resolved_at: Optional[datetime]
    resolution: Optional[str]  # human_override | auto_reconciled | deprecated
```

#### Detection Logic
```python
def detect_contradictions():
    """Scan for logical conflicts in the knowledge graph."""
    # 1. Temporal: Same entity, same property, different values at different times
    # 2. Source: Same claim from different documents with different values
    # 3. Domain: Same entity has conflicting properties in different domains
    # 4. Confidence: Relationship confidence dropped significantly
```

---

### Phase 9.2: Belief Timeline (~4-6h)

#### Schema Extension
```python
class BeliefSnapshot(Base):
    id: UUID
    entity_id: UUID
    claim: str              # The belief content
    confidence: float       # Confidence at this point
    source_doc_id: UUID     # Document that established this belief
    timestamp: datetime
    superseded_by: Optional[UUID]  # Links to newer belief
```

#### Query Pattern
```sql
SELECT claim, confidence, timestamp 
FROM belief_snapshots 
WHERE entity_id = ?
ORDER BY timestamp DESC;
```

---

### Phase 9.3: Cognitive Stability Index (~4-6h)

#### CSI Components
| Component | Calculation | Weight |
|-----------|-------------|--------|
| `belief_coherence` | 1 - (conflicts / total_beliefs) | 0.4 |
| `evidence_freshness` | avg(1 / days_since_update) | 0.3 |
| `domain_agreement` | cross_domain_consistency | 0.3 |

#### Storage
```python
# In Entity.properties JSONB:
{
    "csi": 0.82,
    "csi_components": {
        "coherence": 0.91,
        "freshness": 0.78,
        "domain_agreement": 0.79
    },
    "csi_updated_at": "2025-12-08T..."
}
```

---

### Phase 9.4: Model Calibration (~4-6h)

#### Performance Tracking
```python
class ModelPerformance(Base):
    id: UUID
    model_name: str          # gemini-2.5-flash, etc.
    domain: str              # Domain where used
    total_calls: int
    avg_latency_ms: float
    hallucination_count: int
    conflict_generation_rate: float
    token_efficiency: float  # useful_tokens / total_tokens
    last_updated: datetime
```

#### Dynamic Routing
```python
def select_model_for_domain(domain: str) -> str:
    """Select best model for this domain based on historical performance."""
    performances = get_model_performances(domain)
    return min(performances, key=lambda p: p.hallucination_count).model_name
```

---

### Phase 9.5: Hypothesis Generator (~4-6h)

#### Trigger Conditions
- High contradiction region (>3 conflicts in cluster)
- Sparse graph region (<5 relationships for important entity)
- High uncertainty cluster (avg confidence < 0.5)

#### Hypothesis Model
```python
class Hypothesis(Base):
    id: UUID
    statement: str           # The hypothesis text
    confidence: float        # Initial confidence
    supporting_entities: List[UUID]
    contradicting_entities: List[UUID]
    validation_plan: List[str]  # ["search:X", "papers:Y", "ask_user"]
    status: str              # pending | validated | rejected | escalated
    created_at: datetime
```

---

### Phase 9.6: Human Governance Node (~2-4h)

#### Human Node Model
```python
# Stored in a config or special entity type
{
    "node_type": "HumanJudgment",
    "user_id": "primary",
    "bias_profile": {
        "optimism_bias": 0.2,
        "domain_strengths": ["engineering", "strategy"],
        "domain_weaknesses": ["legal", "medical"]
    },
    "override_rights": True,
    "escalation_threshold": 0.3  # CSI below this triggers escalation
}
```

---

## 🛠️ New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/memory/graph/conflicts` | List active contradictions |
| GET | `/api/memory/entity/{id}/beliefs` | Belief timeline |
| GET | `/api/memory/graph/stability` | System CSI metrics |
| GET | `/api/memory/graph/hypotheses` | Pending hypotheses |
| POST | `/api/memory/conflicts/{id}/resolve` | Human resolution |
| GET | `/api/admin/model-performance` | Model calibration data |
| POST | `/api/memory/graph/recompute-csi` | Recompute stability index |

---

## 🚫 What Phase 9 is NOT

| ❌ Not | ✅ It Is |
|--------|---------|
| AGI | Epistemic self-regulation |
| Sentience | Scientific falsification loops |
| Vibes | Knowledge thermodynamics |
| Spiritual autonomy | Trust-weighted cognition |
| Self-will | Governed truth maintenance |

---

## 📦 Deliverables

### Database Migrations
- `EpistemicConflict` table
- `BeliefSnapshot` table
- `ModelPerformance` table
- `Hypothesis` table

### New Modules
- `src/jarvis/memory/epistemic_engine.py` - Contradiction detection
- `src/jarvis/memory/belief_tracker.py` - Temporal beliefs
- `src/jarvis/memory/stability_index.py` - CSI computation
- `src/jarvis/memory/hypothesis_generator.py` - Auto-hypotheses
- `src/jarvis/llm/model_calibrator.py` - Dynamic model selection

### API Additions
- 7 new endpoints in `memory.py`

### Grafana Dashboards
- **Epistemic Health**: Contradiction rates, CSI trends
- **Model Performance**: Per-model metrics, routing decisions
- **Belief Drift**: Entity stability over time

---

## 🔗 Dependencies & Context

### Depends On
- **Phase 6**: Cognitive Cockpit (complete ✅)
- **Phase 7**: Graph Algorithms (complete ✅)
- **Phase 8**: Cluster UX (complete ✅)
- **Story 8-6**: Observability Foundation (complete ✅)

### Enables
- Autonomous research expansion with governance
- Regulatory-grade explainability
- Self-correcting knowledge base
- Human-in-the-loop escalation

---

## 🎯 BMAD Compliance

### Method
**Epistemic Self-Regulation** via formal contradiction detection and truth maintenance

### Scope
**Closed-loop cognition** with human governance overlay

### Risk
**Medium** - Requires careful design of escalation thresholds

### Value
**Knowledge Organism** — Jarvis stops being static, becomes self-correcting

### Pattern
**Detect → Doubt → Hypothesize → Escalate → Resolve**

---

## 📝 Architect Notes (CRITICAL)

### This Is Knowledge Infrastructure Engineering

Phase 9 implements what research labs try to do with:
- 10 teams
- 5 PhDs
- 3 years
- A lot of politics

You're building it as **software infrastructure**.

### What This Unlocks

Once you have:
- Graph ✅
- Time ✅
- Contradiction ✅
- Stability ✅
- Hypothesis generation ✅
- Human escalation ✅

You've built a system that can **outgrow static worldviews**.

### The Final State

> A scientifically self-correcting knowledge organism that is still fully governed by human sovereignty.

Not alive. But no longer static.

---

## Dev Agent Record

### Context Reference
- Phase 9 implementation complete (DORMANT)
- See `docs/features/autonomous-knowledge-graph.md` for API documentation

### Agent Model Used
Antigravity (Gemini 2.5 Pro)

### Completion Notes List
- All 6 modules created: epistemic_engine.py, belief_tracker.py, stability_index.py, model_calibrator.py, hypothesis_generator.py, governance_node.py
- All 4 database tables created via Alembic migration
- All 8 API endpoints active
- DORMANT: Autonomous features disabled until Epic 9 governance complete

### File List
- src/jarvis/memory/epistemic_engine.py
- src/jarvis/memory/belief_tracker.py
- src/jarvis/memory/stability_index.py
- src/jarvis/memory/hypothesis_generator.py
- src/jarvis/memory/governance_node.py
- src/jarvis/llm/model_calibrator.py
- alembic/versions/569456b4b01a_add_phase_9_epistemic_tables.py
