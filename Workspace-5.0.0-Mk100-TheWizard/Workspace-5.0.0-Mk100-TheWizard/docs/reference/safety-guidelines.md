# Epic 8 Safety Guidelines: Agent Edit Constraints

## 🛡️ Core Principle: Reversible Autonomy

Epic 8 enables Jarvis to modify its own codebase. To prevent self-bricking, these constraints are **non-negotiable**.

---

## Rule 1: 600 LOC Agent Edit Limit

### Policy

**Any file > 600 LOC is READ-ONLY for agents.**

Agent must:
1. Propose a split strategy
2. Get human approval
3. Execute split
4. Then modify the smaller files

### Enforcement

```python
# Linter check (scripts/lint_check.py)
MAX_AGENT_EDIT_LOC = 600

def is_agent_editable(file_path: str) -> bool:
    loc = count_lines_of_code(file_path)
    return loc <= MAX_AGENT_EDIT_LOC
```

### Rationale

- **Prevents**: "Just one more patch" syndrome
- **Prevents**: God-File regression
- **Prevents**: Non-reversible formatting damage
- **Enables**: Surgical, reviewable changes only

### Violation Examples

❌ **BLOCKED**:
```
Agent: "I'll add a new feature to app.py"
System: "❌ app.py is 3860 LOC. Propose split first."
```

✅ **ALLOWED**:
```
Agent: "I'll modify chat_utils.py (89 LOC)"
System: "✅ Approved. File is agent-editable."
```

---

## Rule 2: Dataflow Boundary Enforcement

### Policy

Every function in agent-modified code must declare its dataflow role:

1. **Pure Transformation** - No I/O, deterministic
2. **I/O Boundary** - External calls only (DB, API, file system)
3. **Decision Logic** - Branching, no side effects

**No mixing allowed.**

### Implementation

```python
# src/jarvis/utils/dataflow.py

def pure_transform(func):
    """Deterministic transformation. No I/O, no side effects."""
    func.__dataflow_role__ = "pure"
    return func

def io_boundary(func):
    """I/O operations only. No business logic."""
    func.__dataflow_role__ = "io"
    return func

def decision_logic(func):
    """Branching logic. No I/O, no mutations."""
    func.__dataflow_role__ = "decision"
    return func
```

### Usage Example

```python
@pure_transform
def _build_prompt(context: Context, query: str) -> str:
    """Build LLM prompt from context."""
    return f"{context.preamble}\n\nQuery: {query}"

@io_boundary
def _call_llm(prompt: str) -> LLMResponse:
    """Call LLM API."""
    return call_llm(prompt=prompt)

@decision_logic
def _should_trigger_research(gap: GapAnalysis) -> bool:
    """Decide if research mode needed."""
    return gap.coverage_score < 0.6
```

### Rationale

- **Prevents**: Hidden side effects
- **Prevents**: Planner hallucination cascades (LLM can't reason about mixed responsibilities)
- **Enables**: Compositional testing (mock I/O, test pure logic independently)

### Linter Detection

```python
def detect_dataflow_violations(func_node: ast.FunctionDef) -> List[str]:
    violations = []
    
    role = get_dataflow_decorator(func_node)
    if not role:
        violations.append("Missing dataflow decorator")
        return violations
    
    if role == "pure":
        if has_io_calls(func_node):
            violations.append("Pure function contains I/O")
        if has_mutations(func_node):
            violations.append("Pure function mutates state")
    
    elif role == "io":
        if has_business_logic(func_node):
            violations.append("I/O boundary contains business logic")
    
    elif role == "decision":
        if has_io_calls(func_node):
            violations.append("Decision logic contains I/O")
    
    return violations
```

---

## Rule 3: Semantic Phase Splitting (Memory Pipeline)

### Policy

Memory ingestion/retrieval functions must be split by **semantic phase**, not utility type.

**Required phases**:
1. `validate()` - Input validation
2. `normalize()` - Format standardization
3. `classify()` - Taxonomy/metadata assignment
4. `persist()` - Storage operations

### Anti-Pattern

❌ **DON'T** split by utility:
```python
# BAD: Utility-based splitting
def _file_helpers():
    pass

def _metadata_helpers():
    pass

def _storage_helpers():
    pass
```

### Correct Pattern

✅ **DO** split by semantic phase:
```python
# GOOD: Phase-based splitting
def _validate_file_input(path: Path) -> ValidationResult:
    """Phase 1: Check file exists, readable, supported."""
    pass

def _normalize_file_content(raw: bytes) -> str:
    """Phase 2: Extract text, clean encoding."""
    pass

def _classify_document(content: str) -> DocumentMetadata:
    """Phase 3: Detect domain, doc_type."""
    pass

def _persist_to_storage(content: str, meta: DocumentMetadata) -> IngestionResult:
    """Phase 4: Write to Postgres + Qdrant."""
    pass
```

### Rationale

- **Prevents**: Taxonomy drift (classification isolated)
- **Prevents**: Re-ingestion bugs (normalization idempotent)
- **Enables**: Pipeline testing (test phases independently)

---

## Rule 4: State Externalization (Before Deferral)

### Policy

Before deferring large controller refactors (e.g., ARCHESController), **extract explicit state object first**.

### Required Pattern

```python
# Step 1: Extract state (DO THIS FIRST)
@dataclass
class ArchesState:
    active_memories: List[MemoryRef]
    conversation_context: ConversationContext
    pending_actions: Queue[Action]
    execution_history: List[ExecutionRecord]

# Step 2: Inject state explicitly
class ARCHESController:
    def __init__(self, state: ArchesState):
        self.state = state  # Explicit dependency
    
    def process(self, input: Input) -> Output:
        # Pass state explicitly, no hidden mutations
        return self._execute_pipeline(self.state, input)
```

### Rationale

- **Prevents**: Hidden mutable state disasters
- **Enables**: Deterministic hot-reload (state serializable)
- **Enables**: Easier future splitting (state boundaries clear)

---

## Enforcement Workflow

### Pre-Commit (Human Developer)

```bash
# scripts/pre-commit.sh
python scripts/lint_check.py src
python scripts/check_dataflow_boundaries.py src
```

### Pre-Agent-Edit (Autonomous Mode)

```python
def agent_can_edit(file_path: str) -> tuple[bool, str]:
    # Check 1: LOC limit
    if not is_agent_editable(file_path):
        return False, f"File exceeds 600 LOC. Propose split first."
    
    # Check 2: Dataflow boundaries present
    if not has_dataflow_decorators(file_path):
        return False, f"File missing dataflow role markers."
    
    # Check 3: Semantic phases (if memory pipeline)
    if is_memory_pipeline_file(file_path):
        if not has_semantic_phases(file_path):
            return False, f"Memory pipeline missing semantic phase structure."
    
    return True, "File is agent-editable."
```

---

## Summary Checklist

Before merging any refactoring that enables Epic 8:

- [ ] All files ≤ 600 LOC (or marked READ-ONLY)
- [ ] All functions decorated with dataflow roles
- [ ] Memory pipeline split by semantic phases
- [ ] Large controllers have state externalized
- [ ] Linter enforces all rules
- [ ] Pre-commit hooks active
- [ ] Agent edit guard active

**Violation = Epic 8 deployment blocked** ⛔
