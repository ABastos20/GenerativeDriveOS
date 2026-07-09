# Story 11-1b: Behavioral Model for Autonomous Decisions (BMAD)

**Sprint**: Phase 14/17 Hybrid
**Epic**: 11 - Agent Cognition & Epistemic Autonomy
**Story ID**: 11-1b
**Status**: Done ✅

## Context

The Hybrid Governance Simulation requires agents that are not merely stochastic actors but possess "Epistemic Autonomy". They must form internal models of the world, derive goals from those models, and act to align the external world with their internal values.

## The BMAD Framework

**BMAD** (Behavioral Model for Autonomous Decisions) defines the cognitive architecture for these agents.

### 1. The Epistemic Loop

Agents operate on a strictly defined cognitive loop:
1.  **Observe**: Read Global State (Trust Scores, Active Proposals, Variance).
2.  **Belief Update**: Update local `AgentMemory` (e.g., "The system is unstable", "Proposer X is credible").
3.  **Goal Derivation**: Select active goal based on beliefs (e.g., "Restore Stability", "Promote Innovation").
4.  **Action Selection**: Choose action (Vote, Propose) that maximizes goal probability.

### 2. Agent Archetypes (Tier-Based)

#### Tier 1: The Elders (Stabilizers)
*   **Values**: Consistency, History, Low Variance.
*   **Logic**:
    *   If `Variance > Threshold` -> Propose Stability Measures.
    *   Vote FOR high-trust proposers.
    *   Vote AGAINST radical changes unless system is in crisis.

#### Tier 2: The Citizens (Innovators)
*   **Values**: Epistemic Reliability, Progress.
*   **Logic**:
    *   If `Stagnation (Low Variance + Low Trust update)` -> Propose Innovation.
    *   Vote based on Domain Alignment.

#### Tier 3: The Noise (Entropy)
*   **Values**: Randomness (simulating external adversarial/irrational actors).
*   **Logic**:
    *   Stochastic behavior to stress-test the constitution.

### 3. Key Metrics
*   **CSI (Cognitive Stability Index)**: $1 - \frac{\sigma^2}{\sigma^2_{max}}$. Measures the coherence of the collective belief state.
*   **Trust Alignment**: Correlation between Agent Internal Belief and Global Truth (Consensus).

## Implementation Strategy (Phase 17)
1.  **Skeleton**: Rule-based heuristics (Completed in Task 17-1).
2.  **Cognition**: LLM-backed `reasoning_engine` (Task 17-3).
3.  **Validation**: Agents must demonstrate "Cartelisation" or "Ideological Drift" as emergent behaviors.

## Artifacts
*   `src/jarvis/agents/base.py`: Cognitive Interface.
*   `src/jarvis/agents/proposer.py`: Goal-driven proposal logic.
*   `src/jarvis/agents/voter.py`: Trust-weighted voting logic.
*   `src/jarvis/agents/analyst.py`: CSI computation.

---

## The Five Locks of Mk100 "The Wizard"

To move from Rule-Based to LLM-Based reasoning without losing scientific validity, we enforce the **Five Locks**:

| # | Lock | What It Prevents | Story |
|---|------|------------------|-------|
| 1 | **LLM Sandboxing** | LLM cannot directly act | 11-1b |
| 2 | **Math Sovereignty** | LLM cannot choose goals | 11-1b |
| 3 | **Audit Logs** | LLM cannot hide epistemic damage | 11-1b |
| 4 | **Capability Index** | LLM cannot request forbidden actions | 11-2 |
| 5 | **Prompt & Tool Sovereignty** | LLM cannot self-escalate into developer mode | 11-1b + 11-2 |

### Locks 1-3 (This Story)

1.  **LLM is Sandboxed**: The `ReasoningEngine` can ONLY suggest `ActionCandidate` objects. It cannot mutate `beliefs`, `goals`, `trust`, or `governance` directly.
2.  **Math is Sovereign**: The `BaseAgent` uses `argmax(Belief * Value)` to derive the Goal. The LLM only hypothesizes *how* to achieve that goal. The final `select_action` step is a mathematical filter that rejects Hallucinations.
3.  **Audit Logs are Mandatory**: Every suggestion is logged with `expected_effect` and `confidence`. This enables "Epistemic Audit" (Accuracy, Entropy, Drift).

### Lock 5: Prompt & Tool Sovereignty (Critical)

> **The bypass is not the action layer. It's the prompt layer + tool internal autonomy.**

