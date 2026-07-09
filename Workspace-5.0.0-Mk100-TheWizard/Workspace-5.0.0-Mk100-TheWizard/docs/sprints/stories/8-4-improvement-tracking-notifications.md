# Story 8-4: Improvement Tracking & Notifications

**Epic**: 8 - Self-Improvement & Auto-Evolution  
**Story ID**: 8-4  
**Status**: Ready for Dev 🚀  
**Type**: Monitoring & Communication  
**Sprint**: TBD  
**Estimated Effort**: 6-8 hours  
**Priority**: MEDIUM (Visibility into autonomous actions)

---

## 📋 Story Overview

### User Story

**As a** Jarvis operator monitoring autonomous improvements,  
**I want** a notification system that reports what Jarvis improved,  
**So that** I maintain visibility and can audit autonomous actions.

### Core Purpose

> **Notification system for "I improved X" with full audit trail.**

---

## 🎯 Acceptance Criteria

### Part A: Improvement Tracking

1. [ ] **Improvement Model**: What changed, why, when, outcome
2. [ ] **Auto-Detection**: Track successful pipeline completions
3. [ ] **Impact Assessment**: Measure before/after metrics
4. [ ] **History Storage**: Persistent improvement log

### Part B: Notification System

5. [ ] **Notification Channels**: Console, API, webhook, email (optional)
6. [ ] **Notification Levels**: info, warning, critical
7. [ ] **Subscription Model**: User subscribes to notification types
8. [ ] **Rate Limiting**: Prevent notification spam

### Part C: Dashboard

9. [ ] **Improvement Timeline**: Visual history of improvements
10. [ ] **Impact Metrics**: Charts showing improvement effects
11. [ ] **Rollback History**: Track rollbacks and reasons
12. [ ] **API Endpoint**: `GET /api/admin/improvements`

---

## 📐 Technical Implementation Plan

### Phase 1: Improvement Model (~2-3h)

```python
class Improvement(Base):
    id: UUID
    name: str                    # Short description
    description: str             # Full details
    improvement_type: str        # "performance" | "feature" | "fix" | "refactor"
    pipeline_id: Optional[UUID]  # Link to pipeline that made the change
    before_metrics: Dict         # Metrics before change
    after_metrics: Dict          # Metrics after change
    status: str                  # "pending" | "applied" | "rolled_back"
    created_at: datetime
    applied_at: Optional[datetime]
```

### Phase 2: Notification Service (~2-3h)

```python
class NotificationService:
    def notify(self, message: str, level: str, channel: str):
        """Send notification to specified channel."""
        
    def subscribe(self, user_id: str, notification_type: str):
        """Subscribe user to notification type."""
        
    def get_history(self, limit: int = 50) -> List[Notification]:
        """Get notification history."""
```

### Phase 3: Impact Tracker (~2-3h)

```python
class ImpactTracker:
    def capture_before(self, improvement_id: UUID):
        """Capture metrics before improvement."""
        
    def capture_after(self, improvement_id: UUID):
        """Capture metrics after improvement."""
        
    def calculate_impact(self, improvement_id: UUID) -> ImpactReport:
        """Calculate improvement impact."""
```

---

## 🛠️ New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/admin/improvements` | List improvements |
| GET | `/api/admin/improvements/{id}` | Get improvement details |
| GET | `/api/admin/notifications` | Get notification history |
| POST | `/api/admin/notifications/subscribe` | Subscribe to notifications |

---

## 📦 Deliverables

### New Modules
- `src/jarvis/core/improvement_tracker.py`
- `src/jarvis/core/notification_service.py`
- `src/jarvis/core/impact_tracker.py`

### Database Migrations
- `improvements` table
- `notifications` table
- `notification_subscriptions` table

---

## Dev Agent Record

### Context Reference
- [8-4-improvement-tracking-notifications.context.xml](./8-4-improvement-tracking-notifications.context.xml)

### Agent Model Used
{{agent_model_name_version}}
