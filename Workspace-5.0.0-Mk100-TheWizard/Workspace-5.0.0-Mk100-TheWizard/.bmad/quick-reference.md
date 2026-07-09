# BMAD / BMM Quick Reference (Workspace)

This workspace is wired to **BMAD v6 / BMM 6.0.0‑alpha.10**. Use this as a one‑page refresher when picking work back up.

---

## Where Things Live

- **BMAD core:** `.bmad/`
- **BMM module:** `.bmad/bmm/`
- **Sprint + stories:** `docs/sprints/`
- **Epic definitions:** `docs/epics.md`
- **Story files:** `docs/sprints/stories/3-*.md`
- **Story context XML:** `docs/sprints/stories/3-*.context.xml`

---

## Typical Workflows (Method Track)

These are the ones we actually use day‑to‑day in this repo:

- **Story Context:** BMM → `4-implementation/story-context`
  - Inputs: epic + story ID
  - Outputs: `docs/sprints/stories/{story-id}.context.xml`
  - Purpose: lock in scope, artifacts, and AC before coding.

- **Dev Story:** BMM → `4-implementation/dev-story`
  - Inputs: story + context
  - Outputs: implementation notes, file list, test plan under the story’s “Dev Agent Record”.
  - Purpose: drive actual code + tests to “done”.

- **Sprint Status:** `docs/sprints/sprint-status.yaml`
  - Source of truth for:
    - Epic status: `backlog | contexted | done`
    - Story status: `backlog | drafted | ready-for-dev | in-progress | review | done`

---

## How to Read the Current State Quickly

1. **Which epic / story are we on?**
   - Open `docs/sprints/sprint-status.yaml`
   - Look for:
     - `epic-3: contexted`
     - `3-1-query-command-response-envelope: done`
     - `3-2-hybrid-retrieval-toggle: drafted`

2. **What does this story want?**
   - Open:
     - `docs/sprints/stories/3-2-hybrid-retrieval-toggle.md`
     - `docs/sprints/stories/3-2-hybrid-retrieval-toggle.context.xml`
   - Read:
     - Story text
     - Acceptance criteria
     - Tasks / Dev Notes

3. **Where’s the implementation?**
   - CLI:
     - `src/jarvis/cli/main.py`
     - `src/jarvis/cli/query.py`
   - Memory:
     - `src/jarvis/memory/search.py`
     - `src/jarvis/memory/ingest.py`
   - LLM:
     - `src/jarvis/llm/client.py`
     - `src/jarvis/llm/providers.py`

4. **Tests relevant to Epic 3:**
   - Unit:
     - `tests/unit/cli/test_query.py`
   - Integration:
     - `tests/integration/cli/test_query_integration.py`

---

## Quick Mental Model (Epic 3)

- **3.1 – Query Command & Response Envelope**
  - CLI entry: `jarvis query "question"` (module form in container)
  - Flow: Query → Embed → Qdrant search → Build context → LLM via `call_llm()` → Answer + citations / JSON.

- **3.2 – Hybrid Retrieval Toggle**
  - Extend search layer to blend:
    - Semantic (Qdrant) + Keyword (Postgres full‑text) with weights.
  - Wire `--retriever` and `--weight` into `query` CLI.

---

## Quick Helper Scripts

From workspace root:

```bash
./scripts/bmad_refresh.sh     # Reload BMAD context (READMEs + quick-reference)
./scripts/workspace_status.sh # Check git branch, Epic 3 stories, Docker status
./scripts/kill_background.sh  # Clean up lingering Docker build processes
```

## When in Doubt

- Treat `docs/sprints/stories/{id}.md` as the "what + why".
- Treat `{id}.context.xml` as the "constraints + artifacts".
- Treat BMAD's `dev-story` workflow as the "how to get it done".
- Run `./scripts/workspace_status.sh` to see current state.

