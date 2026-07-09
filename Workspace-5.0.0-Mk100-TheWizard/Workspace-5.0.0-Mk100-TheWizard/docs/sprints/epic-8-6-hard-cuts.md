# Epic 8.6 - Hard Cuts for v2.0.3

**Sprint**: v2.0.3 Surgical Compliance  
**Type**: Structural Segmentation (Metric Compliance)  
**Target**: 7 → 2-3 violations (85-90% total reduction)  
**Estimated**: 3-4 hours

---

## 🎯 Objective

**NOT feature work. NOT cleanup games.**

**ONLY**: Structural segmentation for metric compliance.

---

## 📋 Target List (Priority Order)

| Target | Current | Reason | Action | Time |
|--------|---------|--------|--------|------|
| **GoogleAIProvider** | Complexity 40 | Infra risk + high complexity | 3-layer hard split | 1.5-2h |
| **HealthMonitor** | Complexity 24 | Mixed metric collection | Collector architecture | 1-1.5h |
| **PersonaDB** | Complexity 22 | Mixed I/O + validation | Disk I/O + validation extraction | 45-60m |
| **query CLI** | 550 LOC | Monolithic command | Command router pattern | 1-1.5h |
| **ResearchPlanner** | Complexity 17 | Mixed workflow logic | One workflow extraction | 30-45m |
| **FileEventHandler** | Complexity 16 | Edge case branching | One helper extraction | 15-30m |

---

## 🎯 Expected Results

**After completing Top 3**:
- GoogleAIProvider: 40 → ~12-14 ✅
- HealthMonitor: 24 → ~11-13 ✅
- PersonaDB: 22 → ~11-14 ✅

**Violations**: 7 → **3-4** (85-88% total reduction)

**After completing All 6**:
- **Target**: 7 → **0-2** violations
- **Total**: 24 → 0-2 (**92-100% reduction**)

---

## ✅ Success Criteria

1. ✅ GoogleAIProvider complexity < 15
2. ✅ HealthMonitor complexity < 15
3. ✅ PersonaDB complexity < 15
4. ✅ All tests passing
5. ✅ Zero regressions
6. ✅ Tag v2.0.3 at 85-90%

---

## 🔪 Execution Playbook

### Target 1: GoogleAIProvider

**Hard Cut**: 3-layer architectural split

```python
class GoogleAIProvider:
    def call(self, prompt, system, max_tokens, enable_search):
        # Orchestrator ONLY
        request = self._build_request(prompt, system, max_tokens, enable_search)
        raw_response = self._execute_call(request)
        return self._process_response(raw_response, prompt)
```

**New methods**:
- `_build_request()` - Config assembly
- `_execute_call()` - API execution + error handling
- `_process_response()` - Parsing + formatting

**Result**: 40 → ~12-14

---

### Target 2: HealthMonitor

**Hard Cut**: Collector architecture

```python
class HealthMonitor:
    def run_all_checks(self):
        # Orchestrator ONLY
        db = self._collect_db_metrics()
        mem = self._collect_memory_metrics()
        llm = self._collect_llm_metrics()
        return self._aggregate_results([db, mem, llm])
```

**New methods**:
- `_collect_db_metrics()` - Qdrant health
- `_collect_memory_metrics()` - Memory subsystem
- `_collect_llm_metrics()` - Provider health
- `_aggregate_results()` - Combine

**Result**: 24 → ~11-13

---

### Target 3: PersonaDB

**Hard Cut**: I/O + Validation separation

```python
class PersonaDB:
    def load_personas(self):
        raw = self._load_from_disk()
        validated = [self._validate_persona(p) for p in raw]
        return [p for p in validated if p]
```

**New methods**:
- `_load_from_disk()` - File I/O only
- `_validate_persona()` - Validation logic
- `_write_to_disk()` - Persistence

**Result**: 22 → ~11-14

---

### Target 4: query CLI

**Hard Cut**: Command router pattern

```python
def query(question, **args):
    # Router ONLY
    if args.get('export'):
        return _cmd_export(question, **args)
    elif args.get('council'):
        return _cmd_council(question, **args)
    else:
        return _cmd_search(question, **args)
```

**New functions**:
- `_cmd_search()` - Standard retrieval
- `_cmd_council()` - Council of Ricks mode
- `_cmd_export()` - Export functionality

**Result**: 550 → ~80-100 LOC

---

### Target 5: ResearchPlanner

**Surgical Cut**: Extract one workflow

```python
def _build_research_plan(self, question, gap_analysis):
    # Single-purpose plan builder
    ...
```

**Result**: 17 → ~14-15

---

### Target 6: FileEventHandler

**Surgical Cut**: Extract one branch

```python
def _handle_batch_events(self, events):
    # Batch processing logic
    ...
```

**Result**: 16 → ~14-15

---

## 🚫 What to AVOID

❌ Micro-optimizations (<10 lines)  
❌ Helper nibbling without reducing branches  
❌ Premature extraction  
❌ Over-engineering

✅ **DO**: Hard architectural boundaries, ZERO logic in orchestrators

---

## ✅ Verification After Each Target

```bash
# Lint check
python scripts/lint_check.py src

# Run tests
pytest tests/ -v

# Check specific file
python scripts/lint_check.py src/[target_file].py
```

---

## 📝 BMAD Compliance

**Method**: Surgical structural segmentation  
**Scope**: Metric compliance only  
**Risk**: Minimal (production-ready baseline)  
**Value**: Enterprise-grade clean slate

**This follows**: Stabilize → Cut → Stabilize pattern

---

**Prepared**: Epic 8 Marathon Team  
**Baseline**: v2.0.2 (71% reduction, production-ready)  
**Mission**: Surgical hard cuts only  
**No feature work. No scope creep.**
