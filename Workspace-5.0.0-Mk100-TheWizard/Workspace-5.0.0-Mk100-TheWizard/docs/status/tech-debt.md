# Technical Debt & Refactoring Plan (Story 8-5)

Generated: 2025-12-06
Status: Action Required

## Current Violations (Detected by `scripts/lint_check.py`)

### 1. `src/jarvis/api/chat.py`
- **Violation**: MAX_FILE_LOC
- **Details**: File has > 1000 LOC (Limit: 800)
- **Violation**: MAX_COMPLEXITY
- **Details**: Multiple functions/classes exceed complexity 15.

### 2. `src/jarvis/core/memory.py` (Potential)
- **Violation**: MAX_METHODS
- **Details**: `MemoryManager` class likely exceeds 20 methods.

---

## Refactoring Plan (Heuristic Analysis)

### A. `src/jarvis/api/chat.py` -> Split Strategy
**Heuristic**: "Controller vs Logic vs Utils"

1.  **`src/jarvis/api/routes/chat.py`** (New)
    - Content: FastAPI route definitions (`@router.post("/chat")`), request/response models.
    - Goal: Pure HTTP layer.

2.  **`src/jarvis/controllers/chat_controller.py`** (New)
    - Content: `ChatController` class.
    - Goal: Business logic, orchestration of retrieval + generation.

3.  **`src/jarvis/utils/chat_utils.py`** (New)
    - Content: Helper functions (`format_response`, `parse_query`).
    - Goal: Stateless utilities.

### B. `src/jarvis/core/memory.py` -> Split Strategy
**Heuristic**: "Read vs Write"

1.  **`src/jarvis/core/memory/retrieval.py`**
    - Content: `query()`, `search()`, `get_context()`.
    - Goal: Read operations.

2.  **`src/jarvis/core/memory/ingestion.py`**
    - Content: `add()`, `update()`, `delete()`.
    - Goal: Write operations.

### C. Action Items
1.  [ ] Apply `chat.py` split (Priority: High).
2.  [ ] Apply `memory.py` split (Priority: Medium).
3.  [ ] Add `# jarvis:allow-large-file` to legacy files if refactoring is deferred.

---

## Story 11-5 Tech Debt (Lock 7: Epistemic Sovereignty)

**Added:** 2025-12-10
**Source:** Code Review - Story 11-5
**Status:** Low Priority - Foundation is solid

### 1. Dual-Persona Arbitration - LLM Integration
**File:** `src/jarvis/knowledge/arbitration.py` (lines 178-259)
**Issue:** Uses placeholder heuristic logic instead of actual LLM calls for Analyst and Adversary persona evaluation
**Impact:** Reduces effectiveness of arbitration decisions
**Current State:** Structure is correct, documented with TODO comments
**Priority:** Medium
**Action:**
- [ ] Replace heuristic logic with LLM-based evaluation in Analyst persona (lines 178-207)
- [ ] Replace heuristic logic with LLM-based evaluation in Adversary persona (lines 228-259)
- [ ] Design persona-specific prompts for logical coherence and attack surface analysis
**Estimated Effort:** 1-2 days
**Blocks:** None - current implementation is functional

### 2. Epistemic Audit Log - Database Persistence
**File:** `src/jarvis/knowledge/audit.py` (lines 213-229)
**Issue:** Audit log uses in-memory storage instead of database backing
**Impact:** Limited scalability for large deployments, no persistence across restarts
**Current State:** Acceptable for initial implementation, properly indexed
**Priority:** Low
**Action:**
- [ ] Add database models for epistemic events (SQLAlchemy)
- [ ] Implement database-backed storage in `EpistemicAuditLog`
- [ ] Add migration path from in-memory to database storage
- [ ] Maintain backward compatibility with existing query interface
**Estimated Effort:** 2-3 days
**Blocks:** None - current implementation works for development and testing
**Note:** Consider implementing when moving to production scale or multi-instance deployments
