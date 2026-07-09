# JARVIS Refactoring & Cleanup Plan

**Date:** 2025-12-09
**Status:** Ready for Implementation
**Priority:** High (Code Quality - Before Next Epic)

---

## Executive Summary

Comprehensive refactoring to address technical debt identified in [PROJECT-AUDIT-2025-12-09.md](../PROJECT-AUDIT-2025-12-09.md):

1. **governance_legacy.py** (1,994 LOC) → Split into 5 focused modules
2. **Root scripts** → Organize into proper folders
3. **Root artifacts** → Move/delete temporary files

**Estimated Effort:** 12-16 hours
**Impact:** A- → A+ code quality grade

---

## 1. Refactor governance_legacy.py

**Current State:**
- File: `src/jarvis/api/governance_legacy.py`
- Size: 1,994 LOC (largest file in codebase)
- Status: Monolithic, difficult to test and maintain

**Target State:**
Split into focused modules in `src/jarvis/api/governance/`:

### Module Breakdown

#### 1.1 `src/jarvis/api/governance/proposals.py` (~400 LOC)

**Responsibilities:**
- Proposal CRUD operations
- Proposal lifecycle management (draft → active → approved/rejected)
- Proposal validation

**Functions to Move:**
- `create_proposal()`
- `get_proposal(proposal_id)`
- `list_proposals(status=None)`
- `update_proposal_status()`
- `validate_proposal()`

**Database Tables:**
- `proposals` (primary)
- `governance_users` (foreign key)

---

#### 1.2 `src/jarvis/api/governance/voting.py` (~400 LOC)

**Responsibilities:**
- Vote casting and validation
- Vote counting and quorum checking
- Timeout enforcement

**Functions to Move:**
- `cast_vote(proposal_id, user_id, vote_value)`
- `count_votes(proposal_id)`
- `check_quorum(proposal_id)`
- `enforce_timeout(proposal_id)`
- `get_vote_breakdown(proposal_id)`

**Database Tables:**
- `votes` (primary)
- `proposals` (foreign key)
- `governance_users` (foreign key)

---

#### 1.3 `src/jarvis/api/governance/users.py` (~400 LOC)

**Responsibilities:**
- User registration and management
- Role assignment
- Trust score management

**Functions to Move:**
- `register_user(username, email, role)`
- `get_user(user_id)`
- `list_users(role=None)`
- `update_user_role()`
- `get_trust_scores(user_id)`
- `update_trust_score(user_id, domain, score)`

**Database Tables:**
- `governance_users` (primary)
- `governance_roles` (reference)
- `user_trust_scores` (related)

---

#### 1.4 `src/jarvis/api/governance/constitution.py` (~400 LOC)

**Responsibilities:**
- Constitutional framework management
- Core values and red lines
- Amendment process

**Functions to Move:**
- `get_constitution()`
- `get_core_values()`
- `get_red_lines()`
- `propose_amendment()`
- `validate_against_constitution(action)`

**Database Tables:**
- `constitution` (primary)

---

#### 1.5 `src/jarvis/api/governance/escalation.py` (~394 LOC)

**Responsibilities:**
- Constitutional violation detection
- Escalation workflows
- Audit logging

**Functions to Move:**
- `detect_violation(action)`
- `log_violation(violation_type, details)`
- `escalate_violation(violation_id)`
- `get_violations(status=None)`

**Database Tables:**
- `constitutional_violations` (primary)
- `governance_users` (foreign key)

---

### 1.6 Migration Strategy

**Step 1: Create Module Structure**
```bash
mkdir -p src/jarvis/api/governance
touch src/jarvis/api/governance/__init__.py
touch src/jarvis/api/governance/proposals.py
touch src/jarvis/api/governance/voting.py
touch src/jarvis/api/governance/users.py
touch src/jarvis/api/governance/constitution.py
touch src/jarvis/api/governance/escalation.py
```

**Step 2: Extract Functions (One Module at a Time)**
- Copy functions from `governance_legacy.py` to target module
- Update imports
- Run tests after each module extraction
- Verify API endpoints still work

**Step 3: Update Imports Project-Wide**
```python
# OLD (governance_legacy.py)
from jarvis.api.governance_legacy import create_proposal, cast_vote

# NEW (modular)
from jarvis.api.governance.proposals import create_proposal
from jarvis.api.governance.voting import cast_vote
```

**Step 4: Deprecate and Remove Legacy File**
- Once all functions migrated, rename `governance_legacy.py` → `governance_legacy.py.bak`
- Test full governance workflow
- Delete backup if all tests pass

---

## 2. Organize Root Scripts

**Current State:**
Multiple scripts scattered in project root and `scripts/` root

**Target State:**
All scripts organized into appropriate subdirectories

### 2.1 Move Scripts to `scripts/setup/`

**Files:**
- `scripts/bootstrap_governance.py` → `scripts/setup/bootstrap_governance.py`

**Rationale:** Setup/initialization scripts belong in setup folder

### 2.2 Move Scripts to `scripts/tests/`

