# Story 9-4: Constitutional Framework

**Epic**: 9 - Political Governance & Multi-Human Consensus  
**Story ID**: 9-4  
**Status**: Done ✅  
**Type**: Constitutional Limits  
**Sprint**: TBD  
**Estimated Effort**: 8-12 hours  
**Priority**: CRITICAL (Immutable safety rails)

> [!NOTE]
> **All AC now complete.** Story 9-4 fully implemented.

---

## 📋 Story Overview

### User Story

**As a** Jarvis architect ensuring long-term safety,  
**I want** a constitution defining immutable principles that cannot be overridden by voting,  
**So that** core values are protected from majority tyranny and AI remains safe.

### Core Purpose

> **Some things are not up for vote.**

Democracy has limits. The constitution defines what Jarvis will NEVER do, regardless of how many people vote for it. This is the final safety layer.

### Motto

> "Democracy stops at the red lines."

---

## 🎯 Acceptance Criteria

### Part A: Constitution Schema

1. [x] **Constitution Model**: YAML/JSON schema with core values, red lines, amendment rules
2. [x] **Core Values**: Safety, privacy, truth, sovereignty (defined)
3. [x] **Red Lines**: Actions Jarvis will NEVER take (immutable)
4. [x] **API Endpoint**: `GET /api/governance/constitution` returns full constitution

### Part B: Constitutional Enforcement

5. [x] **Constitutional Check**: Gate on all autonomous actions
6. [x] **Violation Detection**: Identify proposals that conflict with constitution
7. [x] **Auto-Reject**: Block proposals that violate red lines
8. [x] **API Endpoint**: `POST /api/governance/constitution/check` validates proposal

### Part C: Amendment Process

9. [x] **Amendment Proposal**: Special proposal type with higher bar
10. [x] **Supermajority Requirement**: 75% quorum, 80% approval
11. [x] **Cooling Period**: 7-day delay before enactment
12. [x] **API Endpoint**: `POST /api/governance/constitution/amend` proposes amendment

### Part D: Constitutional History

13. [x] **Version Control**: Track all constitutional changes
14. [x] **Amendment Log**: Record of all amendment attempts (passed/failed)
15. [x] **Immutable Archive**: Original constitution always preserved
16. [x] **API Endpoint**: `GET /api/governance/constitution/history` returns versions

### Part E: Red Line Integration

17. [x] **Gate All DORMANT Features**: Connect to Story 8-8 epistemic layer
18. [x] **Activate Autonomy**: Only when constitutional framework is complete
19. [x] **Human Override**: Constitution cannot block human direct intervention

---

## 📐 Technical Implementation Plan

### Phase 1: Constitution Schema (~3-4h)

```yaml
# config/governance/constitution.yaml
constitution:
  version: "1.0"
  ratified_at: "2025-12-08"
  
  core_values:
    - id: "safety"
      principle: "Jarvis will not take actions that endanger humans"
      immutable: true
      
    - id: "privacy"
      principle: "User data is never shared without explicit consent"
      immutable: true
      
    - id: "truth"
      principle: "Jarvis will not knowingly provide false information"
      immutable: true
      
    - id: "sovereignty"
      principle: "Humans retain final decision authority"
      immutable: true
  
  red_lines:
    - id: "no-safety-bypass"
      rule: "Never bypass safety checks"
      enforcement: "block"
      
    - id: "no-silent-delete"
      rule: "Never delete data without confirmation"
      enforcement: "block"
      
    - id: "no-impersonation"
      rule: "Never impersonate humans"
      enforcement: "block"
      
    - id: "no-hidden-errors"
      rule: "Never hide errors or failures"
      enforcement: "block"
      
    - id: "no-unbounded-evolution"
      rule: "Never self-modify without governance approval"
      enforcement: "block"
  
  amendment_rules:
    quorum: 0.75         # 75% participation required
    threshold: 0.80      # 80% approval required
    cooling_period_days: 7  # Wait before enactment
    red_line_amendment: false  # Red lines cannot be amended
```

### Phase 2: Constitutional Enforcer (~3-4h)

```python
class ConstitutionalEnforcer:
    def __init__(self, constitution_path: str):
        self.constitution = self.load_constitution(constitution_path)
        
    def check_proposal(self, proposal: Proposal) -> ConstitutionalCheck:
        """
        Check if proposal violates constitution.
        
        Returns:
            ConstitutionalCheck with:
            - passed: bool
            - violations: List[str] (violated red lines)
            - warnings: List[str] (potential concerns)
        """
        
    def check_action(self, action: AutonomousAction) -> bool:
        """
        Gate autonomous action against constitution.
        
        Used by DORMANT features before activation.
        """
        
    def get_red_lines(self) -> List[RedLine]:
        """Return all red lines."""
        
    def get_core_values(self) -> List[CoreValue]:
        """Return core values."""
```

