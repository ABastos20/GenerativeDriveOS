# Epic 4.5: ARCHES Cognitive Stabilization - Planning Document

**Status**: Backlog → Planning
**Created**: 2025-12-04
**Dependencies**: Epic 4 Complete (✅)
**Priority**: CRITICAL - System Stabilization
**Philosophy**: "Transform ARCHES from pattern to controller"

---

## Executive Summary

Epic 4.5 transforms ARCHES from a distributed cognitive pattern into a **coherent, stateful, feedback-aware cognitive controller**. After Epic 4 introduced multi-agent orchestration (Council of Ricks), autonomous research, and hybrid retrieval, the system now exhibits emergent complexity that requires centralized orchestration and observability.

**The Problem**: You've built a real cognitive system. What it needs now is eyes on its own thoughts.

**The Solution**: Introduce centralized state management, agent-specific memory attribution, retrieval diversity control, and comprehensive cognitive tracing.

**Impact**: ARCHES will stop rerunning what it already knows, justify agent decisions with traceable inputs, control memory sprawl, and become a true orchestrator—not just a pattern.

---

## Current State Assessment

### What's Already Built (Epic 1-4)

#### ✅ ARCHES Pattern Components (Distributed)

**Assess** - [src/jarvis/memory/gap_analyzer.py](../../src/jarvis/memory/gap_analyzer.py)
- Gap detection: coverage, recency, contradictions
- Missing term extraction
- Confidence scoring for memory adequacy

**Research** - [src/jarvis/memory/research_planner.py](../../src/jarvis/memory/research_planner.py)
- Query generation from gaps
- LLM-powered research planning
- Fallback query strategies

**Critical** - [src/jarvis/memory/critical_integrator.py](../../src/jarvis/memory/critical_integrator.py)
- Source integration and conflict resolution
- Citation management
- Critical thinking application

**Hybrid** - [src/jarvis/memory/search.py](../../src/jarvis/memory/search.py)
- Semantic + keyword search fusion
- Domain filtering
- Temporal awareness (partial)

**Execute** - [src/jarvis/memory/research_executor.py](../../src/jarvis/memory/research_executor.py)
- Web search via Gemini Google Search grounding
- Content fetching and summarization
- Source collection and ingestion

**Store** - [src/jarvis/database/models.py](../../src/jarvis/database/models.py)
- Hybrid storage: Qdrant (vectors) + PostgreSQL (full docs)
- Conversation + Message + Document models
- Provenance tracking via `citation_provenance` JSONB

#### ✅ Council of Ricks (Multi-Agent System)

**Orchestration** - [src/jarvis/agents/orchestrator.py](../../src/jarvis/agents/orchestrator.py)
- `ParallelAgentOrchestrator`: Concurrent agent execution
- `PersonaRegistry`: Hot-reloadable persona configuration
- Persona loading from database and YAML

**Consensus** - [src/jarvis/agents/consensus.py](../../src/jarvis/agents/consensus.py)
- `WeightedChaosVoting`: Confidence × Weight × Consistency bonus
- Disagreement detection and resolution
- Voting transcript generation

**Parallel Invocation** - [src/jarvis/agents/parallel_invocation.py](../../src/jarvis/agents/parallel_invocation.py)
- Concurrent persona calls with ThreadPoolExecutor
- Response aggregation and error handling

#### ✅ Memory Infrastructure

**Temporal Chunks** - [src/jarvis/memory/temporal_chunk_manager.py](../../src/jarvis/memory/temporal_chunk_manager.py)
- Time-aware chunk management
- `doc_last_seen` tracking
- Recency scoring (partially implemented)

**Domain Heuristics** - [src/jarvis/memory/domain_heuristics.py](../../src/jarvis/memory/domain_heuristics.py)
- Automatic domain classification
- `CHAVAO_DOMAIN_MAP` taxonomy
- Domain-aware ingestion

**Query Expansion** - [src/jarvis/memory/query_expander.py](../../src/jarvis/memory/query_expander.py)
- Multi-query fusion
- Reciprocal rank fusion (RRF)
- Synonym expansion

### ⚠️ Problems Identified (Why Epic 4.5 is Needed)

#### 1. **Planning Drift / ARCHES Coordination Gap**

