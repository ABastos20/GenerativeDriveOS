# Story 4.5.4: Retrieval Saturation Filter

Status: done

## Story

As a **Jarvis developer optimizing retrieval quality**,
I want **a diversity filter that prevents redundant chunks from dominating retrieval results**,
so that **agents receive topically diverse context and voting reflects true semantic differences**.

## Acceptance Criteria

1. [x] Implement Maximal Marginal Relevance (MMR) algorithm for chunk selection
2. [x] Support three diversity modes: `balanced` (λ=0.5), `aggressive` (λ=0.3), `minimal` (no filtering)
3. [x] Diversity filter applied after semantic search, before returning results
4. [x] Configurable via `--diversity` CLI flag
5. [x] Measurable reduction in chunk overlap (logged metric)
6. [x] No significant latency increase (<50ms for typical result sets)

## Tasks / Subtasks

- [x] Task 1: Create diversity module (AC: #1, #2)
- [x] Task 2: MMR algorithm (AC: #1)
- [x] Task 3: Integration with search (AC: #3)
- [x] Task 4: CLI flag (AC: #4)
- [x] Task 5: Observability (AC: #5)
- [x] Task 6: Performance validation (AC: #6)

## Dev Notes

- **MMR Formula**: Score = λ * relevance - (1-λ) * max_sim_to_selected
- **Same-doc floor**: 0.85 similarity for chunks from same doc_key
- **Pipeline position**: AFTER freshness/version resolution, BEFORE final k

### File List

- [NEW] src/jarvis/memory/diversity.py - MMR implementation
- [MODIFIED] src/jarvis/memory/search.py - Pipeline integration
- [MODIFIED] src/jarvis/cli/query.py - --diversity flag
- [NEW] tests/unit/memory/test_diversity_filter.py - 17 unit tests

## Dev Agent Record

### Agent Model Used

Gemini 2.5 Pro (BMAD Orchestrator Mode)

### Completion Notes List

- Created `apply_diversity_filter()` with MMR selection
- Same-doc similarity floor prevents chunk clustering
- Overlap metrics logged before/after filtering
- All 17 unit tests pass
