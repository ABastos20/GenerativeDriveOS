# Jarvis Export Integration Plan

This plan describes how GPT export data under `docs/gpt export/` is integrated into this Workspace and into Jarvis’ behavior. Treat this as a living document: update statuses and notes as work progresses.

## Phase 1 – Normalize GPT Export into Project Docs

**Goal:** Turn raw GPT export into stable, versioned docs under `docs/jarvis/`.

- [x] Create `docs/jarvis/` structure:
  - [x] `docs/jarvis/persona.md` – Jarvis identity, values, defaults.
  - [x] `docs/jarvis/operating-manual.md` – operating rules and decision flow.
  - [x] `docs/jarvis/playbooks/` – task‑oriented playbooks.
  - [x] `docs/jarvis/integration-plan.md` – this file.

- [x] Add import script:
  - [x] `scripts/import_gpt_export.py`:
    - Reads `docs/gpt export/conversations.json` and `user.json`.
    - Builds:
      - `docs/jarvis/conversation-index.md` – Jarvis‑titled conversations.
      - `docs/jarvis/user-export-snapshot.md` – raw user export snapshot.
  - [x] Extend to:
    - Detect other Jarvis‑relevant threads (by tags/keywords such as GenerativeDrive, hydrogen, telemetry, NTT).
    - Seed initial playbooks from frequently repeated patterns (architect prep, GD energy, hydrogen/water-loop, telemetry/infra).

- [x] Curate from generated docs:
  - [x] Manually review `conversation-index.md` and `user-export-snapshot.md`.
  - [x] Promote recurring patterns into dedicated playbooks under `docs/jarvis/playbooks/` (architect meeting prep, GD energy partnerships, hydrogen & water-loop, telemetry & infra).

## Phase 2 – Wire Jarvis Core into Runtime & Workflows

**Goal:** Make Jarvis persona/ops docs first‑class inputs to stories and agents.

- [x] Architecture & docs:
  - [x] Update `docs/architecture.md` to reference `docs/jarvis/*` as part of FR2/FR4 context.
  - [x] Update `docs/agent-guidelines.md` to mention Jarvis persona/operating‑manual as project‑level instructions.

- [x] Workflows:
  - [x] Ensure `story-context` / `dev-story` workflows treat `docs/jarvis/*` as part of `{document_project_content}` (added `jarvis_core` pattern).
  - [ ] Add a short “Jarvis meta” checklist to relevant workflows (e.g., confirm behavior aligns with persona + operating manual).

- [x] Code helpers:
  - [x] Add a small config/helper module (`src/jarvis/core/jarvis_config.py`) that:
    - Knows paths to `docs/jarvis/persona.md`, `operating-manual.md`, and `gd-overview.md`.
    - Exposes helpers to load these docs for prompt construction or RAG.

## Phase 3 – Make Jarvis Core Searchable in Memory

**Goal:** Jarvis can retrieve its own rules via the memory system.

- [x] **COMPLETED 2025-11-25** Ingest core docs:
  - [x] Ingested `docs/jarvis/persona.md` (2 chunks).
  - [x] Ingested `docs/jarvis/operating-manual.md` (2 chunks).
  - [x] Ingested 306 GPT conversations from `docs/gpt export/conversations.json` (~4,989 chunks).
  - [x] Total: **6,755 points** in Qdrant "knowledge" collection.
  - [ ] Ingest selected playbooks as they are created.

- [x] **COMPLETED 2025-11-25** Tagging strategy:
  - [x] Ingestion payloads include:
    - `domain = "jarvis-core"` for persona.md and operating-manual.md.
    - `domain = "jarvis-conversations"` for GPT export conversations.
    - Metadata: `source_file`, `section`, `title`, `conversation_id`, `chunk_index`, `create_time`, `ingested_at`.

- [ ] Retrieval (Story 2.4):
  - [ ] When building retrieval flows (Epic 2.4 / Epic 3), ensure queries can:
    - Filter on `domain = "jarvis-core"` when we need meta‑instructions.
    - Filter on `domain = "jarvis-conversations"` for GPT export history.
    - Blend Jarvis core context with story/architecture context as needed.

## Phase 4 – Align Assistants with Jarvis Core

**Goal:** Both local tools and external UIs (web, IDE) follow the same Jarvis rules.

- [ ] Local (this repo / CLI / agents):
  - [x] Treat `docs/jarvis/persona.md` and `operating-manual.md` as project‑level guidance.
  - [ ] Add a short reminder in `README_BMAD.md` or `docs/full-documentation.md` about Jarvis docs and how to update them.

- [ ] External (web UI GPT and others):
  - [ ] Copy key sections of `persona.md` / `operating-manual.md` into custom instructions or system prompts on the web UI.
  - [ ] Periodically reconcile differences between web‑side instructions and repo‑side docs.

## Phase 5 – Maintenance & Evolution

**Goal:** Keep Jarvis core consistent as the system evolves.

- [ ] Establish a simple process:
  - [ ] When Jarvis behavior changes, update `docs/jarvis/persona.md` and any affected playbooks.
  - [ ] Optionally re‑run `scripts/import_gpt_export.py` when new GPT exports are available and curate differences.

- [ ] Track changes:
  - [ ] Use concise commit messages referencing Jarvis core (e.g., “Update Jarvis persona from latest GPT export”).
  - [ ] Consider tagging releases when Jarvis’ behavior/contract changes materially.

---

**Notes for assistants working in this repo:**

- Before major design or behavior changes, skim:
  - `docs/jarvis/persona.md`
  - `docs/jarvis/operating-manual.md`
  - Relevant files under `docs/jarvis/playbooks/`
- Treat this plan as the checklist for integrating and maintaining Jarvis’ exported knowledge. Update checkbox statuses as work is completed.
