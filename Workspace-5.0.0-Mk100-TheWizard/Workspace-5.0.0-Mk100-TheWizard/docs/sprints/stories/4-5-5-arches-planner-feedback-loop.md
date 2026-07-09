# Story 4.5.5: ARCHES Planner Feedback Loop

Status: ready-for-dev

## Story

As a **Jarvis cognitive system**,
I want the **ARCHESController to react to voting outcomes and adapt plans dynamically**,
so that **I can self-correct when agents disagree, fail, or produce redundant outputs**.

## Acceptance Criteria

1. [ ] `PlanAction` enum defines: COMPLETE, TRIGGER_RESEARCH_EXPANSION, RETRY_WITH_FALLBACK, INCREASE_DIVERSITY
2. [ ] Controller detects voting ties and high disagreement (> 0.7 threshold)
3. [ ] High disagreement triggers research expansion action
4. [ ] Agent execution failures trigger retry with fallback agents
5. [ ] High chunk overlap (> 0.8) triggers diversity filter increase
6. [ ] All plan actions logged with structured events
7. [ ] Actions executed automatically after voting in chat flow

## Tasks / Subtasks

- [ ] Task 1: Define PlanAction enum (AC: #1)
  - [ ] Create enum in `src/jarvis/arches/controller.py`
  - [ ] Document action semantics
- [ ] Task 2: Implement `react_to_voting_outcome()` (AC: #2, #3, #4, #5)
  - [ ] Check disagreement score threshold
  - [ ] Check failed_agents list
  - [ ] Implement `_detect_chunk_overlap()` helper
  - [ ] Return appropriate PlanAction
- [ ] Task 3: Logging (AC: #6)
  - [ ] Structured log for each decision path
  - [ ] Include session_id, disagreement score, action taken
- [ ] Task 4: Integration with chat flow (AC: #7)
  - [ ] Call `react_to_voting_outcome()` after voting in chat.py
  - [ ] Execute returned action (or queue for next iteration)
- [ ] Task 5: Action handlers
  - [ ] Implement research expansion trigger
  - [ ] Implement fallback agent retry
  - [ ] Implement diversity adjustment
- [ ] Task 6: Complete architects notes
- [ ] Task 7: Apply Mandatory Architect Notes
    - [ ] Validate enum design
    - [ ] Apply planner loop guards
    - [ ] Log actions into CognitiveTrace
    - [ ] Keep planner behaviour local
    - [ ] Centralise logic inside ARCHES controller
    - [ ] Ensure overlap + disagreement follow defined formulas
    - [ ] Add no-action regression test

## Dev Notes

- **Disagreement Threshold**: 0.7 chosen to trigger on meaningful disagreement, not noise
- **Chunk Overlap**: Computed as `1 - (unique_docs / total_chunks)`
- **Fallback Strategy**: Re-invoke with subset of personas if some failed

### Project Structure Notes

- Extends: `src/jarvis/arches/controller.py` (from 4.5.1)
- Modifies: `src/jarvis/api/chat.py`

### References

- [Source: docs/sprints/epic-4.5-arches-stabilization.md#Story-4.5.5]
- [Source: src/jarvis/agents/consensus.py] - Voting result structure

## Dev Agent Record

### Context Reference

- [4-5-5-arches-planner-feedback-loop.context.xml](docs/sprints/stories/4-5-5-arches-planner-feedback-loop.context.xml)

### Agent Model Used

Gemini 2.5 Pro (BMAD Orchestrator Mode)

### Debug Log References

### Completion Notes List

### File List

### Architect notes REFERENCE READ FIRST DO LAST

1. PlanAction enum – add a NOOP and keep it local

Right now:

COMPLETE, TRIGGER_RESEARCH_EXPANSION, RETRY_WITH_FALLBACK, INCREASE_DIVERSITY

I’d explicitly add:

NOOP (or NO_ACTION)

Reason: sometimes everything is fine. You don’t want to overload COMPLETE with “continue with current answer”. Semantics become clearer:

NOOP – “nothing special to do, proceed as planned”

COMPLETE – “stop, final answer confirmed” (if you want that distinction)

If you don’t need a separate COMPLETE, a simple set is fine:

class PlanAction(Enum):
    NOOP = "noop"
    TRIGGER_RESEARCH_EXPANSION = "trigger_research_expansion"
    RETRY_WITH_FALLBACK = "retry_with_fallback"
    INCREASE_DIVERSITY = "increase_diversity"


Keep 4.5.5 per-query, local, not “global tuning” – global learning comes later.

2. Wire it into CognitiveTrace instead of ad-hoc logs

You already have 4.5.6. Don’t reinvent logging.

Update AC #6:

All plan actions logged with structured events

I’d clarify:

Plan actions must be recorded in both:

structured logs (structlog), and

CognitiveTrace (e.g. tags.append("planner:TRIGGER_RESEARCH_EXPANSION") and/or meta["planner_actions"] list).

This ensures:

Planner decisions are visible in

CLI trace show

DB trace_data

Later offline analysis.

A simple pattern:

trace.tags.append(f"planner:{action.value}")
trace.meta.setdefault("planner_actions", []).append({
    "action": action.value,
    "disagreement": disagreement_score,
    "overlap": overlap_score,
    "failed_agents": failed_agents,
})

3. Define disagreement source and loop guard

You refer to:

detects voting ties and high disagreement (> 0.7 threshold)

Assuming VotingResult already has disagreement_score: float and maybe votes: Dict[agent, weight].

Two musts:

Clarify in code/docstring that “disagreement” comes from VotingResult.disagreement_score (not recomputed ad-hoc).

Add a loop guard: planner can only trigger each action type at most once per query, or overall at most N planner steps.

Otherwise you risk:

High disagreement → research → still high → research again → loop.

So in react_to_voting_outcome() you can check:

if "planner:TRIGGER_RESEARCH_EXPANSION" in trace.tags:
    # already did that this session, don’t repeat


or keep a small planner state in the session.

4. Chunk overlap – use what 4.5.4 already gives you

You wrote:

Chunk Overlap: Computed as 1 - (unique_docs / total_chunks)

Good heuristic. I’d:

Compute it from CognitiveTrace.retrieval_events (doc_key).

Use it as a sanity trigger: in theory, with MMR working, high overlap (>0.8) should be rare. So:

if overlap > 0.8 → log a planner action:

temporarily switch diversity_mode to aggressive on next retrieval;

mark trace with tags += ["planner:INCREASE_DIVERSITY"].

But limit this:

Only apply diversity bump once per query.

Only adjust diversity for the next retrieval in that session, not globally.

5. Action handlers – keep them very small and bounded

You already split:

research expansion

fallback retry

diversity adjustment

Key rules:

TRIGGER_RESEARCH_EXPANSION

Use existing research_executor.execute_research(...).

Consume same query + maybe a refined question or explicit gap description from VotingResult (if available).

Append new chunks to memory / retrieval, then re-run council once, not indefinitely.

RETRY_WITH_FALLBACK

Only retry once, with a reduced persona set, e.g.:

drop agents that failed or timed out,

keep 1–2 “robust” personas (architect + critic).

Must record in trace:

tags += ["planner:RETRY_WITH_FALLBACK"]

maybe meta["fallback_agents"] = ["architect", "critic"]

INCREASE_DIVERSITY

For this story, I’d keep it per-query:

set diversity_mode = "aggressive" for the next retrieval in this controller session.

Do not change default config, only the in-memory session state.

You don’t need a full “planner state machine” yet; just a small PlannerState in the session with:

@dataclass
class PlannerState:
    diversity_mode: str = "balanced"
    research_expanded: bool = False
    fallback_used: bool = False

6. Integration point – don’t bury logic in chat.py

Your story says:

Call react_to_voting_outcome() after voting in chat.py

I’d rather:

chat endpoint stays dumb: it calls ARCHES controller and gets back:

answer, trace, maybe planner_actions

controller owns:

calling react_to_voting_outcome()

running extra steps (research, retry, diversity change)

updating trace

So adjust Task 4 to:

chat.py should not implement planner logic, only call the controller abstraction (e.g. controller.handle_query() that internally does voting+planner+retry).

If current architecture already has the council in ARCHES, keep all planner logic there, not in API layer.

7. Tests – add one “no-regression” case

In tests/unit/arches/test_feedback_loop.py:

One test must assert: if

disagreement below 0.7,

no failed agents,

overlap below 0.8,

then:

react_to_voting_outcome(...) returns PlanAction.NOOP (or COMPLETE, depending on what you choose),

no additional calls to research/fallback/diversity handlers.

That prevents planner from “always doing something clever” when not needed.

Syntehtic refinement
🧠 Architect Notes — Mandatory Constraints (MUST APPLY BEFORE CODING)
Add as final section in Story 4.5.5

These notes override all previous ambiguity and constrain implementation.
Claude should read them first before solving the story.

1. PlanAction Enum MUST include NOOP

Required enum values:

class PlanAction(Enum):
    NOOP = "noop"  # no adjustments required
    TRIGGER_RESEARCH_EXPANSION = "trigger_research_expansion"
    RETRY_WITH_FALLBACK = "retry_with_fallback"
    INCREASE_DIVERSITY = "increase_diversity"


Reason: disambiguates “no action needed” vs “final answer”.

2. ALL Planner Outputs MUST be logged in CognitiveTrace

CognitiveTrace must store:

Which action was chosen

Why (disagreement, overlap, failed agents)

Planner-level metadata

Implementation pattern:

trace.tags.append(f"planner:{action.value}")
trace.meta.setdefault("planner_actions", []).append({
    "action": action.value,
    "disagreement": disagreement_score,
    "overlap": overlap_score,
    "failed_agents": failed_agents,
})


This is required for visibility and debugging.

3. Planner MUST NOT loop indefinitely

A planner action may only occur once per query per type.

Implement simple in-session planner state:

@dataclass
class PlannerState:
    diversity_adjusted: bool = False
    research_expanded: bool = False
    fallback_used: bool = False


Guard example:

if action == PlanAction.TRIGGER_RESEARCH_EXPANSION and state.research_expanded:
    return PlanAction.NOOP

4. Integration MUST stay inside ARCHES controller

The API layer (chat.py) MUST NOT implement planner logic.
Correct architecture:

chat.py → controller.handle_query()
              ↳ retrieval
              ↳ council
              ↳ react_to_voting_outcome()
              ↳ optional planner step (research/fallback/diversity)
              ↳ final answer


Only the controller triggers plan actions and updates the trace.

5. Chunk overlap MUST be computed from 4.5.4 trace events

Use:

unique_docs = len(set(ev.doc_key for ev in trace.retrieval_events))
total = len(trace.retrieval_events)
overlap = 1 - (unique_docs / total)


This depends on 4.5.4 and fits perfectly with the CognitiveTrace from 4.5.6.

6. High disagreement MUST be sourced from VotingResult

Do NOT recompute from agent outputs.

Use:

voting_result.disagreement_score


Threshold recommended: 0.7

7. Action semantics must be local-only

4.5.5 MUST NOT change global config.

Each action adjusts behaviour only within the current query session:

diversity_mode = "aggressive" only for next retrieval

fallback agents only override personas for this run

research expansion runs once per query

Global learning comes later (Epics 5+).

8. Replay safety

Because CognitiveTrace is deterministic and replayable:

Planner MUST NOT store raw prompts, raw LLM outputs, or huge blobs.

Only summaries may be kept.

9. Tests MUST include a “no-regression/no-action” case

When:

disagreement < 0.7

no failed agents

overlap < 0.8

Then:

PlanAction.NOOP
