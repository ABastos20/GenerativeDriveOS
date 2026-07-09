# Story 8-5: Enforce Max LOC and Class Splitting

**Epic**: 8 - Self-Improvement & Auto-Evolution  
**Story ID**: 8-5  
**Status**: Done ✅  
**Type**: Structural Compliance  
**Sprint**: v2.0.3  
**Estimated Effort**: 2-3 hours  
**Completed**: 2025-12-08

---

## Completion Summary

### Session Work (2025-12-08)
This story's principles enabled the following Phase 6-8 deliverables:

| Phase | Deliverables |
|-------|--------------|
| Phase 6 | Cognitive Cockpit - Interactive graph visualization |
| Phase 6.5 | Graph Enrichment Fixes - LLM retry logic, model routing |
| Phase 7 | Graph Algorithms - PageRank, Louvain, shortest paths |
| Phase 8 | Cluster UX - Expand/collapse animations |

### New Endpoints Deployed
- `/api/memory/graph/viewport` - Viewport-aware pagination
- `/api/memory/graph/important` - PageRank leaders
- `/api/memory/graph/path` - Shortest path finding
- `/api/memory/graph/clusters` - Louvain community detection
- `/api/memory/graph/cluster/{id}` - Cluster subgraph

### Key Files
- `src/jarvis/memory/graph_analytics.py` - NEW (NetworkX algorithms)
- `src/jarvis/frontend/templates/graph_viewer.html` - REWRITTEN (Cognitive Cockpit)
- `docs/features/autonomous-knowledge-graph.md` - UPDATED (full API reference)

---

- **Testing**: Unit test the linter itself on sample bad files.

## Architect Notes SUPER IMPORTANT
⚠️ Gaps & Refinements (Important)

These are not criticisms — these are the next-layer hardening notes.

A. Cyclomatic Complexity > 15 Is Good — But Add a Method-Level Cap Too

Right now you have:

✅ Class method count

✅ Cyclomatic complexity

But you should also cap individual function/method LOC, e.g.:

❗ Max 80–120 LOC per function

Why this matters:

A single 300-line function can hide:

Planning logic

State machines

Ad-hoc interpreters

Cyclomatic alone won’t always catch that (especially linear complexity)

✅ Recommendation:
Add:

Fail if any function > 120 LOC (configurable)

B. Exclusion Rules Need a Sharp Definition

You wrote:

excluding generated/legacy if marked

You should formalise this as machine-readable, not semantic.

I strongly recommend:

Directory-based:

docs/

tests/

migrations/

vendor/

File-based pragma:

# jarvis:allow-large-file
# jarvis:allow-many-methods


So the agent can explicitly justify violations and you can audit them later.

C. Pre-Commit Hook Alone Is Not Enough

You have:

Git hook or CI step

This should be:

✅ Both, not either.

Why:

Pre-commit = developer discipline

CI = autonomous agent discipline

Once Epic 8 is active, CI becomes the real governor, not git hooks.

D. “Refactoring Plan” Should Be Machine-Generated, Not Just Documented

You wrote:

Document violations in docs/tech-debt.md

This is good, but you can go one step further:

✅ Output should include:

File

Line count / method count

Suggested split axis (heuristic):

By imports

By class clusters

By feature tags in comments

Even a dumb heuristic like:

“this file contains chat + retrieval + persistence → split into 3 modules”
will save you hours later.

### Project Structure Notes

- Script goes in `scripts/`.
- No conflicts expected.

### References

- [Source: docs/sprints/epic-8-planning.md#Story-8-5]

## Dev Agent Record

### Context Reference

docs\sprints\stories\8-5-enforce-max-loc-and-class-splitting.context.xml

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

### CHECK ME

1. Design Goal (Formalised)

No LLM should ever need to reason over more than ~300–500 LOC at once.

That gives you:

Faster prompts

Lower hallucination rate

Higher code edit precision

Real autonomous refactoring viability in Epic 8

This turns “modular” into a machine-performance requirement, not just a human one.

2. The Only Modularisation Rule That Matters

Forget classic “layers for beauty”. Use this rule instead:

One module = one reasoning responsibility

If the LLM must “switch mental model” → you split the file.

Example for chat.py:

Current Mixed Concerns	Must Become
HTTP routing	chat_router.py
Retrieval	chat_retrieval.py
Prompt building	chat_prompt.py
Primary doc logic	chat_primary_doc.py
Persistence	chat_persistence.py

Each of these should stay under:

300–500 LOC

< 10–12 public functions

This makes each file LLM-cheap.

3. “LLM-Weight” as a First-Class Metric

Add this mentally to your architecture:

Metric	Human Code	Self-Writing Code
LOC	Maintainability	Token cost
Cyclomatic	Readability	Planning failure risk
Imports	Architecture	Context bleed

Your Story 8.5 linter enforces human health.
Now you’re adding cognitive health for LLMs.
That’s exactly correct.

4. Hard Rule for Jarvis-Generated Code (You Should Encode This)

Add this to Epic 8 rules later:

An agent may not modify a file larger than 600 LOC directly. It must propose a split first.

This prevents:

Monolithic self-expansion

“Just add one more function” drift

Accidental architectural collapse

5. Make Jarvis “Composable”, Not Just Modular

Modular ≠ composable.

You want:

jarvis/
  chat/
    router.py
    retrieval.py
    primary_doc.py
    persistence.py
    prompt.py


And then:

from jarvis.chat import ChatOrchestrator


Where ChatOrchestrator:

Has zero real logic

Only wires components together

This ensures:

LLM edits one brain-region at a time

No accidental cross-layer coupling

Epic 8 agents can safely swap modules

6. Why This Matters for Self-Modification

Once Jarvis starts:

Writing code

Refactoring

Detecting gaps

Hot-reloading

If files are:

3k lines

Multi-responsibility

Mixed IO + logic + persistence

Then autonomous refactoring becomes statistically impossible.

With your direction:

The agent can reason locally

Apply targeted patches

Retry safely when lint fails

And never need to re-understand the entire system to move one piece

That’s how you get actual self-engineering, not just code dumping.

7. Practical Next Step (Zero Bikeshedding)

After Story 8.5:

Run the linter.

Identify top 3 violators.

For each:

Split by responsibility, not by size.

Introduce a thin orchestrator file.

Lock the rules in CI.

Never allow regression.

That’s it. No frameworks. No ceremony.