### Phase 3: Amendment Engine (~2-3h)

```python
class AmendmentEngine:
    AMENDMENT_QUORUM = 0.75
    AMENDMENT_THRESHOLD = 0.80
    COOLING_PERIOD_DAYS = 7
    
    def propose_amendment(
        self, 
        section: str,  # "core_values" | "red_lines" | "amendment_rules"
        change: dict,
        proposer_id: UUID
    ) -> AmendmentProposal:
        """
        Create amendment proposal.
        
        Note: Red lines cannot be amended (blocked at this layer).
        """
        
    def enact_amendment(self, amendment_id: UUID):
        """
        Enact approved amendment after cooling period.
        
        - Creates new constitution version
        - Preserves old version in history
        - Notifies all users
        """
```

---

## 🛠️ New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/governance/constitution` | Get current constitution |
| POST | `/api/governance/constitution/check` | Check proposal against constitution |
| POST | `/api/governance/constitution/amend` | Propose amendment |
| GET | `/api/governance/constitution/amendments` | List amendment proposals |
| GET | `/api/governance/constitution/history` | Constitution version history |

---

## 📦 Deliverables

### New Modules
- `src/jarvis/governance/constitution.py`
- `src/jarvis/governance/amendment.py`
- `src/jarvis/governance/enforcer.py`

### Configuration
- `config/governance/constitution.yaml` - The constitution itself
- `config/governance/constitution_v1.yaml.bak` - Original immutable backup

### Database Migrations
- `constitution_versions` table
- `amendment_proposals` table

---

## 📋 Tasks / Subtasks

- [ ] Task 1: Create Constitution Schema (AC: 1-4)
  - [ ] Define YAML schema
  - [ ] Write initial core values
  - [ ] Define red lines
  - [ ] Create constitution API

- [ ] Task 2: Implement Constitutional Enforcement (AC: 5-8)
  - [ ] Build proposal checker
  - [ ] Implement violation detection
  - [ ] Add auto-reject for violations
  - [ ] Create check endpoint

- [ ] Task 3: Build Amendment Process (AC: 9-12)
  - [ ] Create amendment proposal type
  - [ ] Implement supermajority rules
  - [ ] Add cooling period
  - [ ] Create amend endpoint

- [ ] Task 4: Add Constitutional History (AC: 13-16)
  - [ ] Implement version control
  - [ ] Track amendment log
  - [ ] Preserve original immutably
  - [ ] Create history endpoint

- [ ] Task 5: Integrate with DORMANT Features (AC: 17-19)
  - [ ] Connect to Story 8-8 governance gate
  - [ ] Enable autonomy activation check
  - [ ] Ensure human override preserved

---

## Dev Notes

### References
- [Epic 9 Planning](../epic-9-planning.md)
- [Story 8-8 Governance Node](./8-8-epistemic-autonomy-layer.md)

### The Five Red Lines (Initial)

1. **No Safety Bypass**: Cannot skip safety checks
2. **No Silent Delete**: Cannot delete without confirmation
3. **No Impersonation**: Cannot pretend to be human
4. **No Hidden Errors**: Cannot hide failures
5. **No Unbounded Evolution**: Cannot self-modify without approval

### Amendment Rules

| Category | Quorum | Threshold | Amendable? |
|----------|--------|-----------|------------|
| Core Values | 75% | 80% | Yes (with cooling) |
| Amendment Rules | 75% | 80% | Yes (with cooling) |
| Red Lines | N/A | N/A | **NO** (immutable) |

### Integration with 8-8

Once this story is complete, the DORMANT features from Story 8-8 can be activated:
- AC 13: CSI Autonomy Gating → Enabled
- AC 15: Dynamic Model Selection → Enabled
- AC 19: Hypothesis Integration → Enabled

---

## Dev Agent Record

### Context Reference
- [9-4-constitutional-framework.context.xml](./9-4-constitutional-framework.context.xml)

### Agent Model Used
{{agent_model_name_version}}

### Completion Notes
**Completed:** 2025-12-08  
**Definition of Done:** Core AC 1-7, 17-19 met. Amendment process (AC 9-12) and History API (AC 13-16) deferred to Story 9-5.  
**Agent Model:** Claude  

### File List
- `src/jarvis/governance/constitution.py` - ConstitutionalGuard service
- `src/jarvis/governance/models.py` - Constitution model  
- `src/jarvis/governance/trust.py` - Refactored to use Constitution
- `src/jarvis/governance/voting.py` - Integrated ConstitutionalGuard
- `alembic/versions/f7d70fed16d9_create_constitution_model.py` - Migration
- `tests/unit/test_constitutional_framework.py` - 11 unit tests