**Symptom**: Duplicate research or re-queries when memory already holds relevant info but isn't ranked correctly.

**Root Cause**: No central cognitive runtime controller. ARCHES spans code but isn't an explicit, state-aware orchestrator. Modules (gap_analyzer, research_planner, orchestrator) make independent decisions without shared state.

**User Experience**: "Why is this being re-queried again?" "Why is this agent redoing the plan?"

**Example**:
```
User: "What is Jarvis?"
→ Gap analyzer: 40% coverage
→ Research triggered
→ [Meanwhile, memory HAS 8 relevant docs but temporal decay lowered scores]
→ Re-query runs, fetches redundant info
```

#### 2. **Chunk Overload / Semantic Saturation**

**Symptom**: Personas generating verbose, repetitive answers pulling from overlapping chunks.

**Root Cause**: As memory grows, Qdrant returns redundant chunks from high-density ingests (large PDFs, recursive chat logs). No retrieval-time diversity enforcement.

**User Experience**: Voting disagreements caused by **differences in chunk context order**, not true semantic divergence. Retrieval feels "dull"—less precision than before.

**Example**:
```
Query: "Explain GenerativeDrive mission"
Retrieved: 15 chunks
→ Chunks 1-5: From GD overview doc (similar content)
→ Chunks 6-10: From session notes (similar content)
→ Chunks 11-15: From architecture doc (similar content)
Result: 3 clusters of redundant info, agents vote differently based on which cluster dominated their context
```

#### 3. **Document Versioning / Chunk Lineage Gap**

**Symptom**: Answers pulled from outdated document versions without "staleness" warnings.

**Root Cause**: Ingestion stores `doc_last_seen`, but retrieval doesn't enforce version freshness. No cross-version linkage in database.

**User Experience**: System answers from 2-month-old docs when newer versions exist (unless manually re-ingested).

**Example**:
```
docs/architecture-v1.md (ingested Nov 2024) → 50 chunks
docs/architecture-v2.md (ingested Dec 2024) → 52 chunks
Query retrieves chunks from BOTH versions
→ No warning about v1 being stale
→ Potential contradictions
```

#### 4. **Persona Divergence Opacity**

**Symptom**: Users/devs see conflicting persona answers but can't understand WHY agents disagreed.

**Root Cause**: Voting works, but **which documents each agent used** is opaque. No per-agent memory map exposed.

**User Experience**: Debugging requires manually inspecting chunk lists and logs. CLI `--show-all` shows votes but not provenance.

**Example**:
```
Rick: "GenerativeDrive focuses on energy systems" (confidence: 0.9)
Morty: "GenerativeDrive is about AI talent development" (confidence: 0.7)
→ Which chunks did each use?
→ Which domains?
→ Why the confidence gap?
→ NOT VISIBLE TO USER
```

#### 5. **Cross-Agent Memory Entanglement**

**Symptom**: All agents pull from the same RAG context → less diversity in reasoning than personas suggest.

**Root Cause**: No domain or goal-specific retrieval filters per agent. All agents see identical memory context.

**User Experience**: Personas designed to be independent are too similar in practice.

**Example**:
```
Rick (High IQ): Gets same 15 chunks as...
Morty (High Anxiety): Gets same 15 chunks
→ Only difference is system prompt and confidence
→ No architectural diversity in information access
```

---

## Epic 4.5 Stories Breakdown

### Story 4.5.1: ARCHES Runtime Controller

**Objective**: Introduce central `arches/controller.py` holding full plan state, memory state, and session tracking.

**Acceptance Criteria**:
- [ ] `ARCHESController` class manages query session lifecycle
- [ ] Tracks: plan state, retrieval history, agent results, used docs/chunks
- [ ] Real-time freshness scores for retrieved memory
- [ ] State flags: `is_research_triggered`, `fallback_needed`, `rerun_detected`
- [ ] Prevents redundant agent calls via state checking
- [ ] Integrates with chat.py and query.py as session manager

