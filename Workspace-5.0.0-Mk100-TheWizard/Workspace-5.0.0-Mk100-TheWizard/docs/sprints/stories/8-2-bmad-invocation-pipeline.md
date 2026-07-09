# Story 8-2: BMAD Invocation Pipeline

**Epic**: 8 - Self-Improvement & Auto-Evolution  
**Story ID**: 8-2  
**Status**: Ready for Dev 🚀  
**Type**: Execution Infrastructure  
**Sprint**: TBD  
**Estimated Effort**: 10-14 hours  
**Priority**: HIGH (Enables autonomous actions)

---

## 📋 Story Overview

### User Story

**As a** Jarvis system capable of self-improvement,  
**I want** a standardized pipeline to invoke Build/Make/Analyze/Deploy actions,  
**So that** I can safely execute improvements in a controlled, traceable manner.

### Core Purpose

> **Standardized way to invoke "Build/Make/Analyze/Deploy" actions via sandboxed execution.**

---

## 🎯 Acceptance Criteria

### Part A: Pipeline Model

1. [ ] **Pipeline Definition**: YAML/JSON schema for pipeline steps
2. [ ] **Step Types**: build, test, analyze, deploy, rollback
3. [ ] **Dependency Graph**: Steps can depend on previous steps
4. [ ] **Timeout & Retry**: Configurable per step

### Part B: Pipeline Executor

5. [ ] **PipelineExecutor Class**: Runs pipelines in sandboxed environment
6. [ ] **Sandbox Isolation**: Docker-based or subprocess isolation
7. [ ] **Output Capture**: Structured logging of all step outputs
8. [ ] **Failure Handling**: Auto-rollback on step failure

### Part C: Pipeline API

9. [ ] **API Endpoint**: `POST /api/admin/pipelines/run` triggers pipeline
10. [ ] **Status Tracking**: `GET /api/admin/pipelines/{id}/status`
11. [ ] **History**: `GET /api/admin/pipelines/history`
12. [ ] **Cancel**: `POST /api/admin/pipelines/{id}/cancel`

### Part D: Safety Constraints

13. [ ] **Allowlist Commands**: Only pre-approved commands can run
14. [ ] **Resource Limits**: CPU, memory, time limits
15. [ ] **Audit Trail**: Every action logged with trace_id

---

## 📐 Technical Implementation Plan

### Phase 1: Pipeline Schema (~3-4h)

```yaml
# Example pipeline definition
name: "improve-retrieval"
version: "1.0"
steps:
  - name: analyze
    type: analyze
    command: "python scripts/analyze_retrieval.py"
    timeout: 300
    
  - name: implement
    type: build
    depends_on: [analyze]
    command: "python scripts/apply_improvement.py"
    
  - name: test
    type: test
    depends_on: [implement]
    command: "pytest tests/integration/ -v"
    
  - name: deploy
    type: deploy
    depends_on: [test]
    command: "docker restart jarvis-app"
    approval_required: true
```

### Phase 2: Executor (~4-6h)

```python
class PipelineExecutor:
    def run(self, pipeline: Pipeline) -> PipelineResult:
        """Execute pipeline with dependency resolution."""
        
    def run_step(self, step: PipelineStep) -> StepResult:
        """Execute single step in sandbox."""
        
    def rollback(self, pipeline_id: UUID):
        """Rollback to pre-pipeline state."""
```

### Phase 3: Sandbox (~3-4h)

```python
class Sandbox:
    def execute(self, command: str, timeout: int) -> ExecutionResult:
        """Run command in isolated environment."""
        
    def validate_command(self, command: str) -> bool:
        """Check against allowlist."""
```

---

## 🛠️ New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/admin/pipelines/run` | Start pipeline |
| GET | `/api/admin/pipelines/{id}/status` | Pipeline status |
| GET | `/api/admin/pipelines/history` | Execution history |
| POST | `/api/admin/pipelines/{id}/cancel` | Cancel running pipeline |

---

## 📦 Deliverables

### New Modules
- `src/jarvis/core/pipeline/executor.py`
- `src/jarvis/core/pipeline/sandbox.py`
- `src/jarvis/core/pipeline/schema.py`

### Configuration
- `config/pipelines/` - Pipeline definitions
- `config/sandbox_allowlist.yaml` - Approved commands

---

## Dev Agent Record

### Context Reference
- [8-2-bmad-invocation-pipeline.context.xml](./8-2-bmad-invocation-pipeline.context.xml)

### Agent Model Used
{{agent_model_name_version}}
