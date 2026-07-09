# Epic 3 Preparation Checklist - RAG Query Engine

**Date Created:** 2025-11-26
**Epic:** Epic 3 - Intelligent RAG Query Engine
**Status:** Prep complete – Epic 3 ready to start
**Target Start:** After prep items complete

---

## Executive Summary

Epic 3 will deliver natural-language RAG queries with hybrid retrieval, query expansion, and citation-first responses. All technical dependencies from Epic 2 are in place. This checklist captures the preparation work identified in the Epic 2 retrospective that must be completed before starting Epic 3 Story 3.1.

**Prep Sprint Estimate:** 5-7 hours wall time (parallelized)

---

## Critical Path Items (Must Complete Before Epic 3 Starts)

### ✅ Item 1: Complete Story 2.4 Non-Functional Requirements

**Owner:** Dana (QA) + Charlie (Dev)
**Status:** ✅ **COMPLETED** (2025-11-26)
**Estimated:** 3-4 hours
**Actual:** Completed during Epic 2 closure

**Tasks Completed:**
- [x] Added structlog events for `jarvis memory search`:
  - Event: `memory_search_completed`
  - Logged: k, domains, result_count, duration_ms
  - No content exposure (metadata only)
- [x] Implemented error handling for invalid filters:
  - ValueError for empty queries with user-friendly message
  - ValueError for invalid k values (must be 1-50)
  - API returns 400 BAD_REQUEST for invalid input
  - API returns 503 SERVICE_UNAVAILABLE for service failures
- [x] Added latency validation test:
  - File: `tests/integration/memory/test_search_performance.py`
  - Test: `test_search_latency_p95_under_100ms_for_small_k`
  - Target: P95 <100ms for k<=10 queries
  - Runs 20 queries, validates P95 latency
- [x] Updated Story 2.4 tasks: All 5 tasks marked complete

**Verification:**
```bash
# Error handling tests
docker compose -f docker/docker-compose.yml run --rm jarvis \
  pytest tests/integration/memory/test_search_performance.py::test_search_error_handling_empty_query -v

# Performance validation (optional, marked @slow)
docker compose -f docker/docker-compose.yml run --rm jarvis \
  pytest tests/integration/memory/test_search_performance.py::test_search_latency_p95_under_100ms_for_small_k -v -s
```

**Success Criteria:** ✅ All criteria met
- [x] Structlog events implemented and tested
- [x] Error handling covers empty queries and invalid k
- [x] Performance test validates <100ms P95 target
- [x] Story 2.4 markdown updated with all tasks checked

---

### ⏳ Item 2: Activate and Validate LLM Client with Live API

**Owner:** Charlie (Dev)
**Status:** ✅ **COMPLETED (2025-11-26)**
**Estimated:** 2-3 hours
**Actual:** Documentation + first live run + verification complete

**Tasks:**
- [x] Document LLM activation steps in README
  - Section added: "LLM Client Activation (Story 2.5)"
  - Prerequisites: OpenRouter API key signup
  - Setup: .env configuration, verification commands
  - Testing: `jarvis memory compile --since 7d` example
  - Troubleshooting: Common errors and solutions
  - Cost management: Tracking, monitoring, optimization
- [x] **USER ACTION REQUIRED:** Add OpenRouter API key to `.env`:
  ```bash
  # LLM Provider Configuration
  OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
  ```
- [x] **USER ACTION REQUIRED:** Run first live LLM compilation:
  ```bash
  docker compose -f docker/docker-compose.yml run --rm jarvis \
    bash -lc "cd /workspace && PYTHONPATH=/workspace/src python -B -m jarvis.cli.main memory compile 7d"
  ```
- [x] **USER ACTION REQUIRED:** Verify cost tracking:
  ```bash
  docker compose -f docker/docker-compose.yml exec postgres psql -U jarvis -d jarvis \
    -c "SELECT p.name AS provider, l.model, l.cost_usd, l.created_at \
FROM llm_usage_log l \
JOIN llm_providers p ON p.id = l.provider_id \
ORDER BY l.created_at DESC \
LIMIT 5;"
  ```
- [x] **USER ACTION REQUIRED:** Verify insights ingested:
  ```bash
  docker compose -f docker/docker-compose.yml run --rm jarvis \
    jarvis memory search --source jarvis-insights "patterns"
  ```

