# Story 4.7: Web Chat Console (BMAD Lab UI)

Status: done

## Story

As a BMAD practitioner,  
I want a minimal web chat console backed by the RAG engine and conversation store,  
So that I (and Raquel/Ariel) can talk to Jarvis like an OpenAI chat while staying fully grounded in our own knowledge base.

## Acceptance Criteria

1. **Given** the Docker stack is running, **When** I open `/chat` in a browser, **Then** I see a Jarvis BMAD Console with:
   - A left sidebar listing recent conversations (title = last assistant message snippet, plus message count).
   - A main chat pane that replays the active conversation history.
   - An input box with `strict` and `domain` controls wired into the RAG query.
2. **Given** I send a message from the web UI, **When** `/api/chat` is called, **Then** Jarvis:
   - Retrieves context from Qdrant using the existing RAG pipeline (semantic / keyword / hybrid + optional expansion).
   - Calls the LLM via the cost-first router.
   - Returns an answer plus a `sources[]` array compatible with the CLI JSON envelope.
3. **Given** a chat turn completes, **When** I reload `/chat`, **Then**:
   - The active conversation is restored using the stored `conversation_id`.
   - History is replayed from Postgres via `GET /api/conversations/{id}?page_size=100`.
4. **Given** an assistant message includes citations, **When** it is rendered in the web UI, **Then**:
   - A `Sources:` strip appears under the answer.
   - Each chip shows `[id] domain s=score` (or file path when no domain).
   - Hovering a chip opens a small balloon with file path, optional section/chunk id, and a short preview of the chunk text.
5. **Given** retrieval returns no context, **When** I send a message:
   - With `strict` enabled, **Then** the response indicates insufficient context and no citations are shown.
   - With `strict` disabled, **Then** Jarvis can answer based on conversation history alone (creative mode), but without fabricating citations.

## Tasks / Subtasks

- [x] **Task 1:** Define chat schemas and endpoint contract  
  - [x] Add `ChatRequest`, `ChatResponse`, `ChatSource`, and `ChatMetadata` to `src/jarvis/api/schemas.py` (aligned with `jarvis query --json-output` sources structure).  
  - [x] Include `message`, `conversation_id`, `user_id`, `provider`, `source`, `k`, `max_tokens`, `retriever`, `weight`, `strict_mode`, and `expand` in `ChatRequest`.  
  - [x] Include `conversation_id`, `message_id`, `query`, `response`, `sources[]`, and `metadata` in `ChatResponse`.

- [x] **Task 2:** Implement `/api/chat` endpoint using the existing RAG loop  
  - [x] Create `src/jarvis/api/chat.py` with a `POST /api/chat` route.  
  - [x] Reuse retrieval logic from `src/jarvis/cli/query.py` (`search_memory`, `keyword_search`, `hybrid_search`, `expanded_search`) including settings-driven defaults and strict-mode behaviour.  
  - [x] Build the same system + user prompts as the CLI, including strict-mode constraints.  
  - [x] Call `call_llm` via the provider router (`provider="auto"` by default) and map LLM response into `ChatResponse`.  
  - [x] Construct `sources[]` with `id`, `content`, `source_file`, `section`, `domain`, `relevance_score`/`score`, and optional `chunk_id`/`hash`.  
  - [x] Ensure error handling returns appropriate HTTP status codes (400 for bad parameters, 503 for backend failures).

- [x] **Task 3:** Persist conversations and messages  
  - [x] Use the existing `Conversation` and `Message` models in `src/jarvis/database/models.py`.  
  - [x] On each `/api/chat` call:
    - Create a new `Conversation` if `conversation_id` is omitted, or re-use the provided one (404 if not found).  
    - Insert a `Message` row for the user message (`role="user"`).  
    - Insert a `Message` row for the assistant answer (`role="assistant"`), including LLM metadata (`provider`, `model`, `token_count`, `cost_usd`).  
    - Store `sources[]` into `Message.citation_provenance` for assistant messages.  
  - [x] Implement a `GET /api/conversations?limit=20` endpoint returning lightweight conversation summaries (id, user_id, created/updated times, last_message, last_message_at, message_count).  
  - [x] Validate that `GET /api/conversations/{id}?page_size=100` returns the conversation with messages ordered and shaped for the UI.

