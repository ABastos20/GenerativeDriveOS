## Story 4.6: Time‑Aware Retrieval & Domain Heuristics

**Epic:** 4 – Council of Ricks Multi‑Agent Reasoning  
**Type:** Engineering / Infra brain upgrade  

### User Story

As a knowledge engineer,  
I want Jarvis’ retrieval to respect both *what* a chunk is about and *when / how mature* it is,  
So that answers feel like talking to a brain that remembers its full history but leans on its latest, converged understanding.

### Scope

This story wires three related capabilities into the memory and retrieval stack:

- Heuristic domain + tag inference based on file paths, keywords, and “chavões” (telecom, cyber, infra, sciences, math, GD, BMAD…).  
- Document‑level cataloguing (first/last seen, step count, doc‑level domains/tags) and propagation back into chunks.  
- Time‑aware retrieval weighting that slightly favours later / richer iterations of a document or conversation while preserving the full timeline.

### Acceptance Criteria

1. **Heuristic domain and tag assignment**
   - **Given** chunks ingested from personal workspace, OneDrive, and GD PDFs,  
     **When** `jarvis analytics catalog-domains` runs,  
     **Then** each point in Qdrant has:
       - `primary_domain` set to a stable key (e.g. `conversations.jarvis`, `gd.generative_drive`, `cyber.security`, `docs.markdown`, `science.physics`, `math.calculus`, `bmad.method`, `project.sprints`, `infra.docker`, `infra.postgres`, `infra.qdrant`).  
       - `domains` as a small list of domains (primary first).  
       - `tags` containing keyword‑style tags (snake/kebab case) such as `generative_drive`, `hydrogen`, `solar`, `sines`, `smart_grid`, `water_loops`, `mitre_attack`, `stix_2.1`, `tenable`, `nessus`, `math_calculus`, `science_neurology`, etc.  
     **And** running the domain summary helper shows non‑trivial counts for GD, cyber, BMAD, infra and science domains (not only the generic core domains).

2. **Document‑level profiles and propagation**
   - **Given** `jarvis analytics catalog-docs` runs over the `knowledge` collection,  
     **When** the catalog completes,  
     **Then** each point has additional payload fields:
       - `doc_key` (source_file path or conversation_id),  
       - `doc_primary_domain` (majority vote over the document’s chunk domains, ignoring `docs.*` / `generic.unknown` when possible),  
       - `doc_tags` (up to 20 aggregated tags for the document),  
       - `doc_first_seen` / `doc_last_seen` (float timestamps derived from `create_time` / `ingested_at`),  
       - `doc_step_count` (number of chunks / messages in that document).  
     **And** chunks that had `primary_domain = generic.unknown` inherit `doc_primary_domain` as their new `primary_domain`.

3. **Time‑aware retrieval weighting (“yolo brain mode”)**
   - **Given** Qdrant payloads include `doc_step_count`,  
     **When** a user runs `jarvis query` (or `jarvis memory search` via `search_memory`),  
     **Then** the search pipeline:
       - Retrieves results across the *full* timeline (no hard time filter by default),  
       - Computes a time weight per result based on `doc_step_count` normalized across the result set,  
       - Multiplies the original vector similarity score by `time_weight = 1 + α * norm_step`, where `α` is controlled via `JARVIS_TIME_WEIGHT_ALPHA` (default `0.2`),  
       - Preserves the original score in `metadata["original_score"]` and exposes `metadata["time_weight"]`.  
     **And** results from richer / later documents (higher `doc_step_count`) are slightly favoured in order, while early assumptions remain visible in the tail of the list.

4. **Fallback and safety behaviour**
   - **Given** a query whose inferred domains lead to an empty semantic result set,  
     **When** `search_memory` runs,  
     **Then** it logs `memory_search_domain_fallback` with the inferred domains and retries search **without a domain filter**,  
     **And** still applies time weighting on the final result set.
   - **Given** a deployment where `doc_step_count` is missing or not yet populated,  
     **When** `search_memory` runs,  
     **Then** `_apply_time_weight` leaves scores and order unchanged (no errors, no re‑ordering).

5. **Configuration & observability**
   - **Given** `JARVIS_TIME_WEIGHT_ALPHA` is set in `.env`,  
     **When** it is set to:
       - `0` or a negative value,  
         **Then** time‑aware weighting is effectively disabled.  
       - A positive float (e.g. `0.2`),  
         **Then** time‑aware weighting is applied and the effect is visible in scores/ordering for queries that hit multi‑step conversations or documents.  
   - **And** for any query, the chosen `doc_step_count`, `time_weight`, and `original_score` can be inspected from the Qdrant payloads and `SearchResult.metadata` for debugging.

### Implementation Notes

- Core logic:
  - **Domain & tag heuristics** live in `src/jarvis/memory/domain_heuristics.py` and `src/jarvis/memory/heuristics/telecom_domains.py` (for telecom/cyber focussed “chavões”).  
  - **Collection‑level catalog** and document aggregation live in `src/jarvis/memory/domain_catalog.py`:
    - `_heuristic_metadata_from_payload`  
    - `catalog_collection_domains`  
    - `catalog_documents`  
  - **Retrieval & time weighting** live in `src/jarvis/memory/search.py`:
    - `infer_query_domains` for query‑side domain inference,  
    - `_build_filter` for multi‑field domain filters,  
    - `_apply_time_weight` for score adjustment based on `doc_step_count`,  
    - `search_memory` for the main semantic retrieval pipeline.

- Environment:
  - `JARVIS_TIME_WEIGHT_ALPHA` controls how aggressively we favour later iterations.  
  - Existing search env vars (hybrid / rerank) remain unchanged and can be combined with time weighting.

- Behavioural intuition:
  - The system behaves like a human brain: it remembers early explorations and wrong turns, but leans slightly on the latest, more complete thoughts when answering.

### Testing & Validation

- **Unit tests**
  - Extend `tests/unit/memory/test_search.py`:
    - Add a test that feeds `search_memory` with two dummy points that have the same base score but different `doc_step_count`, and assert that the higher `doc_step_count` result is ranked first and metadata contains `time_weight` and `original_score`.
    - Add a test that verifies `_apply_time_weight` is a no‑op when no `doc_step_count` is present.

- **Integration tests**
  - Add or extend integration tests under `tests/integration/memory/` to:
    - Run `search_memory` / `jarvis query` against a small seeded set of conversations with multiple steps and assert that:
      - All steps are retrievable.  
      - Later steps are returned above earlier ones when scores are otherwise comparable.  
    - Exercise `jarvis analytics catalog-docs` end‑to‑end to ensure `doc_*` fields are being written and used in retrieval.

- **Manual checks**
  - Run domain and tag distribution queries (as in `docs/jarvis-knowledge-pipeline.md` and `docs/archive/firstResults.md`) to confirm that GD, cyber, BMAD, infra and science domains/tags are populated and stable.  
  - Use targeted queries like:
    - `jarvis query "GD Sines hydrogen model smart-grid"`  
    - `jarvis query "Cisco ASA IPsec config and Riemann curvature tensor"`  
    - `jarvis query "What did we build in Epic 3?"`  
    to visually inspect that retrieval is domain‑aware and time‑aware.

