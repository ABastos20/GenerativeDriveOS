# Story 11-8 — Epic 11 Closure & Activation of Epic 8-8

**Epic**: 11 – Mk100 "The Wizard"
**Story ID**: 11-8
**Status**: Ready 📋
**Priority**: CRITICAL (Epic Closure)
**Depends On**: 11-1 → 11-7, 11-5.1 → 11-5.4
**Unlocks**: Epic 8-8 – *LLM Governance & Research-Oriented Context Optimisation*
**Type**: Governance / Integration / Epic Finalisation

> *"Seal the Sovereign Cognitive Engine."*

---

## Story

As a Jarvis Chief Architect,
I want **a formal verification & activation checklist that closes Epic 11 and unlocks Epic 8-8 safely**,
So that **the system enters Sovereign Knowledge Mode, enabling advanced research agents, long-horizon context optimisation, and safe multi-tenant ingestion pipelines**.

---

## Context

Epic 11 introduced:
- 5 Locks → extended to **7 Locks**
- Tiered knowledge lattice (K0-K4)
- Provenance ledger
- Dual-persona arbitration
- Trust decay model
- Usage policy
- Audit sinks (in-memory + stdout + postgres)
- Full BMAD/BMM rule integration

Story 11-8 validates, signs off, activates the epic, and toggles the system into **Sovereign Mode** required by Epic 8-8.

---

## Acceptance Criteria

### AC 1: All Prior Stories Complete

**Given** Epic 11 stories 11-1 through 11-7 plus 11-5.x substories
**When** checking sprint status
**Then** all are marked `done` with verified tests

**Implementation:**
- [ ] All 11-x stories in `sprint-status.yaml` = done
- [ ] Test suites pass for each story
- [ ] Code reviews completed

---

### AC 2: Sovereign Mode Switch (Fail-Closed)

**Given** Epic 11 invariants should be mandatory in production
**When** activating Sovereign Mode
**Then** all Locks 1-7 are globally enforced with fail-closed semantics

**Implementation:**
```python
# config/sovereign_mode.py
from pydantic_settings import BaseSettings

class SovereignSettings(BaseSettings):
    sovereign_mode: bool = True  # default ON in prod, OFF in tests/dev if you want
    
    # Effects when enabled:
    # - Persona arbitration required for tier promotions
    # - Usage policy enforced at runtime
    # - Contradiction penalties active
    # - All audit sinks receive events
    # - Provenance freeze rules active
    # - BMAD memory strictness enabled

settings = SovereignSettings()
```

**Fail-Closed Semantics:**
> If `sovereign_mode = True` and any required sub-components (usage policy, arbitration, trust engine, audit sinks) fail to initialise, the system **MUST fail-closed**:
> - No tier promotions allowed
> - Logs a critical event
> - Serves only low-risk advisory responses

- [ ] Create `config/sovereign_mode.py` with Pydantic settings
- [ ] Wire into arbitration, trust engine, usage policy
- [ ] Implement fail-closed fallback when dependencies unavailable
- [ ] Tests verify mode enables/disables correctly
- [ ] Tests verify fail-closed behavior on dependency failure

---

### AC 3: Knowledge Tiers Validated

**Given** K0-K4 tier lattice is implemented
**When** validating tier usage
**Then** ingestion, usage policy, and BMAD respect tier semantics

**Implementation:**
- [ ] K4 (External Raw) treated as noise by BMAD
- [ ] K3 (Reviewed) treated as narrative
- [ ] K2+ (Certified) treated as epistemically valid
- [ ] Tier transitions logged to audit

---

### AC 4: Provenance Integrity CLI

**Given** epistemic events form a hash chain
**When** running integrity verification
**Then** CLI reports chain validity with deterministic exit codes

**Exit Codes:**
- `exit 0` = full integrity verified
- `exit 1` = broken chain, inconsistent tiers, or missing events

**Implementation:**
```bash
jarvis provenance verify
# Checks: ledger chain, event order, hash deltas, tier consistency
# Returns: exit 0 on success, exit 1 on any failure
```

- [ ] Add `jarvis provenance verify` command via Typer
- [ ] Validate event ordering and hash chain
- [ ] Return exit code 0 on success, 1 on failure
- [ ] Report issues list on failure for debugging

---

### AC 5: Dual-Persona Freeze Semantics

**Given** Analyst and Adversary personas evaluate promotions
**When** they disagree or fail
**Then** knowledge is frozen correctly

**Implementation:**
- [ ] Analyst approves + Adversary denies → freeze
- [ ] LLM error → freeze (graceful degradation)
- [ ] Frozen knowledge excluded from BMAD

---

### AC 6: Trust Engine Validated

**Given** trust decay formula T_s = w_c*C + w_r*R + w_v*V + w_p*P
**When** time passes without refresh
**Then** trust decays predictably

**Implementation:**
- [ ] Decay formula verified with deterministic tests
- [ ] Refresh resets decay timer
- [ ] Domain weights configurable

---

### AC 7: Audit Sinks Tested

**Given** multiple sink backends configured
**When** logging epistemic events
**Then** all sinks receive events with graceful degradation