**Technical Design**:
```python
# src/jarvis/arches/controller.py

@dataclass
class ARCHESSession:
    """Single query session state."""
    session_id: str
    query: str
    plan_state: Dict[str, Any]  # {stage: status, started_at, completed_at}
    memory_state: Dict[str, Any]  # {chunks_used, domains, freshness_scores}
    agent_results: List[AgentResponse]
    flags: Dict[str, bool]  # research_triggered, fallback_needed, etc.
    created_at: datetime
    updated_at: datetime

class ARCHESController:
    """Central cognitive runtime controller."""

    def __init__(self):
        self.sessions: Dict[str, ARCHESSession] = {}
        self.logger = structlog.get_logger(__name__)

    def start_session(self, query: str, conversation_id: str) -> ARCHESSession:
        """Initialize new ARCHES session."""
        session = ARCHESSession(
            session_id=uuid.uuid4().hex,
            query=query,
            plan_state=self._init_plan_state(),
            memory_state={},
            agent_results=[],
            flags={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.sessions[session.session_id] = session
        return session

    def should_trigger_research(self, session: ARCHESSession, gap_analysis: Dict) -> bool:
        """Decide if research needed based on state + gap analysis."""
        # Check if already researched recently
        if session.flags.get("research_triggered"):
            self.logger.info("research_already_triggered", session_id=session.session_id)
            return False

        # Check gap severity
        if gap_analysis.get("coverage_gap") and gap_analysis.get("coverage_score", 0) < 0.6:
            return True

        return False

    def record_memory_usage(self, session: ARCHESSession, chunks: List[Any], domains: List[str]):
        """Track which chunks/domains were used."""
        session.memory_state.update({
            "chunks_used": [chunk.id for chunk in chunks],
            "domains": domains,
            "freshness_scores": self._compute_freshness(chunks),
            "retrieved_at": datetime.utcnow().isoformat(),
        })
        session.updated_at = datetime.utcnow()

    def _compute_freshness(self, chunks: List[Any]) -> Dict[str, float]:
        """Compute freshness scores for chunks."""
        scores = {}
        now = datetime.utcnow()
        for chunk in chunks:
            age_days = (now - chunk.created_at).days if hasattr(chunk, 'created_at') else 0
            scores[chunk.id] = 1.0 / (1 + age_days / 30)  # Decay over 30 days
        return scores
```

**Integration Points**:
- `chat.py`: Wrap query handling in ARCHESController session
- `query.py`: Same for CLI queries
- `gap_analyzer.py`: Receive session context, check flags before analysis

**Files Created**:
- `src/jarvis/arches/__init__.py`
- `src/jarvis/arches/controller.py`

**Tests**:
- `tests/unit/arches/test_controller.py`
- `tests/integration/arches/test_session_lifecycle.py`

---

### Story 4.5.2: Agent Memory Attribution

**Objective**: Attach memory chunk IDs, domains, and sources to each agent's response for full traceability.

**Acceptance Criteria**:
- [ ] `invoke_personas_parallel()` passes per-agent memory context
- [ ] Each agent response includes: `chunks_used`, `domains_accessed`, `sources`
- [ ] Voting transcript stores per-agent memory attribution
- [ ] CLI `--show-all` displays agent-specific chunk usage
- [ ] API `/api/chat` returns agent attribution in response

