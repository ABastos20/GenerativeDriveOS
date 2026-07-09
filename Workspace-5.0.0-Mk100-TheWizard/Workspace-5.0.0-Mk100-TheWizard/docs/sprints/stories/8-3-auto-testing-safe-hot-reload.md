# Story 8-3: Auto-Testing & Safe Hot-Reload

**Epic**: 8 - Self-Improvement & Auto-Evolution  
**Story ID**: 8-3  
**Status**: Ready for Dev 🚀  
**Type**: Safety & Deployment  
**Sprint**: TBD  
**Estimated Effort**: 12-16 hours  
**Priority**: CRITICAL (Prevents self-bricking)

---

## 📋 Story Overview

### User Story

**As a** Jarvis system making changes to itself,  
**I want** automatic testing and safe hot-reload with rollback,  
**So that** I cannot brick myself and always have a recovery path.

### Core Purpose

> **Apply changes without restarting (where possible) or safe restart with auto-revert on failure.**

### Constraint

> **MUST have a "Last Known Good" snapshot and auto-revert on failure.**

---

## 🎯 Acceptance Criteria

### Part A: Snapshot System

1. [ ] **Snapshot Creation**: `jarvis snapshot create` before any change
2. [ ] **Snapshot Storage**: Versioned state (config, code refs, DB state)
3. [ ] **Snapshot Listing**: `jarvis snapshot list`
4. [ ] **Snapshot Restore**: `jarvis snapshot restore <id>`

### Part B: Auto-Testing

5. [ ] **Pre-Change Tests**: Run test suite before applying changes
6. [ ] **Post-Change Tests**: Run test suite after applying changes
7. [ ] **Test Failure → Rollback**: Auto-revert if tests fail
8. [ ] **Test Coverage Threshold**: Block changes below threshold

### Part C: Hot-Reload

9. [ ] **Config Hot-Reload**: Update config without restart
10. [ ] **Prompt Hot-Reload**: Update prompts without restart
11. [ ] **Code Hot-Reload**: Reload modules where safe
12. [ ] **Full Restart**: Graceful restart when hot-reload not possible

### Part D: Safety Gates

13. [ ] **Last Known Good (LKG)**: Always maintain LKG snapshot
14. [ ] **Auto-Rollback**: Revert within 60s if health check fails
15. [ ] **Human Approval**: Optional gate for risky changes
16. [ ] **Audit Log**: Full trace of all changes and rollbacks

---

## 📐 Technical Implementation Plan

### Phase 1: Snapshot Manager (~4-6h)

```python
class SnapshotManager:
    def create(self, name: str) -> Snapshot:
        """Create snapshot of current state."""
        
    def restore(self, snapshot_id: UUID) -> bool:
        """Restore to snapshot state."""
        
    def get_lkg(self) -> Snapshot:
        """Get last known good snapshot."""
        
    def set_lkg(self, snapshot_id: UUID):
        """Mark snapshot as last known good."""
```

### Phase 2: Test Runner (~3-4h)

```python
class TestRunner:
    def run_pre_change_tests(self) -> TestResult:
        """Run tests before applying change."""
        
    def run_post_change_tests(self) -> TestResult:
        """Run tests after applying change."""
        
    def should_rollback(self, result: TestResult) -> bool:
        """Determine if rollback is needed."""
```

### Phase 3: Hot-Reload Engine (~4-6h)

```python
class HotReloadEngine:
    def reload_config(self) -> bool:
        """Hot-reload configuration."""
        
    def reload_prompts(self) -> bool:
        """Hot-reload prompt templates."""
        
    def reload_module(self, module_path: str) -> bool:
        """Attempt module hot-reload."""
        
    def full_restart(self) -> bool:
        """Graceful full restart."""
```

---

## 🛠️ New CLI Commands

| Command | Purpose |
|---------|---------|
| `jarvis snapshot create <name>` | Create snapshot |
| `jarvis snapshot list` | List snapshots |
| `jarvis snapshot restore <id>` | Restore snapshot |
| `jarvis reload config` | Hot-reload config |
| `jarvis reload prompts` | Hot-reload prompts |
| `jarvis restart --safe` | Graceful restart |

---

## 📦 Deliverables

### New Modules
- `src/jarvis/core/safety/snapshot_manager.py`
- `src/jarvis/core/safety/test_runner.py`
- `src/jarvis/core/safety/hot_reload.py`

### CLI Additions
- `src/jarvis/cli/snapshot.py`
- `src/jarvis/cli/reload.py`

---

## Dev Agent Record

### Context Reference
- [8-3-auto-testing-safe-hot-reload.context.xml](./8-3-auto-testing-safe-hot-reload.context.xml)

### Agent Model Used
{{agent_model_name_version}}
