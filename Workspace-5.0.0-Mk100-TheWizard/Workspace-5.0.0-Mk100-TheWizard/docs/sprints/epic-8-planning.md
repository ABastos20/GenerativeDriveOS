# Epic 8: Epistemic Infrastructure & Cognitive Governance

**Status:** In Progress
**Goal:** Build self-improving, self-doubting knowledge infrastructure with truth maintenance, graph algorithms, and epistemic autonomy while enforcing strict safety constraints.

---

## Architect Notes (The "Safety First" Mandate)

> "You are no longer building a chatbot. You have a Cognitive OS. Now we are giving it Hands."

### The Three Risks
1.  **Hot-Reload Without Rollback = Self-Bricking**: If Jarvis breaks its own config, it must be able to revert automatically.
2.  **Manual Tests Will Not Survive**: We need automated regression suites (pytest) before self-improvement starts.
3.  **Observability Must Exit the Log File**: We need a dashboard to see "Health" at a glance.

---

## Story Breakdown

### 8-1: Capability Registry & Gap Detection
- **Goal**: Jarvis can scan its own tools/prompts and identify missing capabilities.
- **Mechanism**: `CapabilityRegistry` class + `GapDetector` agent.

### 8-2: BMAD Invocation Pipeline
- **Goal**: Standardized way to invoke "Build/Make/Analyze/Deploy" actions.
- **Mechanism**: `PipelineExecutor` that runs safe, sandboxed commands.

### 8-3: Auto-Testing & Safe Hot-Reload
- **Goal**: Apply changes without restarting the container (where possible) or safe restart.
- **Constraint**: MUST have a "Last Known Good" snapshot and auto-revert on failure.

### 8-4: Improvement Tracking
- **Goal**: Notification system for "I improved X".

### 8-5: Code Quality Enforcement (New)
- **Goal**: Prevent "God Classes" and unmaintainable code.
- **Rules**:
    - Max 800 LOC per file.
    - Max 20 methods per class.
    - Cyclomatic complexity limits.
- **Mechanism**: `scripts/lint_check.py` or pre-commit hook that Jarvis runs on itself.

### 8-6: Safety, Testing & Observability Foundation ✅
- **Goal**: The "Immune System" for Epic 8.
- **Deliverables**:
    - **Safe Mode**: Boot flag `--safe` to load minimal config.
    - **Rollback**: `jarvis restore <snapshot_id>`.
    - **Pytest Suite**: `tests/integration/` covering memory, retrieval, and planning.
    - **Admin Dashboard**: `/admin/health` endpoint and UI.

### 8-7: Autonomous Knowledge Graph ✅
- **Goal**: Self-discovering, self-organizing knowledge infrastructure.
- **Deliverables**:
    - **Graph Enrichment**: LLM-based entity/relationship extraction
    - **Cognitive Cockpit**: Interactive visualization (Cytoscape.js)
    - **PageRank**: Entity importance scoring
    - **Louvain Clustering**: Community detection
    - **Shortest Paths**: Connection finding
    - **Cluster UX**: Expand/collapse animations

### 8-8: Epistemic Autonomy Layer (Phase 9) 📋
- **Goal**: Closed-loop epistemic organism with truth maintenance.
- **Deliverables**:
    - **Contradiction Detection**: A → B and A → ¬B across time/sources
    - **Belief Timeline**: Temporal belief tracking per entity
    - **Cognitive Stability Index (CSI)**: Quantitative stability metric
    - **Model Calibration**: Dynamic model selection per domain
    - **Hypothesis Generator**: Auto-generate testable hypotheses
    - **Human Governance Node**: Escalation when CSI < threshold
- **Motto**: "The system learns how to doubt itself."

---

## Execution Plan

1.  **Foundation (8-6)**: Build the safety net FIRST. ✅ COMPLETE
2.  **Enforcement (8-5)**: Ensure the codebase remains clean. ✅ COMPLETE
3.  **Knowledge Graph (8-7)**: Self-discovering memory. ✅ COMPLETE
4.  **Epistemic Layer (8-8)**: Truth maintenance & self-doubt. 📋 NEXT
5.  **Capabilities (8-1, 8-2)**: Build the registry and pipeline.
6.  **Autonomy (8-3, 8-4)**: Turn on the self-improvement loop.
