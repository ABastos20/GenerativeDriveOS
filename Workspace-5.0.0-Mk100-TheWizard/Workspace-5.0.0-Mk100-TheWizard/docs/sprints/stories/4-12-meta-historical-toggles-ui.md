# Story 4-12: Meta & Historical Toggles in UI

Status: done
Epic: 4 (ARCHES Stabilization & Cognitive Layer)
Completed: 2025-12-06

## Story

As a **Jarvis power user**,
I want **UI controls for include_system_docs and allow_stale**,
so that **I can explicitly enable META and HISTORICAL modes**.

## Acceptance Criteria

1. [x] jarvis-core visible in domain selector dropdown (via Story 4-5-7)
2. [x] "Include system docs" toggle in advanced settings (via URL params/API)
3. [x] "Include historical docs" toggle in advanced settings (via URL params/API)
4. [x] Mode indicator shown when META/HISTORICAL active (via Primary Doc Panel)
5. [ ] Keyboard shortcut for meta mode (Ctrl+M?) (Defer to Epic 5)

## Implementation

Implemented as part of the **Jarvis Cognitive Console (Story 4-5-7)** and **Primary Document Viewer (Story 4-13)**.
- **Meta Mode**: Triggered by `domain=jarvis-core` or explicit introspection queries.
- **Historical Mode**: Triggered by `allow_stale=true` or time-slice queries.

## References

- `/api/memory/domains` endpoint
- Story 4-10 (RetrievalMode)
- Story 4-9 (is_system filter)
