# Story 4.5.6: Cognitive Trace Log

Status: in-progress

## Story

As a **Jarvis developer debugging query processing**,
I want a **complete cognitive trace capturing the full query lifecycle**,
so that **I can replay, analyze, and understand every decision made during query handling**.

## Acceptance Criteria

1. [ ] `CognitiveTrace` dataclass captures: inputs, plan, memory, agents, voting, output, metadata
2. [ ] Traces persisted to `cognitive_traces` PostgreSQL table with JSONB `trace_data`
3. [ ] CLI commands: `jarvis trace list`, `jarvis trace replay <id>`, `jarvis trace export <id>`
4. [ ] API endpoint: `GET /api/traces/{trace_id}` returns full trace
5. [ ] Traces include timing: `total_latency_ms`, `created_at`
6. [ ] Trace IDs linkable from chat responses for debugging

## Tasks / Subtasks

- [ ] Task 1: Define CognitiveTrace schema (AC: #1)
  - [ ] Create `src/jarvis/arches/trace.py`
  - [ ] Define all trace fields as dataclass
  - [ ] Include conversation_history, domains, chunks, agents, voting, sources
- [ ] Task 2: Database schema (AC: #2)
  - [ ] Create `cognitive_traces` table
  - [ ] Columns: id, trace_id, session_id, query, trace_data (JSONB), created_at
  - [ ] Add indexes on session_id and created_at
  - [ ] Create alembic migration
- [ ] Task 3: Persistence functions (AC: #2)
  - [ ] `log_cognitive_trace()` - persist trace to DB
  - [ ] `replay_cognitive_trace()` - retrieve and reconstruct
- [ ] Task 4: CLI commands (AC: #3)
  - [ ] Create `src/jarvis/cli/trace.py`
  - [ ] Implement `list`, `replay`, `export` commands
  - [ ] Add to main CLI command group
- [ ] Task 5: API endpoint (AC: #4)
  - [ ] Add route to `src/jarvis/api/` or create `trace.py` router
  - [ ] Return CognitiveTrace as JSON
- [ ] Task 6: Integration (AC: #5, #6)
  - [ ] Capture trace at end of query processing
  - [ ] Include trace_id in chat response
- [ ] Task 7: Complete ARCHITECT SUGESTION MAJOR PART OF THE SYSTEM bellow.


## Dev Notes

- **Trace Size**: May be large; consider compression for trace_data
- **Retention**: Consider TTL or archival strategy for old traces
- **Privacy**: Traces contain user queries; handle appropriately

### Project Structure Notes

- New files: `src/jarvis/arches/trace.py`, `src/jarvis/cli/trace.py`
- Migration: `alembic/versions/20241204_add_cognitive_traces.py`
- Database: `src/jarvis/database/models.py` - add CognitiveTraceLog

### References

- [Source: docs/sprints/epic-4.5-arches-stabilization.md#Story-4.5.6]

## Dev Agent Record

### Context Reference

- [4-5-6-cognitive-trace-log.context.xml](docs/sprints/stories/4-5-6-cognitive-trace-log.context.xml)

### Agent Model Used

Gemini 2.5 Pro (BMAD Orchestrator Mode)

### Debug Log References

### Completion Notes List

### File List


### ARCHITECT SUGESTION MAJOR PART OF THE SYSTEM
🧠 CognitiveTrace — Dataclass Skeleton (Authoritative 4.5.6)

(Copy/paste this into your BMAD “Story Context” for Claude)

# src/jarvis/arches/trace.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4


@dataclass
class RetrievedChunkTrace:
    chunk_id: str
    doc_key: str
    version: Optional[int]
    domain: Optional[str]
    score_before_mmr: float
    score_after_mmr: float
    freshness_score: Optional[float] = None


@dataclass
class AgentTrace:
    name: str                     # e.g. "architect", "critic", "researcher"
    role: str                     # semantic role of the agent
    input_summary: str            # short distilled summary of inputs
    output_summary: str           # short distilled summary of outputs
    vote: Optional[float]         # voting / weighting
    latency_ms: int               # time spent in reasoning
    model_name: Optional[str]     # e.g. GPT/Claude model used


@dataclass
class ResearchCallTrace:
    query: str
    provider: str                 # e.g. "web-search", "bing", "memory-fallback"
    success: bool
    duration_ms: int
    results_count: int
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveTrace:
    # --- Core Identifiers ---
    trace_id: UUID = field(default_factory=uuid4)
    session_id: Optional[str] = None
    query: str = ""
    mode: str = "qa"                            # qa | research | planning | hybrid
    arches_version: str = "4.5.6"
    trace_schema_version: int = 1               # increments on schema change

    # --- Timing ---
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_latency_ms: Optional[int] = None
    phase_timings: Dict[str, int] = field(default_factory=dict)
    # e.g. {"retrieval_ms": 40, "council_ms": 120}

    # --- Retrieval Phase ---
    retrievers_used: List[str] = field(default_factory=list)
    diversity_mode: str = "balanced"
    k_initial: int = 0
    k_final: int = 0
    retrieval_events: List[RetrievedChunkTrace] = field(default_factory=list)

    # --- Council of Ricks ---
    agents: List[AgentTrace] = field(default_factory=list)

    # --- Research Loops ---
    research_calls: List[ResearchCallTrace] = field(default_factory=list)

    # --- Final Decision / Output ---
    final_answer_summary: Optional[str] = None
    sources: List[str] = field(default_factory=list)     # chunk_ids/doc_keys
    domains: List[str] = field(default_factory=list)
    confidence_estimate: Optional[float] = None

    # --- Meta ---
    model_versions: Dict[str, str] = field(default_factory=dict)
    severity: str = "normal"                    # normal | error | low_confidence | debug
    sampled: bool = True                        # indicates retained trace
    errors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # --- Raw storage (optional future use) ---
    meta: Dict[str, Any] = field(default_factory=dict)   # misc extra info

🧩 Important Integration Notes to Give Claude

Add this into your BMAD task if needed:

- Trace must be created at the very start of query processing in ARCHES controller.
- Subsystems (retrieval, MMR, council, research) append to the trace, but do NOT persist it.
- Only ARCHES writes the final trace via log_cognitive_trace() AFTER completion.
- Trace IDs must appear in final chat response {"trace_id": "..."}.
- No raw prompts, no raw LLM outputs (summaries only).
- Trace must remain deterministic and replayable without calling any LLM.

🧠 Result

This is now a rock-solid dataclass definition, architecturally consistent with ARCHES and scalable into Epic 5–10.

Claude will be able to implement:

DB schema

Alembic migration

CLI

API

Integration hooks

without hallucinating or omitting fields.