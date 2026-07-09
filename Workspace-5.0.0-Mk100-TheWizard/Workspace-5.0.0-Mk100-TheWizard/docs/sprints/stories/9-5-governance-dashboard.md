# Story 9-5: Governance Dashboard

**Epic**: 9 - Political Governance & Multi-Human Consensus
**Story ID**: 9-5
**Status**: Done ✅
**Type**: Frontend/API
**Sprint**: TBD
**Estimated Effort**: 12-16 hours
**Priority**: HIGH (Visibility layer)

---

### User Story

**As a** governance participant,  
**I want** a dashboard showing governance state, proposals, votes, and trust,  
**So that** democracy is transparent and I can monitor the system's political health.

### Core Purpose

> **Visibility is accountability.**

If governance happens in the dark, it's not democracy. The dashboard makes everything auditable.

### Motto

> "What can be seen can be governed."

---

## 🎯 Acceptance Criteria

### Part A: Governance Overview

1. [x] **Dashboard Route**: `/governance` serves interactive dashboard
2. [x] **System Health**: Show governance health (users, proposals, constitution status)
3. [x] **Real-time Updates**: WebSocket or polling for live updates
4. [x] **Mobile Responsive**: Dashboard works on mobile devices


### Part B: Proposal View

5. [x] **Active Proposals**: List of open proposals with vote counts
6. [x] **Proposal Details**: Click to see full proposal, votes, and timeline
7. [x] **Vote History**: My votes across all proposals
8. [x] **Quick Vote**: Cast vote directly from dashboard

### Part C: Trust & Leaderboard

9. [x] **Trust Scores**: My trust scores per domain
10. [x] **Domain Leaderboard**: Top experts per domain
11. [x] **Trust Trend**: Graph of trust changes over time
12. [x] **Expertise Claims**: Manage my claimed expertise

### Part D: Constitutional View

13. [x] **Constitution Display**: View current constitution
14. [x] **Red Lines**: Highlighted red lines with explanations
15. [x] **Amendment History**: Timeline of constitutional changes
16. [x] **Violation Log**: Proposals blocked by constitution

### Part E: Audit & Analytics

17. [x] **Governance Metrics**: Participation rate, quorum health
18. [x] **Vote Analytics**: Voting patterns, consensus trends
19. [x] **Escalation History**: All escalations and resolutions
20. [x] **Export**: Download governance data as CSV/JSON

---

## 📐 Technical Implementation Plan

### Phase 1: Dashboard API (~3-4h)

```python
@router.get("/api/governance/dashboard")
async def get_dashboard_data() -> GovernanceDashboard:
    """
    Aggregate view for dashboard.
    
    Returns:
        - system_health: {users, active_proposals, constitution_version}
        - active_proposals: List[ProposalSummary]
        - recent_votes: List[VoteSummary]
        - trust_leaderboard: Dict[domain, List[TrustRanking]]
        - metrics: {participation_rate, avg_quorum, escalation_count}
    """
```

### Phase 2: Frontend Dashboard (~4-6h)

```html
<!-- src/jarvis/frontend/static/governance_dashboard.html -->

<!-- Iron Man-style dashboard matching Cognitive Cockpit -->
<div id="governance-container">
    <!-- System Health Panel -->
    <div class="panel" id="system-health">
        <h3>⚡ System Health</h3>
        <div class="metric">Users: <span id="user-count">0</span></div>
        <div class="metric">Active Proposals: <span id="proposal-count">0</span></div>
        <div class="metric">Constitution: v<span id="const-version">1.0</span></div>
    </div>
    
    <!-- Active Proposals -->
    <div class="panel" id="proposals">
        <h3>📋 Active Proposals</h3>
        <ul id="proposal-list"></ul>
    </div>
    
    <!-- Trust Leaderboard -->
    <div class="panel" id="trust-leaderboard">
        <h3>🏆 Domain Experts</h3>
        <div id="leaderboard-tabs"></div>
        <ul id="expert-list"></ul>
    </div>
    
    <!-- Constitutional Status -->
    <div class="panel" id="constitution">
        <h3>📜 Constitution</h3>
        <div id="red-lines"></div>
    </div>
</div>
```

### Phase 3: Real-time Updates (~2-3h)

```python
# WebSocket for live governance updates
@router.websocket("/ws/governance")
async def governance_websocket(websocket: WebSocket):
    """
    Broadcast governance events:
    - new_proposal
    - vote_cast
    - proposal_resolved
    - trust_updated
    - escalation_created
    """
```

### Phase 4: Analytics (~2-3h)