**Technical Design**:
```python
# src/jarvis/agents/response.py (enhancement)

@dataclass
class AgentResponse:
    """Enhanced with memory attribution."""
    persona_name: str
    content: str
    confidence: float
    # NEW: Memory attribution
    chunks_used: List[str]  # Chunk IDs
    domains_accessed: List[str]
    sources: List[str]  # doc_keys
    memory_freshness: float  # Average freshness of chunks used

# src/jarvis/agents/parallel_invocation.py (enhancement)

def invoke_personas_parallel(
    personas: List[Persona],
    prompt: str,
    context: str,
    chunks: List[Any],  # NEW: Pass chunks to agents
    domains: List[str],  # NEW: Pass domains
) -> List[AgentResponse]:
    """Invoke personas with memory attribution."""

    def _invoke_with_memory(persona: Persona) -> AgentResponse:
        # Build prompt with chunk IDs embedded
        attributed_context = _build_attributed_context(context, chunks)

        response = persona.invoke(prompt, attributed_context)

        # Parse which chunks were actually used (via citation analysis)
        chunks_used = _extract_used_chunks(response.content, chunks)

        return AgentResponse(
            persona_name=persona.name,
            content=response.content,
            confidence=response.confidence,
            chunks_used=[c.id for c in chunks_used],
            domains_accessed=list(set(c.domain for c in chunks_used if hasattr(c, 'domain'))),
            sources=[c.doc_key for c in chunks_used],
            memory_freshness=_compute_avg_freshness(chunks_used),
        )

    with ThreadPoolExecutor(max_workers=len(personas)) as executor:
        futures = [executor.submit(_invoke_with_memory, p) for p in personas]
        return [f.result() for f in futures]

def _build_attributed_context(context: str, chunks: List[Any]) -> str:
    """Add chunk IDs to context for attribution tracking."""
    lines = []
    for idx, chunk in enumerate(chunks, 1):
        lines.append(f"[Source {idx} | Chunk ID: {chunk.id}]")
        lines.append(chunk.content)
        lines.append("")
    return "\n".join(lines)

def _extract_used_chunks(content: str, chunks: List[Any]) -> List[Any]:
    """Parse which chunks were cited in agent response."""
    cited_nums = re.findall(r'\[(\d+)\]', content)
    cited_indices = [int(n) - 1 for n in cited_nums if n.isdigit()]
    return [chunks[i] for i in cited_indices if i < len(chunks)]
```

**Integration Points**:
- `chat.py`: Pass chunks and domains to invoke_personas_parallel()
- `consensus.py`: Store agent attribution in voting transcript
- CLI output: Format attribution in `--show-all` mode

**Database Changes**:
```sql
-- Add memory_attribution JSONB to messages table
ALTER TABLE messages
ADD COLUMN memory_attribution JSONB DEFAULT '{}';

-- Example structure:
-- {
--   "agents": [
--     {
--       "persona": "Rick",
--       "chunks_used": ["chunk-123", "chunk-456"],
--       "domains": ["GenerativeDrive", "BMAD"],
--       "sources": ["gd-overview", "bmad-methodology"],
--       "memory_freshness": 0.92
--     }
--   ]
-- }
```

**Files Modified**:
- `src/jarvis/agents/response.py`
- `src/jarvis/agents/parallel_invocation.py`
- `src/jarvis/agents/consensus.py`
- `src/jarvis/database/models.py`

**Alembic Migration**:
- `alembic/versions/20241204_add_memory_attribution.py`

**Tests**:
- `tests/unit/agents/test_memory_attribution.py`
- `tests/integration/agents/test_agent_attribution_e2e.py`

---

### Story 4.5.3: Memory Recency & Lineage Enforcement

**Objective**: Enforce document freshness at retrieval time, quarantine stale chunks, prioritize recent versions.

**Acceptance Criteria**:
- [ ] Retrieval compares `doc_last_seen` vs ingestion time
- [ ] Prioritize chunks from most recent document version
- [ ] Optional: Quarantine stale chunks if fresher doc exists
- [ ] Warning logs when retrieving from stale documents
- [ ] CLI flag: `--allow-stale` to override (default: false)

**Technical Design**:
```python
# src/jarvis/memory/search.py (enhancement)

def search_memory(
    query: str,
    k: int = 10,
    domains: List[str] = None,
    min_freshness: float = 0.5,  # NEW: Minimum freshness threshold
    allow_stale: bool = False,  # NEW: Override stale filtering
) -> List[SearchResult]:
    """Search with freshness enforcement."""

    # Standard semantic search
    raw_results = _semantic_search_qdrant(query, k * 2, domains)

    # Compute freshness scores
    now = datetime.utcnow()
    for result in raw_results:
        doc_age_days = (now - result.doc_last_seen).days if result.doc_last_seen else 999
        result.freshness_score = 1.0 / (1 + doc_age_days / 30)  # 30-day half-life

    # Filter by freshness (unless overridden)
    if not allow_stale:
        filtered = [r for r in raw_results if r.freshness_score >= min_freshness]
        if len(filtered) < k:
            logger.warning(
                "insufficient_fresh_results",
                requested=k,
                available=len(filtered),
                threshold=min_freshness,
            )
    else:
        filtered = raw_results

    # Check for document version conflicts
    filtered = _resolve_version_conflicts(filtered)

    # Sort by relevance × freshness
    filtered.sort(key=lambda r: r.score * (1 + 0.5 * r.freshness_score), reverse=True)

    return filtered[:k]

def _resolve_version_conflicts(results: List[SearchResult]) -> List[SearchResult]:
    """Prefer newer document versions, quarantine stale."""
    doc_groups = defaultdict(list)
    for result in results:
        base_key = result.doc_key.rsplit('-v', 1)[0]  # Strip version suffix
        doc_groups[base_key].append(result)

    resolved = []
    for base_key, group in doc_groups.items():
        if len(group) == 1:
            resolved.extend(group)
        else:
            # Multiple versions found
            group.sort(key=lambda r: r.doc_last_seen, reverse=True)
            latest = group[0]
            stale = group[1:]

            logger.warning(
                "version_conflict_detected",
                base_key=base_key,
                latest_version=latest.doc_key,
                stale_versions=[s.doc_key for s in stale],
            )

            # Only include latest
            resolved.append(latest)

    return resolved
```