**Files:**
- `scripts/simulate_governance_v1.py` → `scripts/tests/simulate_governance.py`
- `scripts/simulate_hybrid_v1.py` → `scripts/tests/simulate_hybrid.py`
- `scripts/test_model_identity.py` → `scripts/tests/test_model_identity.py`
- `scripts/verify_auth.py` → `scripts/tests/verify_auth.py`

**Rationale:** Test/verification scripts belong in tests folder

### 2.3 Move Scripts to `scripts/diagnostics/`

**Files:**
- `debug_trust.py` (root) → `scripts/diagnostics/debug_trust.py`
- `replace_research_block.py` (root) → `scripts/diagnostics/replace_research_block.py` (or delete if obsolete)

**Rationale:** Diagnostic/debugging scripts belong in diagnostics folder

### 2.4 Organize Root-Level scripts/ Files

**Move to subdirectories:**
- `scripts/fix_keycloak_users.py` → `scripts/maintenance/fix_keycloak_users.py`
- `scripts/force_schema.py` → `scripts/maintenance/force_schema.py`
- `scripts/genesis_registrar.py` → `scripts/setup/genesis_registrar.py`
- `scripts/nuke_db.py` → `scripts/maintenance/nuke_db.py`
- `scripts/provision_red_team_users.py` → `scripts/setup/provision_red_team_users.py`
- `scripts/verify_genesis.py` → `scripts/tests/verify_genesis.py`
- `scripts/verify_persona_api.py` → `scripts/tests/verify_persona_api.py`

---

## 3. Clean Up Root Artifacts

**Current State:**
Temporary files in project root

**Target State:**
Clean root directory, artifacts in `artifacts/` or deleted

### 3.1 Move to `artifacts/`

**Files:**
- `active_proposals.json` → `artifacts/governance/active_proposals.json`
- `valid_proposals.json` → `artifacts/governance/valid_proposals.json`
- `vote.json` → `artifacts/governance/vote.json`

**Actions:**
```bash
mkdir -p artifacts/governance
mv active_proposals.json artifacts/governance/
mv valid_proposals.json artifacts/governance/
mv vote.json artifacts/governance/
```

### 3.2 Delete Obsolete Files

**Files to Delete (if no longer needed):**
- `sim_error.log` (temporary error log)
- Any other `*.log` files in root

**Verification:** Ask user before deleting

---

## 4. Implementation Checklist

### Phase 1: Governance Refactoring (8-10h)

- [ ] Create `src/jarvis/api/governance/` module structure
- [ ] Extract `proposals.py` from governance_legacy.py
- [ ] Extract `voting.py` from governance_legacy.py
- [ ] Extract `users.py` from governance_legacy.py
- [ ] Extract `constitution.py` from governance_legacy.py
- [ ] Extract `escalation.py` from governance_legacy.py
- [ ] Update all imports project-wide
- [ ] Run full test suite
- [ ] Test governance dashboard UI
- [ ] Delete `governance_legacy.py`

### Phase 2: Script Organization (2-3h)

- [ ] Move `scripts/bootstrap_governance.py` → `scripts/setup/`
- [ ] Move simulation scripts to `scripts/tests/`
- [ ] Move verification scripts to `scripts/tests/`
- [ ] Move diagnostic scripts to `scripts/diagnostics/`
- [ ] Move root Python scripts to appropriate folders
- [ ] Organize remaining root-level scripts/ files
- [ ] Update any documentation referencing old paths
- [ ] Verify scripts run from new locations

### Phase 3: Artifact Cleanup (1h)

- [ ] Create `artifacts/governance/` directory
- [ ] Move JSON files to artifacts
- [ ] Delete obsolete log files (after confirmation)
- [ ] Clean up root directory
- [ ] Update `.gitignore` if needed

### Phase 4: Testing & Verification (2h)

- [ ] Run full test suite
- [ ] Test governance API endpoints
- [ ] Test governance dashboard
- [ ] Test relocated scripts
- [ ] Verify no broken imports
- [ ] Verify documentation accuracy

---

## 5. Post-Refactoring Validation

**Success Criteria:**
- ✅ All tests pass
- ✅ Governance dashboard functional
- ✅ No files >500 LOC (except generated code)
- ✅ Root directory clean
- ✅ All scripts in organized folders
- ✅ Code quality: A+ grade

**Rollback Plan:**
- Git commits after each phase
- Keep `governance_legacy.py.bak` until validation complete
- Can restore from git history if needed

---

## 6. Related Documentation

**Update After Refactoring:**
- [docs/architecture/index.md](../architecture/index.md) - Update governance architecture section
- [README.md](../../README.md) - Update script organization section if referenced
- [docs/guides/repository-guidelines.md](../guides/repository-guidelines.md) - Update code organization examples

---

*Generated by: Claude Sonnet 4.5*
*Based on: [PROJECT-AUDIT-2025-12-09.md](../PROJECT-AUDIT-2025-12-09.md)*
*Date: 2025-12-09*