**Success Criteria:**
- [x] One successful end-to-end memory compilation with real LLM calls
- [x] Cost logging wired to PostgreSQL `llm_usage_log` table (provider, model, tokens, cost_usd)
- [x] Compiled insights auto-ingested into Qdrant with `domain="jarvis-insights"`
- [x] Error handling validated at least via provider fallback and DB logging (API/DB failures)

**Notes:**
- LLM infrastructure is complete and tested with mocked responses
- Cost logging is now implemented in `src/jarvis/llm/client.py` and writes to `llm_usage_log`
- Activation requires user API key (not committed to repository)
- User can activate when ready for Epic 3 Story 3.1
- Cost estimate: ~$0.02-0.05 per week of conversations compiled

**Documentation:** See README.md section "LLM Client Activation (Story 2.5)" for complete instructions

---

### ⏳ Item 3: Research Query Expansion Strategies (Epic 3 Story 3.3 Prep)

**Owner:** Winston (Architect)
**Status:** ⏳ **OPTIONAL, NOT BLOCKING**
**Estimated:** 4-6 hours
**Priority:** High value, can run in parallel with Stories 3.1/3.2

**Tasks:**
- [ ] Research LLM-based query expansion approaches:
  - GPT-4 generating alternate phrasings
  - Claude generating semantic variations
  - Cost per expansion (input tokens + output tokens)
  - Latency impact on P95 <2s target
- [ ] Research heuristic expansion approaches:
  - Synonym replacement using WordNet/NLTK
  - Semantic similarity via embeddings
  - Template-based expansion (e.g., "how to X" → "tutorial X", "X guide")
  - Zero-cost, minimal latency overhead
- [ ] Evaluate local LLM options for cost efficiency:
  - llama.cpp with small models (7B, 13B)
  - Embedding-based query rewriting
  - Trade-off: lower quality vs. zero API cost
- [ ] Cost analysis and projections:
  - Tokens per expansion (estimated)
  - Cost per query with expansion enabled
  - Monthly cost projection at 1000 queries/day
  - Free tier viability
- [ ] Latency analysis:
  - Expansion overhead (milliseconds)
  - Impact on P95 latency target (<2s for expanded queries)
  - Parallel vs. sequential expansion execution
- [ ] Recommendation with trade-offs:
  - Approach 1: LLM-based (high quality, low-medium cost)
  - Approach 2: Heuristic (medium quality, zero cost)
  - Approach 3: Hybrid (LLM for complex queries, heuristics for simple)
  - Default recommendation with reasoning

**Deliverable:** Technical brief documenting:
- Research findings for each approach
- Cost/latency/quality trade-off matrix
- Recommended approach for Story 3.3 with rationale
- Implementation considerations

**Timeline:**
- Can start immediately (parallel with Items 1 & 2)
- Must complete before Story 3.3 planning begins
- Not blocking for Stories 3.1 or 3.2

**Notes:**
- Epic 3 can start before this research completes
- Findings will inform Story 3.3 implementation decisions
- If not complete by Story 3.3, defaults to heuristic approach with future LLM upgrade path

---

## Parallel Work Strategy

**Two parallel tracks:**

1. **Track A: Critical Path (Charlie + Dana)**
   - ✅ Item 1: Story 2.4 completion (Charlie + Dana, 3-4 hours) - COMPLETED
   - ⏳ Item 2: LLM validation (Charlie, 2-3 hours) - Documented, awaiting user activation
   - **Total:** 5-7 hours sequential

2. **Track B: Research (Winston)**
   - ⏳ Item 3: Query expansion research (Winston, 4-6 hours, parallel)
   - **Total:** 4-6 hours parallel to Track A

**Wall Time with Parallelization:** 5-7 hours (Track A critical path)

---

## Epic 2 → Epic 3 Readiness Assessment

### Dependencies from Epic 2: All Met ✅

- [x] **PostgreSQL conversation/message storage** - Operational with schema from Story 2.1
- [x] **Qdrant 6,755-point knowledge base** - Searchable with domain tagging
- [x] **Document ingestion pipeline** - Ready for additional content ingestion
- [x] **Memory search API with domain filtering** - `/api/memory/search` operational
- [x] **LLM client infrastructure (Story 2.5)** - Foundation built, ready for activation

### Quality Gates: All Met ✅

