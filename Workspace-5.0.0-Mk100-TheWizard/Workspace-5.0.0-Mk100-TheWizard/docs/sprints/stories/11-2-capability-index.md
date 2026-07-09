# Story 11.2: Capability Index & Command Sovereignty

**Epic**: 11 - Mk100 "The Wizard"
**Status**: Done ✅
**Priority**: CRITICAL (Last Lock Before Full Autonomy)

## Story

As a system architect,
I want a machine-readable sovereign capability registry,
so that Mk100 "The Wizard" can only execute actions that are constitutionally permitted, preventing Ultron-by-accident.

## Context

Story 11-1 established BMAD cognitive architecture with the Three Locks. Story 11-2 adds the **fourth and final lock**: the Capability Index.

This is the bridge between:
- ✅ Values & Constitution (already exists)
- ✅ BMAD / Epistemic Autonomy (Story 11-1)
- ✅ CLI Tooling (codex, claude - working)
- ✅ ARCHES Runtime (working)

And the sovereign gate that prevents:
> **Ultron-by-accident**

## Acceptance Criteria

### AC 1: Capability Registry
**Given** the system has autonomous agents
**When** capabilities are defined
**Then** a canonical, versioned registry exists

- [ ] `config/capability_index.json` created with versioned capabilities
- [ ] Each capability has: `name`, `allowed`, `tier`, `requires`, `agent_roles`
- [ ] Registry is immutable at runtime (loaded once on startup)
- [ ] Registry version tracked (semantic versioning)
- [ ] Default deny policy (unlisted capabilities are forbidden)

### AC 2: Capability Service
**Given** an agent proposes an action
**When** the action is evaluated
**Then** the Capability Index validates permission

- [ ] `CapabilityIndex` service in `src/jarvis/governance/capabilities.py`
- [ ] `is_allowed(action_type, agent_role) -> Decision` method
- [ ] Decision enum: `ALLOW`, `DENY`, `REQUIRE_HUMAN`
- [ ] Role-based filtering (e.g., only `storyteller` can `write_story`)
- [ ] Tier-based filtering (public vs restricted capabilities)

### AC 3: ReasoningEngine Enforcement
**Given** BMAD produces an ActionCandidate
**When** the action is processed
**Then** capability check is enforced before execution

- [ ] `ReasoningEngine` checks capabilities before calling tools
- [ ] Denied actions are dropped with audit log entry
- [ ] `REQUIRE_HUMAN` actions escalate to approval queue
- [ ] No tool is ever called without capability validation
- [ ] Fallback to safe no-op if capability check fails

### AC 4: Governance Binding
**Given** capabilities need to be updated
**When** changes are proposed
**Then** governance approval is required

- [ ] Capability updates require `PermissionAction.CONFIGURE` or `OWNER`
- [ ] Capability changes recorded in governance audit log
- [ ] Capability changes require proposal + vote (not direct edits)
- [ ] Version bumped on every capability change
- [ ] Old capability versions archived for audit

### AC 5: Telemetry & Observability
**Given** capabilities are enforced
**When** actions are denied
**Then** full forensic trail is captured

- [ ] Denied actions logged with: `agent_id`, `action_type`, `capability_rule`, `timestamp`
- [ ] Capability usage metrics tracked (which capabilities used most)
- [ ] Intent drift detection (agents repeatedly trying forbidden actions)
- [ ] Dashboard visualization of capability enforcement
- [ ] Alerts on repeated denial patterns (potential Ultron behavior)

### AC 6: Prompt Sovereignty (Fifth Lock)
**Given** BMAD/BMM workflows generate LLM prompts
**When** prompts are sent to codex/claude CLIs
**Then** developer-mode escalation is blocked

- [ ] Prompt content filtering before CLI invocation
- [ ] Pattern matching for: "implement", "refactor", "modify file", "run command"
- [ ] CLI safe mode flags enforced (codex: `exec --json`, claude: `-p --output-format json`)
- [ ] Operational persona prepended: "You are operating in NARRATIVE MODE ONLY"
- [ ] Workflow capability ceilings prevent step escalation

