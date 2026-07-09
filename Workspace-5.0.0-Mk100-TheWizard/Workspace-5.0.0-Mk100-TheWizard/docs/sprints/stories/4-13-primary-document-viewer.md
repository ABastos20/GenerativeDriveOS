# Story 4-13: Primary Document Viewer & UX Authority

Status: done
Epic: 4 (ARCHES Stabilization & Cognitive Layer)
Completed: 2025-12-06

## Story

As a **Jarvis user engaging in deep research**,
I want **a persistent "Primary Document" panel that mirrors the dominant source of the conversation**,
so that **I can always access the full context of what we are discussing without losing it in the chat scroll**.

## Acceptance Criteria

1. [x] **Backend Persistence**: `ConversationPrimaryDoc` table stores the dominant document for each conversation.
2. [x] **Dominant Source Logic**:
   - New search results > Stored document (if score > threshold).
   - Stored document > Nothing (resurface if no new relevant results).
   - **Stickiness**: Vague intent ("that file") sticks to stored doc unless new result is overwhelmingly better (> 0.6).
3. [x] **Explicit Intent**: "Retrieve that file" or "Show me X" forces link injection.
4. [x] **Blue Links**: Markdown links `[text](url)` render as clickable blue links in the UI.
5. [x] **Clean Links**: Links use `/api/docs/filename` format (no internal paths).
6. [x] **Artifact Free**: No "below in the **" hallucinations.

## Technical Implementation

### Schema
See `4-13-primary-document-viewer.context.xml` for the `ConversationPrimaryDoc` schema.

### Logic Flow (`chat.py`)

1. **Search**: Perform vector/hybrid search.
2. **Select**: `_select_primary_doc` picks the best candidate (Score > 0.01).
3. **Stickiness**: If explicit intent is vague ("that file"), prefer stored doc over weak new results.
4. **Persist**: Save selection to `ConversationPrimaryDoc`.
5. **Inject**: Append `[View full filename](...)` hint to LLM response.

## Validation

- **Scenario 1 (Normal)**: "Explain Hydrogen" -> Panel shows `gd-hydrogen...`.
- **Scenario 2 (Shift)**: "Summarize memory.core" -> Panel updates to `memory.core.md`.
- **Scenario 3 (Stickiness)**: "Retrieve that file" -> Panel stays on `memory.core.md` (or whatever was active).
- **Scenario 4 (Explicit)**: "Show me notes.md" -> Panel updates to `notes.md`.

## Artifacts

- `src/jarvis/database/models.py`: `ConversationPrimaryDoc`
- `src/jarvis/api/chat.py`: Selection & Persistence Logic
- `src/jarvis/api/app.py`: Frontend Link Rendering