- [x] **Task 4:** Build the web chat UI shell (`/chat`)  
  - [x] Add a `GET /chat` route in `src/jarvis/api/app.py` returning a single-page HTML/CSS/JS console.  
  - [x] Layout:
    - Left sidebar listing recent conversations from `GET /api/conversations?limit=20` with an active state and `+ New` button.  
    - Main area with header (status), messages pane, and input area.  
  - [x] Implement client-side logic to:
    - Read/write `conversation_id` from `localStorage` (`jarvis_conversation_id`).  
    - On load, call `GET /api/conversations/{id}?page_size=100` to replay history when `conversation_id` exists.  
    - On send, call `POST /api/chat` with `message`, `conversation_id`, `user_id="web-ui"`, `k`, `expand`, `source`, and `strict_mode`.  
    - Update the sidebar after each message (via `GET /api/conversations?limit=20`).

- [x] **Task 5:** Wire strict mode and domain bias  
  - [x] Add `strict` checkbox and `domain` text input to the UI, wiring them into the `/api/chat` request as `strict_mode` and `source`.  
  - [x] In `search_memory`, bias default retrieval domains toward `jarvis.conversations` when no explicit `source` is provided, so GPT export–backed executive summaries are more likely to ground answers.  
  - [x] Increase `k` and `expand` defaults slightly for the web UI payload (e.g., `k=12`, `expand=3`) to enrich context for exploratory conversations.

- [x] **Task 6:** Implement citations strip + balloon  
  - [x] Render a `Sources:` row under each assistant reply using `data.sources` for live responses and `msg.citation_provenance` for reloaded history.  
  - [x] Each chip shows `[id] domain s=score` (or file path when domain is empty).  
  - [x] On hover, show a small fixed-position balloon with `source_file`, optional `section`/`chunk_id`, and a short preview of the chunk text.  
  - [x] Keep the JS implementation conservative (ES5, ASCII-only) to avoid breaking the inline script.

- [x] **Task 7:** Documentation updates  
  - [x] Update `README.md` with a “Web Chat UI (Jarvis BMAD Console)” section (how to access, what it does, citations behaviour).  
  - [x] Update `README_BMAD.md` with a BMAD-style breakdown (Business / Model / Architecture / Delivery) of the web chat.  
  - [x] Update `docs/full-documentation.md` with `/api/chat` and `/chat` details (schemas, endpoints, domain bias, strict vs creative mode).  
  - [x] Update `docs/epics.md` to add Story 4.7 under Epic 4 or note it as a FR9 slice tied to existing RAG stories.

## Dev Notes

- The chat endpoint reuses the **same retrieval and prompt logic** as the CLI `jarvis query` command to avoid divergence. Any future changes to RAG behaviour should be applied in shared code paths (`src/jarvis/memory/search.py` and the core prompt builder).  
- Conversation persistence is intentionally simple: each `/api/chat` turn logs both user and assistant messages, which allows later analytics stories (Epic 4/5/9) to use the same tables.  
- Strict mode is important for BMAD lab work: it gives you a clear “librarian only” channel, while non-strict mode unlocks creative, history-only replies when no memory is found. Make sure UI lab usage defaults (strict off/on) are called out in docs.  
- Domain bias towards `jarvis.conversations` is safe in the lab context, but future production deployments may tune `infer_query_domains` differently; keep this behaviour clearly documented.  
- Citations balloons are deliberately lightweight and read‑only; no deep linking yet. If/when deep links are added (e.g., VS Code file jump), prefer using `chunk_id`/`hash` to construct URLs without hardcoding absolute paths.

### Learnings / Guidance for Future Agents

- When extending the web UI (e.g., dashboards, agent management), **do not fork the RAG logic** into browser-only code. Keep retrieval, domain inference, and prompt construction server-side so CLI, MCP, and web remain consistent.  
- Use `ChatRequest` / `ChatResponse` as the canonical contract for chat-like interactions; if fields are added, extend rather than rename to avoid breaking existing clients.  
- Be cautious with inline JavaScript in `app.py`:
  - Stick to ES5 and ASCII-only to avoid parse issues in constrained environments.  
  - Prefer small, well-tested helpers (like the current citation balloon) over complex UI frameworks.  
- For FR9 evolution (dashboards, telemetry views), consider moving the web UI into a separate static asset pipeline or SPA, but keep the existing `/chat` as a low-friction, always-available console for BMAD experiments.  
- Always update:
  - `docs/epics.md` with new stories / acceptance criteria.  
  - `docs/full-documentation.md` with API/behaviour changes.  
  - `README.md` / `README_BMAD.md` with user-facing capabilities, especially when new surfaces like this chat UI are added.

