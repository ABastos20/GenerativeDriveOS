# Story 9-2: Disagreement Voting Engine

**Epic**: 9 - Political Governance & Multi-Human Consensus  
**Story ID**: 9-2  
**Status**: Done  
**Type**: Decision Infrastructure  
**Sprint**: TBD  
**Estimated Effort**: 14-18 hours  
**Priority**: HIGH (Core decision mechanism)

---

## 📋 Story Overview

### User Story

**As a** governance participant,  
**I want** a structured voting system for resolving disagreements,  
**So that** multiple humans can make collective decisions with clear rules and deadlines.

### Core Purpose

> **Disagreement without deadlock.**

When humans disagree, the system must resolve it — not by picking a winner randomly, but through structured democratic process.

### Motto

> "Every voice counts. Silence is not consensus."

---

## 🎯 Acceptance Criteria

### Part A: Proposal System

1. [ ] **Proposal Model**: Title, description, proposer, type, status, deadline
2. [ ] **Proposal Types**: decision, config_change, constitutional_amendment
3. [ ] **Proposal Lifecycle**: draft → open → voting → passed/rejected/expired
4. [ ] **API Endpoint**: `POST /api/governance/proposals` creates proposal

### Part B: Voting Mechanics

5. [ ] **Vote Model**: Proposal, user, vote (for/against/abstain), weight, reason
6. [ ] **Vote Collection**: Track all votes with timestamps
7. [ ] **Vote Immutability**: Once cast, votes cannot be changed (audit requirement)
8. [ ] **API Endpoint**: `POST /api/governance/proposals/{id}/vote` casts vote

### Part C: Quorum & Threshold Rules

9. [ ] **Quorum Configuration**: Minimum participation percentage (default 50%)
10. [ ] **Approval Threshold**: Percentage needed to pass (default 50%+1)
11. [ ] **Constitutional Threshold**: Higher bar for amendments (80%)
12. [ ] **Timeout Rules**: Auto-expire proposals after deadline

### Part D: Vote Resolution

13. [ ] **Vote Calculator**: Tally weighted votes and determine outcome
14. [ ] **Tie Breaker**: Escalate ties to higher authority (Story 9-1)
15. [ ] **Result Notification**: Notify all participants of outcome
16. [ ] **API Endpoint**: `GET /api/governance/proposals/{id}/results` returns outcome

### Part E: Vote Transparency

17. [ ] **Vote History**: Public record of all votes (optional anonymity for observers)
18. [ ] **Vote Reasoning**: Optional explanation for each vote
19. [ ] **Audit Trail**: Complete audit log of proposal lifecycle

---

## 📐 Technical Implementation Plan

### Phase 1: Proposal Model (~4-6h)

```python
class Proposal(Base):
    id: UUID
    title: str
    description: str
    proposer_id: UUID
    proposal_type: str  # "decision" | "config_change" | "constitutional_amendment"
    status: str  # "draft" | "open" | "voting" | "passed" | "rejected" | "expired"
    quorum_required: float  # 0.5 = 50% participation
    approval_threshold: float  # 0.5 = majority
    deadline: datetime
    created_at: datetime
    resolved_at: Optional[datetime]
    resolution_reason: Optional[str]
    
class ProposalType(str, Enum):
    DECISION = "decision"  # Normal decision
    CONFIG_CHANGE = "config_change"  # System configuration
    CONSTITUTIONAL = "constitutional_amendment"  # Requires supermajority
```

### Phase 2: Vote Model (~3-4h)

```python
class Vote(Base):
    id: UUID
    proposal_id: UUID
    user_id: UUID
    vote: str  # "for" | "against" | "abstain"
    weight: float  # From trust score (Story 9-3)
    reason: Optional[str]  # Justification
    voted_at: datetime
    
    # Constraint: One vote per user per proposal
    __table_args__ = (UniqueConstraint('proposal_id', 'user_id'),)
```

### Phase 3: Vote Calculator (~3-4h)