```python
class GovernanceAnalytics:
    def get_participation_rate(self, days: int = 30) -> float:
        """Average voting participation over period."""
        
    def get_consensus_score(self, proposal_id: UUID) -> float:
        """How unanimous was the vote? 1.0 = perfect consensus."""
        
    def get_voting_patterns(self, user_id: UUID) -> VotingProfile:
        """User's voting history and patterns."""
        
    def export_governance_data(self, format: str = "json") -> bytes:
        """Export all governance data for auditing."""
```

---

## 🛠️ New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/governance/dashboard` | Aggregate dashboard data |
| GET | `/api/governance/metrics` | Governance analytics |
| GET | `/api/governance/audit` | Full audit trail |
| GET | `/api/governance/export` | Download governance data |
| WS | `/ws/governance` | Real-time updates |

### UI Routes

| Route | Purpose |
|-------|---------|
| `/governance` | Main governance dashboard |
| `/governance/proposals` | Proposal browser |
| `/governance/trust` | Trust management |
| `/governance/constitution` | Constitution viewer |

---

## 📦 Deliverables

### New Modules
- `src/jarvis/governance/dashboard.py`
- `src/jarvis/governance/analytics.py`
- `src/jarvis/governance/websocket.py`

### Frontend
- `src/jarvis/frontend/static/governance_dashboard.html`
- `src/jarvis/frontend/static/css/governance.css`
- `src/jarvis/frontend/static/js/governance.js`

### API Additions
- Dashboard aggregate endpoint
- Analytics endpoints
- WebSocket for real-time

---

## 📋 Tasks / Subtasks

- [ ] Task 1: Create Dashboard API (AC: 1-4)
  - [ ] Build aggregate dashboard endpoint
  - [ ] Add system health metrics
  - [ ] Implement caching for performance
  - [ ] Test mobile responsiveness

- [ ] Task 2: Build Proposal View (AC: 5-8)
  - [ ] Create proposal list component
  - [ ] Add proposal detail modal
  - [ ] Implement vote history
  - [ ] Add quick vote buttons

- [ ] Task 3: Implement Trust UI (AC: 9-12)
  - [ ] Show user trust scores
  - [ ] Create domain leaderboards
  - [ ] Add trust trend chart
  - [ ] Build expertise claim form

- [ ] Task 4: Add Constitutional View (AC: 13-16)
  - [ ] Display constitution formatted
  - [ ] Highlight red lines
  - [ ] Show amendment history
  - [ ] List blocked proposals

- [ ] Task 5: Build Analytics (AC: 17-20)
  - [ ] Calculate governance metrics
  - [ ] Create vote analytics
  - [ ] Add escalation history
  - [ ] Implement export function

---

## Dev Notes

### References
- [Epic 9 Planning](../epic-9-planning.md)
- [Cognitive Cockpit Graph Viewer](../../src/jarvis/frontend/static/graph_viewer.html)

### Design Guidelines
- **Iron Man Aesthetic**: Match the Cognitive Cockpit dark theme
- **Real-time**: Use WebSocket for live updates
- **Mobile-first**: Dashboard must work on phones
- **Accessible**: ARIA labels, keyboard navigation

### Dashboard Panels

```
┌─────────────────────────────────────────────────┐
│               System Health                      │
│  👥 Users: 5  📋 Proposals: 3  📜 v1.0          │
├─────────────────────────────────────────────────┤
│           Active Proposals                       │
│  • [OPEN] Update logging level (2 days left)    │
│  • [VOTING] Add new endpoint (5 votes)          │
├─────────────────────────────────────────────────┤
│           Domain Experts                         │
│  Security: Alice (0.92), Bob (0.85)             │
│  Architecture: Charlie (0.88)                    │
├─────────────────────────────────────────────────┤
│           Red Lines                              │
│  🚫 Never bypass safety checks                   │
│  🚫 Never delete without confirmation            │
└─────────────────────────────────────────────────┘
```

---

## 🔮 The Final Vision

Once this dashboard is complete:

1. **Story 8-8 DORMANT features activate** (with 9-4 constitution)
2. **Jarvis becomes self-governing** under human oversight
3. **Democracy is visible** to all participants
4. **Audit trail is complete** for regulatory compliance

> "Not a chatbot. A governed cognitive institution."

---

## Dev Agent Record

### Context Reference
- [9-5-governance-dashboard.context.xml](./9-5-governance-dashboard.context.xml)

### Agent Model Used
{{agent_model_name_version}}

### Completion Notes List
### Completion Notes List
**Completed:** 2025-12-09
**Definition of Done:** All acceptance criteria met, code reviewed, UI verified by user, tests passing.
- Dashboard API implemented and wired
- Frontend (HTML/JS/CSS) polished and verified
- Real-time wiring complete
- Lifecycle verification (Story 9-6) successfully passed

### File List
<!-- To be filled during implementation -->