**Implementation:**
- [ ] In-memory sink functional
- [ ] Stdout JSON sink functional
- [ ] PostgreSQL sink functional (with table created)
- [ ] Sink failure doesn't crash pipeline

---

### AC 8: Epic 8-8 Activation Gate (Mechanical Precondition)

**Given** AC1-AC7 all pass
**When** 11-8 is marked complete
**Then** Epic 8-8 becomes officially unlocked

**Mechanical Enforcement:**
> Any workflow tagged `epic=8-8` **MUST** check `.bmad/bmm/env/sovereign.json` and refuse execution if `sovereign=false` or 11-8 incomplete.

**Implementation:**
- [ ] Create `.bmad/bmm/env/sovereign.json` declaring stability
- [ ] Include: `{"sovereign": true, "epic": 11, "version": "5.0.0", "locks": [1,2,3,4,5,6,7]}`
- [ ] Create `docs/sprints/stories/8-8-*.md` story template with `locked-by: 11-8`
- [ ] Update `sprint-status.yaml` with 8-8 epic marked `locked-by: 11-8`

---

### AC 9: Integration Report

**Given** Epic 11 is complete
**When** generating closure report
**Then** summary includes code coverage, story mapping, lock verification

**Implementation:**
- [ ] Generate integration report
- [ ] Document in walkthrough
- [ ] Archive any remaining tech debt

---

## Tasks / Subtasks

- [ ] Task 1: Implement Sovereign Mode Config (AC: #2)
  - [ ] Create `config/sovereign_mode.py`
  - [ ] Wire into arbitration, trust, usage policy
  - [ ] Add tests for mode toggle

- [ ] Task 2: Provenance Integrity CLI (AC: #4)
  - [ ] Add `jarvis provenance verify` command
  - [ ] Implement chain validation
  - [ ] Add CLI tests

- [ ] Task 3: Sink Fan-Out Verification (AC: #7)
  - [ ] Test in-memory sink isolation
  - [ ] Test stdout + in-memory combo
  - [ ] Test postgres failure graceful degradation

- [ ] Task 4: End-to-End Freeze Path Tests (AC: #5)
  - [ ] Simulate persona disagreement
  - [ ] Verify freeze event logged
  - [ ] Verify BMAD exclusion

- [ ] Task 5: BMAD Binding Enforcement (AC: #3)
  - [ ] Verify tier treatment in reasoning
  - [ ] Test hypothesis creation = K4
  - [ ] Test usage policy integration

- [ ] Task 6: Activate Epic 8-8 (AC: #8)
  - [ ] Create sovereign.json
  - [ ] Create 8-8 story template
  - [ ] Update sprint status

- [ ] Task 7: Final Integration Report (AC: #9)
  - [ ] Generate summary
  - [ ] Document completion
  - [ ] Archive tech debt items

---

## Sovereign Mode Definition

```python
sovereign_mode = True
```

**Effects when enabled:**
- Disables heuristic shortcuts
- Enforces persona arbitration for all tier promotions
- Enforces usage policy at runtime
- Enables contradiction penalties
- Routes audit events to all configured sinks
- Enables provenance freeze rules
- Activates memory strictness in BMAD

**Sovereign Mode = Epic 11 invariants are now mandatory, not optional.**

---

## Master Checklist (Ship / No-Ship Gate)

### 🧠 Lock 1-3 (Cognitive Core)
- [ ] LLM sandboxed (no direct mutations)
- [ ] Math sovereignty (goal = argmax formula)
- [ ] All actions have audit telemetry

### 🛡️ Lock 4 (Capability Index)
- [ ] Registry default = deny
- [ ] Enforcement real (no bypass)
- [ ] Governance binding (changes require votes)

### 🔥 Lock 5 (Semantic Firewall)
- [ ] Prompt safety patterns active
- [ ] Deny = never reaches provider
- [ ] Narrative-only persona enforced

### 🧠 Lock 6 (C-IDS Emergent)
- [ ] Code index functional
- [ ] Abuse patterns defined
- [ ] Intent drift detection active

### 📚 Lock 7 (Epistemic Sovereignty)
- [ ] Evidence ledger with T_s formula
- [ ] Answer trust exposed
- [ ] Knowledge graph operational

### 📥 Lock 7+ (Trust-Aware Ingestion)
- [ ] Manifests versioned
- [ ] Quarantine functional
- [ ] Metrics exposed

### ♻️ Lock 7++ (Knowledge Lifecycle)
- [ ] States: raw → reviewed → vetted → deprecated → revoked
- [ ] Promotion/demotion logged
- [ ] Conflict detection active

---

## File List

**New Files:**
- `config/sovereign_mode.py` - Sovereign mode configuration
- `src/jarvis/cli/provenance.py` - Provenance verification CLI
- `.bmad/bmm/env/sovereign.json` - Epic 11 stability declaration

**Modified Files:**
- `docs/sprints/sprint-status.yaml` - Add 11-8 and 8-8 entries

---

## References

- [Epic 11 Overview](../epics/epic-11-wizard.md)
- [Lock 7: Epistemic Sovereignty](11-5-knowledge-sovereignty.md)
- [Unlocks: Epic 8-8](8-8-governance-context-optimization.md)
