# Story 8-1: Capability Registry & Gap Detection

**Epic**: 8 - Self-Improvement & Auto-Evolution  
**Story ID**: 8-1  
**Status**: Ready for Dev 🚀  
**Type**: Self-Awareness Infrastructure  
**Sprint**: TBD  
**Estimated Effort**: 8-12 hours  
**Priority**: HIGH (Foundation for autonomous improvement)

---

## 📋 Story Overview

### User Story

**As a** Jarvis system evolving towards self-improvement,  
**I want** a registry of all my capabilities and automatic detection of gaps,  
**So that** I can identify what I cannot do and propose improvements.

### Core Purpose

> **Jarvis can scan its own tools/prompts and identify missing capabilities.**

---

## 🎯 Acceptance Criteria

### Part A: Capability Registry

1. [ ] **CapabilityRegistry Class**: Central registry of all Jarvis capabilities
2. [ ] **Capability Model**: Name, type, description, status, dependencies
3. [ ] **Auto-Discovery**: Scan codebase for registered capabilities
4. [ ] **API Endpoint**: `GET /api/admin/capabilities` returns full registry

### Part B: Gap Detection

5. [ ] **GapDetector Agent**: Identifies missing or weak capabilities
6. [ ] **Gap Model**: What's missing, why it matters, suggested resolution
7. [ ] **Heuristic Rules**: Pattern matching for common gaps
8. [ ] **API Endpoint**: `GET /api/admin/gaps` returns detected gaps

### Part C: Reporting

9. [ ] **Capability Dashboard**: UI view of all capabilities and gaps
10. [ ] **Gap Prioritization**: Rank gaps by impact and effort
11. [ ] **Trend Tracking**: Track gap resolution over time

---

## 📐 Technical Implementation Plan

### Phase 1: Capability Model (~3-4h)

```python
class Capability(Base):
    id: UUID
    name: str                    # e.g., "web_search", "code_execution"
    capability_type: str         # "tool" | "agent" | "prompt" | "api"
    description: str
    status: str                  # "active" | "deprecated" | "experimental"
    dependencies: List[str]      # Other capabilities required
    version: str
    last_used: Optional[datetime]
    usage_count: int
```

### Phase 2: Registry Service (~3-4h)

```python
class CapabilityRegistry:
    def scan_codebase(self) -> List[Capability]:
        """Discover capabilities from decorators/configs."""
        
    def register(self, capability: Capability):
        """Add capability to registry."""
        
    def get_all(self) -> List[Capability]:
        """Return all registered capabilities."""
        
    def find_by_type(self, cap_type: str) -> List[Capability]:
        """Filter by capability type."""
```

### Phase 3: Gap Detector (~4-6h)

```python
class GapDetector:
    def detect_gaps(self) -> List[Gap]:
        """Identify missing or weak capabilities."""
        
    def suggest_resolution(self, gap: Gap) -> str:
        """Propose how to fill the gap."""
```

---

## 🛠️ New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/admin/capabilities` | List all capabilities |
| GET | `/api/admin/capabilities/{id}` | Get capability details |
| GET | `/api/admin/gaps` | List detected gaps |
| POST | `/api/admin/gaps/{id}/acknowledge` | Mark gap as acknowledged |

---

## 📦 Deliverables

### New Modules
- `src/jarvis/core/capability_registry.py`
- `src/jarvis/core/gap_detector.py`

### Database Migrations
- `capabilities` table
- `detected_gaps` table

### API Additions
- 4 new endpoints in `admin.py`

---

## Dev Agent Record

### Context Reference
- [8-1-capability-registry-gap-detection.context.xml](./8-1-capability-registry-gap-detection.context.xml)

### Agent Model Used
{{agent_model_name_version}}
