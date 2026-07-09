# Story 9-1: Multi-Human Governance Model

**Epic**: 9 - Political Governance & Multi-Human Consensus  
**Story ID**: 9-1  
**Status**: Done ✅  
**Type**: Governance Infrastructure  
**Sprint**: TBD  
**Estimated Effort**: 12-16 hours  
**Priority**: CRITICAL (Foundation for all governance)

---

## 📋 Story Overview

### User Story

**As a** Jarvis architect building machine democracy,  
**I want** a multi-human governance model with roles, permissions, and escalation paths,  
**So that** multiple stakeholders can participate in AI decisions with clear authority structures.

### Core Purpose

> **Define who can decide what, and when to escalate.**

This is the political foundation — without clear roles, voting becomes chaos.

### Motto

> "Many voices. Clear authority."

---

## 🎯 Acceptance Criteria

### Part A: User Registry

1. [x] **GovernanceUser Model**: Extends base User with governance fields
2. [x] **Role Enum**: Owner, Admin, Contributor, Observer
3. [x] **Role Permissions Matrix**: What each role can do
4. [x] **API Endpoint**: `GET /api/governance/users` lists governance users

### Part B: Permission System

5. [x] **Permission Model**: Action → Role mapping
6. [x] **Permission Categories**: vote, propose, amend, override, view
7. [x] **Permission Check**: Decorator/middleware for role-gated endpoints
8. [x] **API Endpoint**: `GET /api/governance/permissions` returns matrix

### Part C: Escalation Rules

9. [x] **EscalationRule Model**: Condition → escalate to higher authority
10. [x] **Escalation Triggers**: Tie votes, quorum not met, constitutional conflict
11. [x] **Escalation Chain**: Contributor → Admin → Owner
12. [x] **API Endpoint**: `GET /api/governance/escalations` returns pending escalations

### Part D: Integration with Epistemic Layer

13. [x] **Governance Gate**: Connect to CSI thresholds from Story 8-8
14. [x] **Auto-Escalate**: When system stability drops, require higher authority
15. [x] **Audit Trail**: All role assignments and permission changes logged

---

## 📐 Technical Implementation Plan

### Phase 1: GovernanceUser Model (~4-6h)

```python
class GovernanceUser(Base):
    id: UUID
    name: str
    email: str
    role: str  # "owner" | "admin" | "contributor" | "observer"
    trust_scores: Dict[str, float]  # domain -> score (from Story 9-3)
    permissions: List[str]  # cached permission list
    joined_at: datetime
    last_active: datetime
    invited_by: Optional[UUID]  # For audit trail
    
class Role(str, Enum):
    OWNER = "owner"           # Full control, constitutional authority
    ADMIN = "admin"           # Can manage users, moderate votes
    CONTRIBUTOR = "contributor"  # Can vote and propose
    OBSERVER = "observer"     # Read-only access
```

### Phase 2: Permission Matrix (~3-4h)

```python
PERMISSION_MATRIX = {
    "owner": ["*"],  # All permissions
    "admin": ["vote", "propose", "moderate", "manage_users", "view"],
    "contributor": ["vote", "propose", "view"],
    "observer": ["view"],
}

class PermissionGate:
    def require(self, permission: str):
        """Decorator for permission-gated endpoints."""
        
    def check(self, user_id: UUID, permission: str) -> bool:
        """Check if user has permission."""
```

### Phase 3: Escalation Engine (~3-4h)

```python
class EscalationRule(Base):
    id: UUID
    trigger: str  # "tie_vote" | "quorum_failed" | "csi_below_threshold"
    escalate_to: str  # Role that handles escalation
    timeout_hours: int  # Time before auto-escalate again
    
class EscalationEngine:
    def should_escalate(self, context: dict) -> Optional[EscalationRule]:
        """Determine if escalation is needed."""
        
    def escalate(self, proposal_id: UUID, reason: str):
        """Escalate to higher authority."""
```

---

## 🛠️ New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/governance/users` | List governance users |
| POST | `/api/governance/users` | Add new governance user |
| PATCH | `/api/governance/users/{id}/role` | Change user role |
| GET | `/api/governance/permissions` | Get permission matrix |
| GET | `/api/governance/escalations` | List pending escalations |
| POST | `/api/governance/escalations/{id}/resolve` | Resolve escalation |

---

## 📦 Deliverables

### New Modules
- `src/jarvis/governance/models.py`
- `src/jarvis/governance/permissions.py`
- `src/jarvis/governance/escalation.py`
- `src/jarvis/api/governance.py`

### Database Migrations
- `governance_users` table
- `escalation_rules` table
- `escalations` table

### Configuration
- `config/governance/roles.yaml` - Role definitions
- `config/governance/permissions.yaml` - Permission matrix

---

## 📋 Tasks / Subtasks

- [ ] Task 1: Create GovernanceUser model (AC: 1-4)
  - [ ] Define Role enum
  - [ ] Create SQLAlchemy model
  - [ ] Create Alembic migration
  - [ ] Create API endpoint for user list

- [ ] Task 2: Implement Permission System (AC: 5-8)
  - [ ] Define PERMISSION_MATRIX
  - [ ] Create PermissionGate class
  - [ ] Add permission decorator
  - [ ] Create permissions API endpoint

- [ ] Task 3: Build Escalation Engine (AC: 9-12)
  - [ ] Create EscalationRule model
  - [ ] Implement escalation triggers
  - [ ] Create escalation chain logic
  - [ ] Create escalations API endpoints

- [ ] Task 4: Integrate with Epistemic Layer (AC: 13-15)
  - [ ] Connect to GovernanceGate from 8-8
  - [ ] Implement CSI-based escalation
  - [ ] Add audit logging

---

## Dev Notes

### References
- [Epic 9 Planning](../epic-9-planning.md)
- [Story 8-8 Governance Node](./8-8-epistemic-autonomy-layer.md)
- [Governance Node Module](../../src/jarvis/memory/governance_node.py)

### Project Structure Notes
- New `src/jarvis/governance/` package for all governance modules
- Follows existing API patterns from `src/jarvis/api/`
- Integrates with existing observability for audit trail

### Testing Standards
- Unit tests for permission checking
- Integration tests for role-based API access
- Test escalation triggers

---

## Dev Agent Record

### Context Reference
- [9-1-multi-human-governance-model.context.xml](./9-1-multi-human-governance-model.context.xml)

### Agent Model Used
{{agent_model_name_version}}

### Completion Notes List
- Implemented full governance database schema (Users, Permissions, Escalations, Audit)
- Implemented `GovernanceGate` and `EscalationEngine` for logic
- Implemented `PermissionGate` decorators (`@require_permission`, `@require_role`)
- Implemented `GovernanceMiddleware` for header-based auth
- Implemented API endpoints for Users, Permissions, Escalations
- Verified Logic with `tests/integration/test_governance.py` (100% pass)
- Fixed 500 error in API by ensuring Request context propagation

### File List
- `src/jarvis/governance/models.py`
- `src/jarvis/governance/permissions.py`
- `src/jarvis/governance/escalation.py`
- `src/jarvis/api/governance.py`
- `src/jarvis/api/middleware.py`
- `src/jarvis/memory/governance_node.py`
- `alembic/versions/20241208_align_governance_full.py`
- `tests/integration/test_governance.py`