**Database Changes**:
```sql
-- Add freshness_score computed column
ALTER TABLE documents
ADD COLUMN freshness_score FLOAT GENERATED ALWAYS AS (
    1.0 / (1 + EXTRACT(EPOCH FROM (NOW() - last_seen)) / (30 * 86400))
) STORED;

-- Index for freshness queries
CREATE INDEX idx_documents_freshness ON documents(freshness_score DESC);
```

**Integration Points**:
- All search functions: semantic, keyword, hybrid
- CLI: Add `--allow-stale` flag
- API: Add `allow_stale` parameter

**Files Modified**:
- `src/jarvis/memory/search.py`
- `src/jarvis/cli/query.py`
- `src/jarvis/api/chat.py`

**Tests**:
- `tests/unit/memory/test_freshness_filtering.py`
- `tests/integration/memory/test_version_conflict_resolution.py`

---

### Story 4.5.4: Retrieval Saturation Filter

**Objective**: Enforce retrieval diversity to prevent chunk overload and semantic redundancy.

**Technical Design**:
```python
# src/jarvis/memory/diversity.py (NEW FILE)

def apply_diversity_filter(
    results: List[SearchResult],
    max_results: int,
    diversity_mode: str = "balanced",  # "balanced" | "aggressive" | "minimal"
) -> List[SearchResult]:
    """Filter results to maximize topical diversity."""

    if diversity_mode == "minimal":
        return results[:max_results]

    # Compute similarity matrix between results
    similarity_matrix = _compute_pairwise_similarity(results)

    # Maximal Marginal Relevance (MMR) algorithm
    selected = []
    remaining = list(range(len(results)))

    # Start with highest-scoring result
    selected.append(remaining.pop(0))

    while len(selected) < max_results and remaining:
        scores = []
        for idx in remaining:
            # Relevance score
            relevance = results[idx].score

            # Redundancy penalty: similarity to already-selected results
            max_sim = max(similarity_matrix[idx][s] for s in selected)

            # MMR score
            lambda_param = 0.5 if diversity_mode == "balanced" else 0.7
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
            scores.append((mmr_score, idx))

        # Select highest MMR score
        _, best_idx = max(scores)
        selected.append(best_idx)
        remaining.remove(best_idx)

    return [results[i] for i in selected]

def _compute_pairwise_similarity(results: List[SearchResult]) -> np.ndarray:
    """Compute cosine similarity between all result pairs."""
    embeddings = np.array([r.embedding for r in results])
    return cosine_similarity(embeddings)
```

**Integration**:
```python
# In search.py
from jarvis.memory.diversity import apply_diversity_filter

def search_memory(..., diversity_mode: str = "balanced") -> List[SearchResult]:
    raw_results = _semantic_search_qdrant(query, k * 2, domains)
    # ... freshness filtering ...
    diverse_results = apply_diversity_filter(raw_results, k, diversity_mode)
    return diverse_results
```

**Files Created**:
- `src/jarvis/memory/diversity.py`

**Files Modified**:
- `src/jarvis/memory/search.py`

**Tests**:
- `tests/unit/memory/test_diversity_filter.py`