- [x] **Story 2.4 complete** - All tasks checked, observability implemented
- [x] **Integration tests passing** - Error handling and performance validated
- [x] **Documentation complete** - LLM activation steps in README

### Known Risks: Acknowledged

1. **LLM client untested with live APIs**
   - Risk: First real LLM integration in Story 3.1 might reveal issues
   - Mitigation: Comprehensive documentation in README, activation path clear
   - Status: ✅ Mitigated — first live `memory compile` and cost logging verified on 2025-11-26

2. **Query expansion strategy not finalized**
   - Risk: Story 3.3 implementation might pivot based on research findings
   - Mitigation: Research tracked in Item 3, defaults to heuristic if needed
   - Status: Acceptable, not blocking Stories 3.1/3.2

---

## Epic 3 Story Overview

**Epic 3: Intelligent RAG Query Engine**

### Story 3.1: Query Command & Response Envelope
- **User Value:** Natural-language queries return cited answers
- **Dependencies:** Epic 2 memory backbone ✅, LLM client ⏳ (user activation)
- **Estimated Complexity:** Medium (RAG loop integration)

### Story 3.2: Hybrid Retrieval Toggle
- **User Value:** Blend semantic + BM25 for edge cases
- **Dependencies:** Story 3.1 complete
- **Estimated Complexity:** Medium (PostgreSQL full-text search integration)

### Story 3.3: Query Expansion & Multi-Query Fusion
- **User Value:** Ambiguous queries still retrieve relevant knowledge
- **Dependencies:** Story 3.2 complete, Item 3 research (optional)
- **Estimated Complexity:** High (query generation, result fusion, deduplication)

### Story 3.4: Citation-First Response Formatting
- **User Value:** Every answer cites sources for verification
- **Dependencies:** Stories 3.1-3.3 complete
- **Estimated Complexity:** Low (formatting + metadata preservation)

**Total Stories:** 4
**Estimated Epic Duration:** 2-3 implementation sessions
**Business Value:** Memory backbone becomes actionable intelligence via natural-language interface

---

## Next Steps

1. **Immediate (User Action):**
   - [x] Review LLM activation documentation in README
   - [x] Add OpenRouter API key to `.env` when ready
   - [x] Run first live `jarvis memory compile --since 7d` (via Python module inside container)
   - [x] Verify cost tracking and insights ingestion

2. **Before Epic 3 Story 3.1:**
   - [x] Confirm Item 2 (LLM validation) complete OR accept deferred activation risk
   - [ ] Review Epic 2 retrospective action items: [docs/sprints/epic-2-retro-2025-11-26.md](epic-2-retro-2025-11-26.md)
   - [ ] Run Epic 3 kickoff meeting (optional)

3. **During Epic 3:**
   - [ ] Track Item 3 (query expansion research) progress (optional)
   - [ ] Incorporate research findings into Story 3.3 planning (optional)
   - [x] Monitor LLM costs via `llm_usage_log` table (found 1+ rows)

---

## Success Metrics

**Prep Sprint Complete When:**
- [x] Story 2.4 all tasks complete and tested
- [x] LLM activation documentation in README
- [x] User activates LLM (optional but recommended)
- [ ] Query expansion research in progress (optional)

**Epic 3 Ready to Start When:**
- [x] All Epic 2 dependencies met
- [x] Story 2.4 quality gates passed
- [x] LLM infrastructure documented and validated
- [x] User completes first live LLM compilation (recommended)

**Current Status:** ✅ **Epic 3 prep complete; Epic 3 in progress (Story 3.1)** (LLM activated and validated)

---

## References

- **Epic 2 Retrospective:** [docs/sprints/epic-2-retro-2025-11-26.md](epic-2-retro-2025-11-26.md)
- **Epic 3 Definition:** [docs/epics.md#Epic-3](../epics.md)
- **LLM Activation Guide:** [README.md#LLM-Client-Activation](../../README.md)
- **Story 2.4 Implementation:** [stories/2-4-memory-retrieval-filters-api.md](stories/2-4-memory-retrieval-filters-api.md)
- **Story 2.5 Implementation:** [stories/2-5-scheduled-memory-compilation.md](stories/2-5-scheduled-memory-compilation.md)

---

**Prepared by:** Claude (Dev Agent) + Bob (Scrum Master)
**Date:** 2025-11-26
**Next Update:** Before Epic 3 Story 3.1 kickoff