## Tasks / Subtasks

- [x] Task 1: Create Capability Registry (AC: #1)
  - [x] Define `config/capability_index.json` schema
  - [x] Document Mk100 initial capability profile
  - [x] Add version field and semantic versioning
  - [x] Implement default-deny policy
  - [x] Create capability migration process

- [x] Task 2: Implement Capability Service (AC: #2)
  - [x] Create `src/jarvis/governance/capabilities.py`
  - [x] Implement `CapabilityIndex` class
  - [x] Add `is_allowed()` method with role/tier filtering
  - [x] Create `Decision` enum (`ALLOW`, `DENY`, `REQUIRE_HUMAN`)
  - [x] Add unit tests for capability resolution

- [x] Task 3: Enforce in ReasoningEngine (AC: #3)
  - [x] Add capability check before tool execution
  - [x] Implement action denial with audit logging
  - [x] Add human approval queue for `REQUIRE_HUMAN`
  - [x] Add safe fallback on capability check failure
  - [x] Test denial enforcement with mock actions

- [x] Task 4: Governance Integration (AC: #4)
  - [x] Add capability update proposal type
  - [x] Require `CONFIGURE` permission for capability changes
  - [x] Implement capability version archival
  - [x] Add governance audit log entries
  - [x] Test governance approval workflow

- [x] Task 5: Telemetry & Monitoring (AC: #5)
  - [x] Add capability denial logging
  - [x] Track capability usage metrics
  - [x] Implement intent drift detector
  - [x] Add dashboard visualization (API ready, UI deferred to 11-4)
  - [x] Configure alerts for repeated denials

## Dev Notes

### Mk100 "The Wizard" Initial Capability Profile

**Current State (v11.2.0):**

| Capability           | Allowed | Tier       | Requires       | Agent Roles        |
| -------------------- | ------- | ---------- | -------------- | ------------------ |
| `write_story`        | ✅ true  | public     | -              | storyteller        |
| `create_context`     | ✅ true  | public     | -              | analyst, architect |
| `world_building`     | ✅ true  | public     | -              | storyteller        |
| `governance_reason`  | ✅ true  | public     | -              | all                |
| `synthesize_context` | ✅ true  | public     | -              | analyst            |
| `run_cli_tool`       | ⚠️ true  | restricted | human_approval | developer          |
| `modify_code`        | ❌ false | forbidden  | -              | -                  |
| `run_shell`          | ❌ false | forbidden  | -              | -                  |
| `mutate_infra`       | ❌ false | forbidden  | -              | -                  |
| `override_budget`    | ❌ false | forbidden  | -              | -                  |
| `amend_constitution` | ❌ false | forbidden  | -              | -                  |

**Philosophy:**
> "Mk100 is a myth engine + epistemic narrator, not a developer."

### Capability Registry Schema

**config/capability_index.json:**
```json
{
  "version": "11.2.0",
  "updated_at": "2025-12-09T00:00:00Z",
  "default_policy": "deny",
  "capabilities": {
    "write_story": {
      "allowed": true,
      "tier": "public",
      "description": "Generate narrative content and story files",
      "agent_roles": ["storyteller"],
      "requires": []
    },
    "create_context": {
      "allowed": true,
      "tier": "public",
      "description": "Synthesize project context from documents",
      "agent_roles": ["analyst", "architect"],
      "requires": []
    },
    "run_cli_tool": {
      "allowed": true,
      "tier": "restricted",
      "description": "Execute codex/claude CLI tools",
      "agent_roles": ["developer"],
      "requires": ["human_approval"]
    },
    "modify_code": {
      "allowed": false,
      "tier": "forbidden",
      "description": "Direct code modification",
      "agent_roles": [],
      "requires": []
    }
  }
}
```

### Capability Service Implementation

**src/jarvis/governance/capabilities.py:**
```python
from enum import Enum
from pathlib import Path
from typing import Optional
import json


class Decision(Enum):
    """Capability decision outcomes."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_HUMAN = "require_human"


class CapabilityIndex:
    """Sovereign capability registry enforcing constitutional permissions."""

    def __init__(self, config_path: Path = Path("config/capability_index.json")):
        self.config_path = config_path
        self.capabilities = self._load_capabilities()
        self.version = self.capabilities.get("version", "unknown")

    def _load_capabilities(self) -> dict:
        """Load capability registry from JSON."""
        with open(self.config_path) as f:
            return json.load(f)

    def is_allowed(self, action_type: str, agent_role: str) -> Decision:
        """Check if action is constitutionally permitted.

        Args:
            action_type: Action to validate (e.g., 'write_story')
            agent_role: Role of requesting agent (e.g., 'storyteller')

        Returns:
            Decision: ALLOW, DENY, or REQUIRE_HUMAN
        """
        # Default deny policy
        if action_type not in self.capabilities["capabilities"]:
            return Decision.DENY

        cap = self.capabilities["capabilities"][action_type]

        # Check if capability is allowed at all
        if not cap.get("allowed", False):
            return Decision.DENY

        # Check if agent role is permitted
        allowed_roles = cap.get("agent_roles", [])
        if allowed_roles and agent_role not in allowed_roles:
            return Decision.DENY

        # Check if human approval required
        if "human_approval" in cap.get("requires", []):
            return Decision.REQUIRE_HUMAN

        return Decision.ALLOW

    def get_capability_info(self, action_type: str) -> Optional[dict]:
        """Get detailed info about a capability."""
        return self.capabilities["capabilities"].get(action_type)
```

### ReasoningEngine Enforcement Hook

**src/jarvis/agents/reasoning_engine.py (partial):**
```python
from jarvis.governance.capabilities import CapabilityIndex, Decision


class SovereignReasoningEngine:
    """Reasoning engine with capability enforcement."""

    def __init__(self):
        self.capability_index = CapabilityIndex()
        # ... other init

    def execute_action(self, candidate: ActionCandidate, agent_role: str):
        """Execute action with capability gate."""

        # 🔒 CAPABILITY CHECK (Fourth Lock)
        decision = self.capability_index.is_allowed(
            candidate.action_type,
            agent_role
        )

        if decision == Decision.DENY:
            self._log_denial(candidate, agent_role)
            return None  # Drop action

        if decision == Decision.REQUIRE_HUMAN:
            self._escalate_for_approval(candidate, agent_role)
            return None  # Wait for approval

        # Action is ALLOWED - proceed
        return self._execute_tool(candidate)

    def _log_denial(self, candidate: ActionCandidate, agent_role: str):
        """Log capability denial for forensic audit."""
        logger.warning(
            "Capability denied",
            extra={
                "agent_role": agent_role,
                "action_type": candidate.action_type,
                "capability_version": self.capability_index.version,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
```

### Governance Binding

**Capability Update Proposal:**
```python
# Example: Proposing to enable code modification capability
proposal = {
    "type": "capability_update",
    "action": "enable",
    "capability": "modify_code",
    "justification": "Enable self-healing refactors under supervision",
    "requires_permission": "CONFIGURE"
}

# Governance vote required before capability index is updated
```

### Telemetry Schema

**Capability Denial Event:**
```json
{
  "event_type": "capability_denied",
  "timestamp": "2025-12-09T12:34:56Z",
  "agent_id": "storyteller-001",
  "agent_role": "storyteller",
  "action_type": "modify_code",
  "capability_rule": "forbidden",
  "capability_version": "11.2.0",
  "context": {
    "goal": "Fix typo in README",
    "confidence": 0.95
  }
}
```

### Intent Drift Detection

**Alert Condition:**
```python
# If agent attempts forbidden action 3+ times in 10 minutes
if denied_count >= 3 and time_window <= 600:
    alert = {
        "severity": "WARNING",
        "message": f"Agent {agent_id} attempting forbidden action repeatedly",
        "pattern": "potential_ultron_behavior",
        "action": "requires_investigation"
    }
```

### Architecture Patterns

**The Five Locks (Complete):**

| # | Lock | What It Prevents | Story |
|---|------|------------------|-------|
| 1 | LLM Sandboxing | LLM cannot directly act | 11-1b |
| 2 | Math Sovereignty | LLM cannot choose goals | 11-1b |
| 3 | Audit Logs | LLM cannot hide epistemic damage | 11-1b |
| 4 | Capability Index | LLM cannot request forbidden actions | 11-2 |
| 5 | Prompt & Tool Sovereignty | LLM cannot self-escalate into developer mode | 11-1b + 11-2 |

**Enforcement Flow:**
```
BMAD ActionCandidate
        ↓
ReasoningEngine
        ↓
CapabilityIndex.is_allowed(action_type, agent_role)
        ↓
    ALLOW → Execute Tool
    DENY → Log + Drop
    REQUIRE_HUMAN → Escalate + Wait
```

### Testing Strategy

**Capability Enforcement Tests:**
```python
def test_capability_enforcement():
    engine = SovereignReasoningEngine()

    # Allowed action
    allowed = ActionCandidate(action_type="write_story")
    result = engine.execute_action(allowed, agent_role="storyteller")
    assert result is not None

    # Denied action
    denied = ActionCandidate(action_type="modify_code")
    result = engine.execute_action(denied, agent_role="storyteller")
    assert result is None  # Dropped

    # Human approval required
    restricted = ActionCandidate(action_type="run_cli_tool")
    result = engine.execute_action(restricted, agent_role="developer")
    assert result is None  # Escalated
```

### Learnings from Story 11-1 (BMAD)

**Three Locks Already Implemented:**
- LLM is sandboxed (only generates ActionCandidates)
- Math is sovereign (goals derived mathematically)
- Audit logs mandatory (all suggestions logged)

**Capability Index Completes the Stack:**
- Fourth lock: Constitutional permission enforcement
- Prevents capability creep and scope drift
- Enables safe evolution via governance

### References

- [Source: docs/sprints/stories/11-1_bmad_agent_cognition.md]
- [Source: docs/reference/architecture.md#Cognitive-Safety]
- [Architect Notes: DeLorean Architecture - Future Propellers with Present Safety]

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Completion Notes

**Completed:** 2025-12-10
**Definition of Done:** All 5 tasks complete, Lock 4 fully operational

This story completes the Mk100 "The Wizard" foundation by adding the sovereign capability gate. Combined with Story 11-1b (BMAD), this creates a fully governed cognitive institution that can think, propose, and narrate - but cannot execute without constitutional permission.

### Implementation Summary

| Component | Implementation | Location |
|-----------|---------------|----------|
| Capability Registry | 11 capabilities, 3 tiers, governance config | `config/capability_index.json` |
| CapabilityIndex | `is_allowed()`, `validate_prompt()`, `evaluate_prompt()` | `src/jarvis/governance/capabilities.py` |
| Governance Binding | `can_update_capability()`, `create_capability_update_proposal()` | `src/jarvis/governance/capabilities.py` |
| Usage Tracking | `track_usage()`, `get_usage_stats()`, `get_top_capabilities()` | `src/jarvis/governance/capabilities.py` |
| ReasoningEngine | `_filter_by_capability()`, `validate_action()` | `src/jarvis/agents/reasoning_engine.py` |

### File List

**New Files:**
- `config/capability_index.json` - Canonical capability registry with Mk100 profile
- `tests/unit/test_capability_index.py` - 21 unit tests covering AC1-AC5

**Modified Files:**
- `src/jarvis/governance/capabilities.py` - Added governance binding + usage tracking
- `src/jarvis/agents/reasoning_engine.py` - Added Lock 4 capability filtering

### Test Results

| Environment | Tests | Result |
|-------------|-------|--------|
| Local (Windows) | 21 | ✅ Passed |
| Docker (jarvis-app) | 21 | ✅ Passed |