---

### Story 4.5.5: ARCHES Planner Feedback Loop

**Objective**: Enable ARCHES controller to react to execution outcomes and adapt plans.

**Technical Design**:
```python
# In arches/controller.py

class ARCHESController:
    def react_to_voting_outcome(
        self,
        session: ARCHESSession,
        voting_result: VotingResult,
    ) -> PlanAction:
        """Decide next action based on voting outcome."""

        # Voting tie or high disagreement
        if voting_result.is_tie or voting_result.disagreement_score > 0.7:
            self.logger.warning(
                "high_agent_disagreement",
                session_id=session.session_id,
                disagreement=voting_result.disagreement_score,
            )
            # Reroute: trigger research expansion
            return PlanAction.TRIGGER_RESEARCH_EXPANSION

        # Agent dropout (some agents failed)
        if len(voting_result.failed_agents) > 0:
            self.logger.error(
                "agent_execution_failure",
                failed=voting_result.failed_agents,
            )
            # Repair: retry with fallback agents
            return PlanAction.RETRY_WITH_FALLBACK

        # High chunk overlap detected
        if self._detect_chunk_overlap(session.memory_state) > 0.8:
            self.logger.warning("high_chunk_overlap", session_id=session.session_id)
            # Adjust: increase diversity filter
            return PlanAction.INCREASE_DIVERSITY

        # Success
        return PlanAction.COMPLETE

    def _detect_chunk_overlap(self, memory_state: Dict) -> float:
        """Compute overlap ratio in retrieved chunks."""
        chunks_used = memory_state.get("chunks_used", [])
        if len(chunks_used) < 2:
            return 0.0

        # Simple heuristic: count duplicate doc_keys
        doc_keys = [c.split(':')[0] for c in chunks_used]
        unique_docs = len(set(doc_keys))
        overlap = 1.0 - (unique_docs / len(chunks_used))
        return overlap
```

**Integration Points**:
- `chat.py`: After voting, call `controller.react_to_voting_outcome()`
- `research_executor.py`: Accept plan actions from controller

**Files Modified**:
- `src/jarvis/arches/controller.py`
- `src/jarvis/api/chat.py`

**Tests**:
- `tests/unit/arches/test_feedback_loop.py`

---

### Story 4.5.6: Cognitive Trace Log

**Objective**: Structured trace format for full query lifecycle observability.

**Technical Design**:
```python
# src/jarvis/arches/trace.py (NEW FILE)

@dataclass
class CognitiveTrace:
    """Complete trace of query processing."""
    trace_id: str
    session_id: str
    query: str

    # Inputs
    conversation_history: List[Dict]
    domains_requested: List[str]

    # Plan
    plan_state: Dict[str, Any]
    research_triggered: bool

    # Memory
    chunks_retrieved: List[str]
    chunk_scores: Dict[str, float]
    freshness_scores: Dict[str, float]
    diversity_mode: str

    # Agents
    agents_invoked: List[str]
    agent_responses: List[Dict]  # {persona, content, confidence, chunks_used}

    # Voting
    voting_result: Dict
    winner_persona: str
    disagreement_score: float

    # Output
    final_answer: str
    sources_cited: List[str]

    # Metadata
    total_latency_ms: float
    created_at: datetime

def log_cognitive_trace(trace: CognitiveTrace):
    """Persist cognitive trace to database."""
    with get_session() as session:
        trace_record = CognitiveTraceLog(
            trace_id=trace.trace_id,
            session_id=trace.session_id,
            query=trace.query,
            trace_data=asdict(trace),
            created_at=trace.created_at,
        )
        session.add(trace_record)

def replay_cognitive_trace(trace_id: str) -> CognitiveTrace:
    """Retrieve and reconstruct cognitive trace."""
    with get_session() as session:
        record = session.query(CognitiveTraceLog).filter_by(trace_id=trace_id).one()
        return CognitiveTrace(**record.trace_data)
```

**Database Schema**:
```sql
CREATE TABLE cognitive_traces (
    id SERIAL PRIMARY KEY,
    trace_id VARCHAR(64) UNIQUE NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    query TEXT NOT NULL,
    trace_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_trace_session (session_id),
    INDEX idx_trace_created (created_at DESC)
);
```

