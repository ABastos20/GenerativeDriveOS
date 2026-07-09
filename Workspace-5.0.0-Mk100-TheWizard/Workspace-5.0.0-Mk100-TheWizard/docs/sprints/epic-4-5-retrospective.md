# Epic 4.5 Retrospective – ARCHES Cognitive Stabilization

**Status:** ✅ Complete  
**Period:** 2025-11 – 2025-12-05

---

## Stories Completed

| Story | Name | Status |
|-------|------|--------|
| 4.5.1 | ARCHES Runtime Controller | ✅ done |
| 4.5.2 | Agent Memory Attribution | ✅ done |
| 4.5.3 | Memory Recency & Lineage Enforcement | ✅ done |
| 4.5.3b | Qdrant `is_latest` Payload Filter | ✅ done |
| 4.5.4 | Retrieval Saturation Filter (MMR) | ✅ done |
| 4.5.5 | ARCHES Planner Feedback Loop | ✅ done |
| 4.5.6 | Cognitive Trace Log | ✅ done |
| 4.5.7 | Jarvis Cognitive Console UI | ✅ done |
| 4-13 | Primary Document Viewer | ✅ done |
| 4-13-b | UX Authority Enforcement | ✅ done |

---

## Story 4.5.3b Final Verification

### Backfill Status ✅

| Metric | Value |
|--------|-------|
| Chunks scanned | 94 |
| Marked as latest | 94 |
| Marked as stale | 0 |
| Dry-run updates needed | 0 (all correct) |

- **New ingests:** Include `is_latest=true` in Qdrant payload
- **Historical corpus:** Backfill ran successfully (2025-12-05)
- **Script:** `scripts/backfill_is_latest.py` working
- **Future action:** Run benchmarks at ~500K chunks

## Story 4-13 & 4-13-b Final Verification

### Features ✅
- **Primary Doc Panel:** Persists across queries, updates on topic change.
- **Blue Links:** Markdown links `[text](url)` render as clickable blue links.
- **UX Authority:**
    - **Low Threshold:** Updates for low-score topics (e.g. Hydrogen).
    - **Explicit Intent:** "Retrieve that file" forces link injection.
    - **Stickiness:** Vague intent sticks to stored doc; Named file overrides.
    - **Artifacts:** "below in the **" artifacts eliminated.

---

## What Jarvis Gained

After Epic 4 & 4.5, Jarvis moved from "smart RAG with personas" to:

> **Cognitive OS with brain, spine, black box, and cockpit.**

- **Cognitive Stability:** ARCHES owns session lifecycle, Recency/Lineage enforcement.
- **User Authority:** Primary Document Viewer ensures the user always has access to the source of truth.
- **Observability:** Every query has a CognitiveTrace; UI has domains/tags steering.
- **Self-Correction:** Planner reacts to disagreement; Gap analysis triggers research.

---

## Technical Debt Resolved

- `is_latest` index-level filtering ready for 1M+ chunks
- Backfill script available for corpus migration
- `--allow-stale` preserved for historical queries
- **Story 4-13:** Consolidated primary doc selection logic, removed redundant UI toggles.

## Future Scaling Actions

1. Run `scripts/backfill_is_latest.py` after major corpus migrations
2. Add `jarvis admin index-health` to sample `is_latest` coverage
3. Run p50/p90 benchmarks when corpus hits ~500K chunks
4. **UX:** Monitor "Stickiness" feedback in wild; consider "Pin Document" feature.