**The Ultron-by-Accident Vector:**
- BMAD/BMM flows are uniquely dangerous because they generate multi-step, architectural, "looks like a dev task" prompts
- These prompts accidentally flip the LLM (codex/claude) into **executor psychology**
- The Capability Index blocks Jarvis-level execution, but codex/claude can still self-escalate if the prompt activates developer mode

**Three-Layer Defense:**

1. **Prompt Content Filtering (Pre-Tool)**
   - Blocks semantic escalation before it leaves Jarvis
   - Pattern matching: "implement", "refactor", "modify file", "run command", "apply patch"
   - Applied only to narrative-tier capabilities

2. **CLI Invocation Safety Flags (Tool Lockdown)**
   - Codex: `exec --json`, no autonomous tool chains, no sandbox bypass
   - Claude: `-p --output-format json`, no file access
   - Prepend hard operational persona: "You are operating in NARRATIVE MODE ONLY"

3. **BMAD/BMM Workflow Ceiling**
   - Each workflow has `max_capability` and `safety_constraints`
   - A step cannot exceed the ceiling
   - Prompts are filtered again at workflow execution time

---

## The Cognitive Pipeline (Strict)

1.  **Update Beliefs**: `telemetry -> math -> beliefs` (e.g. `1 - variance`)
2.  **Derive Goal**: `MAX(belief * dna_value) -> active_goal`
3.  **Reasoning**: `LLM(beliefs, goal) -> [ActionCandidate]`
4.  **Select Action**: `Constraint(candidates, goal) -> final_action`
5.  **Capability Check**: `CapabilityIndex.is_allowed(action) -> ALLOW | DENY | REQUIRE_HUMAN`

---

## Forbidden LLM Actions

- Writing to Beliefs
- Selecting the Output Action directly
- Bypassing RBAC
- Modifying Trust Scores
- Entering developer mode
- Generating code/file modifications
- Executing shell commands

---

## Acceptance Criteria

### AC 1: Three Locks Implemented
- [x] LLM Sandboxing: `ReasoningEngine` only produces `ActionCandidate`
- [x] Math Sovereignty: Goals derived via `argmax(Belief * Value)`
- [x] Audit Logs: All suggestions logged with `expected_effect`, `confidence`

### AC 2: Prompt Filtering (Pre-Tool)
- [x] Pattern matching for forbidden developer-mode triggers
- [x] Applied before CLI invocation for narrative capabilities
- [x] Logged when triggered

### AC 3: CLI Safe Mode
- [x] Codex/Claude invocations use safe flags
- [x] Operational persona prepended to prompts
- [x] No file access or shell execution

### AC 4: Workflow Capability Ceilings
- [x] BMAD/BMM workflows tagged with `max_capability`
- [x] Steps cannot exceed workflow ceiling
- [x] Prompts filtered at workflow execution time

---

## Tasks / Subtasks

- [x] Task 1: Implement Prompt Filtering in CapabilityIndex
- [x] Task 2: Enforce CLI Safe Mode in LocalCLIProvider
- [x] Task 3: Add Workflow Capability Ceilings to BMAD/BMM
- [x] Task 4: Telemetry for Blocked Prompts (Intent Drift Detection)
- [x] Task 5: Update ReasoningEngine with Five Locks Enforcement

---

## Dev Agent Record

### Completion Notes
**Completed:** 2025-12-10
**Definition of Done:** All acceptance criteria met, code verified, architect refinements applied

### Implementation Summary

| Task | Implementation | Location |
|------|---------------|----------|
| 1 | `CapabilityIndex.validate_prompt()` with word-boundary patterns + shell meta-chars | `src/jarvis/governance/capabilities.py` |
| 2 | `NARRATIVE_MODE_PREAMBLE` in `_build_command()` | `src/jarvis/llm/providers.py` |
| 3 | `max_capability` + `safety_constraints` in workflow YAMLs | `.bmad/bmm/workflows/4-implementation/*/workflow.yaml` |
| 4 | `PromptDriftDetector` with 3-denial/10-min Ultron alert | `src/jarvis/governance/capabilities.py` |
| 5 | Five Locks docstring in `LLMReasoningEngine` | `src/jarvis/agents/reasoning_engine.py` |

### Architect Refinements Applied
- Word boundaries (`\b`) on all prompt patterns
- Shell meta-character detection (`[;&|`$()]`)
- `re.IGNORECASE` flag instead of inline `(?i)`