**CLI Command**:
```bash
# Replay a cognitive trace
jarvis trace replay <trace_id>

# Export trace to JSON
jarvis trace export <trace_id> --output trace.json

# List recent traces
jarvis trace list --limit 10
```

**API Endpoint**:
```python
@router.get("/api/traces/{trace_id}")
def get_cognitive_trace(trace_id: str) -> CognitiveTrace:
    """Retrieve cognitive trace by ID."""
    return replay_cognitive_trace(trace_id)
```

**Files Created**:
- `src/jarvis/arches/trace.py`
- `src/jarvis/cli/trace.py`
- `src/jarvis/database/models.py` (add CognitiveTraceLog)

**Alembic Migration**:
- `alembic/versions/20241204_add_cognitive_traces.py`

**Tests**:
- `tests/unit/arches/test_trace_logging.py`
- `tests/integration/arches/test_trace_replay.py`

---

## Implementation Phases

### Phase 1: Foundation (Stories 4.5.1 + 4.5.6)
**Duration**: 2-3 days
**Goal**: Establish ARCHES controller and trace logging infrastructure

**Tasks**:
1. Create `src/jarvis/arches/` module
2. Implement ARCHESController with session management
3. Implement CognitiveTrace schema and logging
4. Integrate controller into chat.py and query.py
5. Add database migration for cognitive_traces table
6. Add CLI commands: `jarvis trace list/replay/export`

**Validation**: ARCHES controller tracks session state; traces logged for every query

---

### Phase 2: Attribution & Freshness (Stories 4.5.2 + 4.5.3)
**Duration**: 2-3 days
**Goal**: Add agent memory attribution and enforce document freshness

**Tasks**:
1. Enhance AgentResponse with memory attribution fields
2. Modify invoke_personas_parallel() to pass chunks and track usage
3. Implement freshness scoring in search.py
4. Add version conflict resolution
5. Add memory_attribution JSONB to messages table
6. Update voting transcript to include attribution

**Validation**: CLI `--show-all` displays per-agent chunk usage; stale chunks filtered

---

### Phase 3: Diversity & Feedback (Stories 4.5.4 + 4.5.5)
**Duration**: 2-3 days
**Goal**: Implement retrieval diversity and reactive plan adjustment

**Tasks**:
1. Create diversity.py with MMR algorithm
2. Integrate diversity filter into all search functions
3. Implement feedback loop in ARCHESController
4. Add reaction logic for voting ties, agent failures, chunk overlap
5. Wire feedback actions into research executor

**Validation**: Retrieval returns diverse results; controller adapts plans based on outcomes

---

### Phase 4: Testing & Documentation
**Duration**: 1-2 days
**Goal**: Comprehensive test coverage and documentation updates

**Tasks**:
1. Unit tests for all new modules (controller, trace, diversity, attribution)
2. Integration tests for end-to-end ARCHES flows
3. Update README with ARCHES architecture diagram
4. Add observability guide: "Understanding Cognitive Traces"
5. Update API documentation with new endpoints

**Validation**: All tests passing; documentation complete

---

## Success Metrics

### Operational Metrics (Before vs After)

| Metric | Before Epic 4.5 | After Epic 4.5 |
|--------|----------------|----------------|
| Redundant research triggers | ~30% of queries | <5% of queries |
| Agent voting ties (high disagreement) | ~15% of queries | <5% of queries |
| Chunk overlap in retrieval | ~60% (avg) | <30% (avg) |
| Stale document warnings | 0 (undetected) | Logged + filtered |
| Trace observability | Logs only | Full cognitive trace |
| Agent attribution | Opaque | Fully traceable |

### User Experience Goals

- **For Users**: "Why did Jarvis say that?" → Full provenance via `jarvis trace replay`
- **For Developers**: Debugging agent disagreements becomes trivial
- **For System**: Self-aware, adaptive, doesn't waste resources on redundant work

---

## Non-Goals (Deferred to Later Epics)

- **LLM-based auto-plan generation** (Epic 5+)
- **Feedback learning loops for weight tuning** (Epic 6+)
- **Agent self-training or self-promotion** (Epic 7+)
- **Multi-user memory scoping** (Epic 8: Multi-Tenant)
- **Tool invocation guardrails** (Epic 8: Tool Security)
- **Graph-based provenance storage** (Epic 9: Advanced Observability)