```python
class VoteCalculator:
    def calculate_result(self, proposal_id: UUID) -> VoteResult:
        """
        Calculate weighted vote totals and determine outcome.
        
        Returns:
            VoteResult with:
            - total_for: Sum of weighted "for" votes
            - total_against: Sum of weighted "against" votes
            - participation: Percentage who voted
            - quorum_met: bool
            - passed: bool
            - tie: bool
        """
        
    def check_quorum(self, proposal_id: UUID) -> bool:
        """Check if minimum participation reached."""
        
    def resolve_tie(self, proposal_id: UUID) -> TieResolution:
        """Handle tie vote - escalate to higher authority."""
```

### Phase 4: Proposal Lifecycle (~3-4h)

```python
class ProposalEngine:
    def create(self, data: ProposalCreate, proposer: UUID) -> Proposal:
        """Create new proposal in draft state."""
        
    def open_for_voting(self, proposal_id: UUID):
        """Move proposal from draft to open."""
        
    def close_voting(self, proposal_id: UUID) -> VoteResult:
        """Calculate result and update status."""
        
    def check_expired(self):
        """Background job to expire overdue proposals."""
```

---

## 🛠️ New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/governance/proposals` | List proposals (filter by status) |
| POST | `/api/governance/proposals` | Create new proposal |
| GET | `/api/governance/proposals/{id}` | Get proposal details |
| POST | `/api/governance/proposals/{id}/open` | Open for voting |
| POST | `/api/governance/proposals/{id}/vote` | Cast vote |
| GET | `/api/governance/proposals/{id}/votes` | List all votes |
| GET | `/api/governance/proposals/{id}/results` | Get voting results |

---

## 📦 Deliverables

### New Modules
- `src/jarvis/governance/proposals.py`
- `src/jarvis/governance/voting.py`
- `src/jarvis/governance/calculator.py`

### Database Migrations
- `proposals` table
- `votes` table

### Background Jobs
- `check_proposal_expiration` - Hourly check for expired proposals

---

## 📋 Tasks / Subtasks

- [ ] Task 1: Create Proposal Model (AC: 1-4)
  - [ ] Define Proposal schema
  - [ ] Create ProposalType enum
  - [ ] Implement lifecycle state machine
  - [ ] Create API for proposal CRUD

- [ ] Task 2: Implement Voting System (AC: 5-8)
  - [ ] Create Vote model with uniqueness constraint
  - [ ] Implement vote casting endpoint
  - [ ] Ensure vote immutability
  - [ ] Add voting deadline enforcement

- [ ] Task 3: Build Quorum & Threshold Logic (AC: 9-12)
  - [ ] Implement quorum checking
  - [ ] Add configurable thresholds
  - [ ] Create constitutional amendment high bar
  - [ ] Implement expiration job

- [ ] Task 4: Create Vote Calculator (AC: 13-16)
  - [ ] Build weighted vote tallying
  - [ ] Implement tie detection and escalation
  - [ ] Add result notification
  - [ ] Create results API

- [ ] Task 5: Add Transparency Features (AC: 17-19)
  - [ ] Create vote history API
  - [ ] Allow vote reasoning
  - [ ] Integrate audit trail

---

## Dev Notes

### References
- [Epic 9 Planning](../epic-9-planning.md)
- [Story 9-1 Governance Model](./9-1-multi-human-governance-model.md)
- [Story 9-3 Trust Weights](./9-3-trust-weighted-consensus.md)

### Critical Design Decisions
- Votes are **immutable** once cast (for audit compliance)
- Weight comes from trust scores (Story 9-3) — default weight = 1.0
- Constitutional amendments require 75% quorum + 80% approval
- Ties escalate to next role level (Contributor → Admin → Owner)

### Dependencies
- Depends on: Story 9-1 (roles/permissions)
- Feeds into: Story 9-3 (trust scores update based on vote accuracy)

---

## Dev Agent Record

### Context Reference
- [9-2-disagreement-voting-engine.context.xml](./9-2-disagreement-voting-engine.context.xml)

### Agent Model Used
{{agent_model_name_version}}

### Completion Notes List
**Completed:** 2025-12-08
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing.
- Implemented Proposal and Vote models.
- Implemented VotingEngine logic.
- Implemented API endpoints.
- Verified via integration tests.

### File List
- src/jarvis/governance/models.py
- src/jarvis/governance/voting.py
- src/jarvis/api/governance.py
- tests/integration/test_voting_engine.py