---

## Post-4.5 Anticipated Challenges

*(These are expected to emerge AFTER Epic 4.5 is complete)*

### 1. Plan Explosion (ARCHES Scheduling Complexity)

Once ARCHES becomes stateful and reactive, plan construction may overload with subgoal trees, conflicting branches, or re-entrant mutations.

**Mitigation**: Introduce declarative plan schema (YAML/JSON), plan freezing, lifecycle states

### 2. Persona Trust Degradation

Some personas will perform better in certain domains; others may hallucinate more.

**Mitigation**: Track persona performance logs, adaptive weighting, trust scores per domain

### 3. Semantic Memory Collisions (Context Bleed)

Semantically similar but topically wrong chunks across domains (e.g. "tokens" in crypto vs ML).

**Mitigation**: Domain orthogonality constraints, context anchoring fields, shard Qdrant by domain

### 4. Undetected Document Decay (Silent Drift)

Long-term documents silently become obsolete without user awareness.

**Mitigation**: Periodic freshness audit jobs, auto re-ingestion suggestions, source validation checksums

### 5. Cross-User Memory Contamination (Multi-Tenant Risk)

Memory chunks may bleed across user sessions or tenants.

**Mitigation**: Enforce user scoping per chunk/doc, query-time filters (user_id, tenant_id), per-user trace logs

### 6. Tool Invocation Chaos

Autonomous agents invoking tools may silently corrupt memory with bad data or incomplete results.

**Mitigation**: Toolguard wrappers with retry + validation, quarantined memory layer, tool memory firewall

### 7. Answer Auditing Chain Weakness

Need full versioned trails: "Why did the system say that, back then?"

**Mitigation**: Version documents/chunks at ingestion, graph-format traces, CLI replay tool

---

## Risk Assessment

### Critical Risks

1. **Complexity Explosion**: ARCHES controller could become a god object
   - **Mitigation**: Keep controller focused on state + coordination; delegate execution to existing modules

2. **Performance Regression**: Freshness checks and diversity filtering add latency
   - **Mitigation**: Cache freshness scores, optimize diversity algorithm (MMR), parallel execution

3. **Migration Failures**: Adding JSONB fields to large tables
   - **Mitigation**: Idempotent migrations, background index creation, staged rollout

### Medium Risks

1. **Incomplete Attribution**: Agent responses may not cite all chunks used
   - **Mitigation**: Fallback to "unknown" attribution, log warnings

2. **Diversity Filter Too Aggressive**: May filter out relevant results
   - **Mitigation**: Three modes (minimal/balanced/aggressive), configurable per query

---

## Open Questions

1. **Should ARCHES sessions persist across multiple queries in a conversation?**
   - Option A: One session per query (stateless between queries)
   - Option B: Session spans full conversation (stateful)
   - **Recommendation**: Start with Option A (simpler), evolve to Option B

2. **How to handle agent attribution for streamed responses?**
   - Current design assumes batch responses
   - Streaming may require incremental attribution
   - **Recommendation**: Defer streaming support to Epic 4.6

3. **Should cognitive traces be stored indefinitely?**
   - Trade-off: Observability vs storage cost
   - **Recommendation**: TTL-based retention (30 days default, configurable)

---

## Conclusion

Epic 4.5 is **not a fix for broken code—it's an evolution into introspection**. You've built a machine that can think. Now you're giving it eyes on its own thoughts.

**After Epic 4.5, ARCHES will**:
- Stop rerunning what it already knows
- Justify agent decisions with traceable inputs
- Control memory sprawl and document drift
- Become a true orchestrator, not just a pattern

**Philosophy**: "You're crossing from cognitive execution into cognitive operations."

The system becomes alive enough to require care—and you're ready for that.

---

**Next Steps**:
1. Review and approve this planning document
2. Begin Phase 1: Foundation (Stories 4.5.1 + 4.5.6)
3. Run daily standups to track progress
4. Iterate based on implementation learnings

**Approval Required**: User (Ariel) + optional Codex/Antigravity review

---

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
