# Jarvis Brain Status – 2025‑12‑02

## 1. Scope & Context

- Repository: `C:\Users\abast\Desktop\Workspace` (Jarvis personal workspace)
- Stack: Docker (`jarvis-app`, `jarvis-postgres`, `jarvis-qdrant`, `jarvis-redis`)
- Goal: Turn Jarvis into a “company brain” for rich RAG over:
  - Core GPT/Jarvis conversations and configuration
  - Local workspace docs (code, PRDs, BMAD workflows)
  - OneDrive knowledge (PDF, TXT, MD)
  - With offline catalog + enrichment via Gemini to prepare for multi‑domain, multi‑agent use.

This document summarizes what we ingested, how retrieval works, what we changed for Gemini catalog/enrichment, tests we ran, and key findings/trade‑offs.

---

## 2. Corpus & Ingestion Status

### 2.1 Qdrant `knowledge` Collection

- Backend: Qdrant collection `knowledge` (vector store)
- Size at latest run (from catalog simulation): **~43,700 points**
- Sources (domains / payload hints):
  - `jarvis-conversations` – from `docs/gptExportNEW/conversations.json`
  - `jarvis-core` – from `docs/gptExportNEW/memory.core.md` (core GPT/Jarvis configuration, history since ~2021)
  - `md` – workspace markdown, BMAD docs, sprint stories, PRDs, architecture
  - `pdf` – OneDrive and local PDFs (cyber security portfolio, GD Sines documents, etc.)
  - `txt` – text notes from OneDrive
  - `jarvis-insights` – auto‑compiled insight files from `jarvis memory compile`

### 2.2 Ingestion Paths

- **Core GPT Export**
  - `scripts/bootstrap_jarvis_memory.py --gpt-export docs/gptExportNEW/conversations.json`
  - Domain: `jarvis-conversations`

- **Core Memory File**
  - Direct call inside container:
    - `ingest_file("docs/gptExportNEW/memory.core.md", domain="jarvis-core")`
  - Result: 11 chunks / 11 points, contains core configuration and long‑term context.

- **Workspace Docs**
  - `bash scripts/ingest-all-docs.sh`
  - Targets: repo markdown, PRDs, architecture, BMAD docs, sprint stories.

- **OneDrive Mount**
  - Host: `C:\Users\abast\OneDrive` mounted read‑only into container as `/mnt/onedrive`
  - Ingestion command pattern:
    - `find /mnt/onedrive -type f \( -name '*.md' -o -name '*.markdown' -o -name '*.txt' -o -name '*.pdf' \) ! -path '*/.git/*' ! -path '*/node_modules/*' ! -path '*/.venv/*' -print0 | xargs -0 -P2 -I{} python -m jarvis.cli.main memory add "{}"`
  - PDF ingestion uses `PyPDF2` fallback. Some PDFs are imperfectly extracted (expected).

### 2.3 Ingestion Code & Tests

- Code: `src/jarvis/memory/ingest.py`
- Features:
  - Supports `.md/.markdown`, `.txt`, `.pdf`
  - Splits content into chunks with metadata: `text`, `source_file`, `section`, `domain`, `ingested_at`, `hash`
  - Upserts into Qdrant with `DEFAULT_COLLECTION_NAME="knowledge"`
- Tests:
  - `tests/unit/memory/test_ingest.py` – sanity over file types and payload structure.

---

## 3. Retrieval & Query Engine

### 3.1 Search Engine

- Code: `src/jarvis/memory/search.py`
- Capabilities:
  - `search_memory` – semantic search via Qdrant embeddings.
  - `keyword_search` – Postgres FTS over text payload.
  - `hybrid_search` – fuses semantic + keyword with configurable weight.
  - `expanded_search` – query expansion + multi‑variant search + reciprocal rank fusion (RRF).
  - Optional cross‑encoder rerank (`CrossEncoder("cross-encoder/ms-marco-MiniLM-L-12-v2")`) controlled by env `JARVIS_RERANK_ENABLED`.

### 3.2 Query CLI

- Code: `src/jarvis/cli/query.py`
- Entry point: `python -m jarvis.cli.main query ...`
- Key flags:
  - `--retriever` (`semantic`, `keyword`, `hybrid`)
  - `--weight` (hybrid weighting)
  - `--expand` (query expansion count, uses `query_expander.py`)
  - `--k` (top‑k)
  - `--json-output` (machine‑readable response envelope)
  - `--strict-mode` (hallucination‑resistant mode)
- Behaviour:
  - Uses the RAG loop: retrieve → build prompt from chunks → call LLM → return answer + citations.
  - Strict mode system prompt:
    - Answers **only** from retrieved context.
    - Prefers **user‑defined models/architectures** (e.g., GD Sines) over generic internet projects.
    - If context is insufficient, explicitly says it cannot answer instead of inventing project history.

### 3.3 Observed Behaviour

- GD Sines Hydrogen Model:
  - With `--expand` and `hybrid` retriever, answers now favor the GD model built in this workspace (including smart‑grid details and capacity) rather than external hydrogen projects, while still being allowed to mention real‑world analogues if explicitly prompted.

- “What did we build in Epic 3?”:
  - When documentation doesn’t yet describe Epic 3 deliverables, Jarvis correctly responds that it cannot answer from current sources (no hallucinated stories/retrospective).

---

## 4. LLM Providers & Gemini Integration

### 4.1 Provider Routing

- Code: `src/jarvis/llm/client.py`, `src/jarvis/llm/providers.py`
- Default `provider="auto"` routing:
  1. OpenRouter (free / trial)
  2. Perplexity (`sonar`)
  3. Local CLI tools (Claude, Codex, Gemini) if present
  4. Direct APIs: GoogleAI, Anthropic, OpenAI as last resort
- Logging:
  - All calls recorded in `LLMUsageLog` with provider, model, tokens, and cost.

### 4.2 GoogleAIProvider (Gemini)

- Code: `GoogleAIProvider` in `src/jarvis/llm/providers.py`
- Uses `google.generativeai` with models like `gemini-2.0-flash-exp:free` (via OpenRouter) and `gemini-2.5-pro` (direct Google AI Studio).
- Edge case handled:
  - Gemini often returns `finish_reason=MAX_TOKENS` with **no `Part` content**.
  - We now wrap `response.text` in `try/except` and, on `ValueError`:
    - Log `google_ai_empty_text` with error and model.
    - Attempt to aggregate `candidate.content.parts[*].text` if present.
    - Fall back to empty string and log `domain_classification_parse_failed` if content is truly empty.

---

## 5. Domain Catalog & Enrichment with Gemini

### 5.1 Domain Catalog Job

- Code: `src/jarvis/memory/domain_catalog.py`
- CLI: `python -m jarvis.cli.analytics catalog-domains ...`
- Script: `scripts/run_gemini_catalog_enrichment.sh` (Step 1)
- Purpose:
  - Iterate Qdrant `knowledge` collection.
  - For each chunk, classify into:
    - `primary_domain`
    - `secondary_domains`
    - `rick_personas` (ownership personas, e.g., Architect/Dev/Ops/PM “Ricks”)
    - `tags`
    - `domain_confidence`
  - Persist new `KnowledgeDomain` records in Postgres.
  - Update Qdrant payload with domain metadata.

### 5.2 Windowing & Aggregation (Key Change)

- Previous behaviour:
  - Single prompt with ~4k chars of text → high risk of `MAX_TOKENS` and empty responses, especially for dense PDFs.
- Current behaviour (`_default_classifier` + `_classify_window`):
  - Environment‑controlled windowing:
    - `JARVIS_CATALOG_WINDOW_CHARS` (default `1500`, last runs at `1200`)
    - `JARVIS_CATALOG_MAX_WINDOWS` (default `3`, last runs at `2`)
  - For each long chunk:
    - Truncate text to `window_chars * max_windows`.
    - Split into windows of `window_chars` each.
    - Call Gemini once per window via `_classify_window`.
    - Aggregate:
      - `primary_domain`: majority vote over non‑`generic.unknown` domains, fallback to first.
      - `secondary_domains`, `rick_personas`, `tags`: union sets with caps (5/5/10).
      - `confidence`: average of window confidences.
  - Logging:
    - Each window logs `domain_classification_call` with `provider`, `model`, `text_chars`, `text_preview` (first 160 chars) for transparency.

### 5.3 Gemini Catalog & Enrichment Script

- File: `scripts/run_gemini_catalog_enrichment.sh`
- Intended invocation (inside `jarvis-app`):
  - `bash scripts/run_gemini_catalog_enrichment.sh`
  - With overrides such as:
    - `JARVIS_ENRICH_PROVIDER=google-ai`
    - `JARVIS_ENRICH_MODEL=gemini-2.5-pro`
    - `JARVIS_CATALOG_WINDOW_CHARS=1200`
    - `JARVIS_CATALOG_MAX_WINDOWS=2`
    - `JARVIS_USAGE_PROVIDER=google-ai`
- Behaviour:
  1. **Simulation:**
     - Reads Qdrant `knowledge` collection info and optional limits (`JARVIS_CATALOG_LIMIT`, `JARVIS_ENRICH_LIMIT`).
     - Estimates total tokens and cost from:
       - `JARVIS_SIM_TOKENS_PER_CHUNK` (default `600`)
       - `JARVIS_SIM_COST_PER_1K_TOKENS_USD` (default `0.0005`)
     - Prints historical LLM usage from Postgres for `JARVIS_USAGE_PROVIDER`.
  2. **Step 1 – Catalog Domains:**
     - `python -m jarvis.cli.analytics catalog-domains ...`
     - Logs `domain_classification_call` and Gemini usage.
     - Any empty/failed responses become `generic.unknown` with warnings, not crashes.
  3. **Step 2 – Enrich Chunks:**
     - `python -m jarvis.cli.analytics enrich-chunks ...`
     - Generates `summary`, `facts`, `tags`, `doc_type` per chunk within selected domains.
  4. **Afterwards:**
     - Prints updated LLM usage for cost tracking.

### 5.4 Observed Job Characteristics

- Collection size (latest run): `total_points=43715`, `catalog_points=43715`, `enrich_points=43715`.
- Simulation: ~52.5M tokens, ~\$26.23 for combined catalog + enrichment at 0.0005\$/1k tokens.
- Actual calls:
  - Many windows succeed; some yield `MAX_TOKENS` with empty content → logged as warnings and mapped to `generic.unknown`.
  - Cost per failed call is minimal (hundreds of tokens).

### 5.5 Heuristic Domain Inference & Document Profiles

To avoid over‑relying on Gemini and to keep costs low, we layered a **deterministic heuristic classifier** in front of the LLM, plus a **document‑level profiler** that propagates context down to chunks.

#### 5.5.1 Chunk‑Level Heuristics (`_heuristic_metadata_from_payload`)

File: `src/jarvis/memory/domain_catalog.py`

Inputs per chunk:

- `payload["domain"]` (original ingestion domain, e.g., `jarvis-conversations`, `jarvis-core`, `pdf`, `md`, `txt`)
- `payload["source_file"]`, `payload["section"]`, `payload["title"]`, `payload["chunk_index"]`
- `combined` text: first ~2 000 characters of the chunk

Heuristic order:

1. **Direct domain mapping**
   - `jarvis-core`     → `primary_domain = "jarvis.core"`
   - `jarvis-conversations` → `primary_domain = "conversations.jarvis"`
   - `jarvis-insights` → `primary_domain = "jarvis.insights"`

2. **Path‑based hints**
   - `docs/jarvis/**`              → `jarvis.core`, `jarvis.playbooks`
   - `docs/sprints/**`             → `project.sprints`
   - `.bmad/**`                    → `bmad.method` / `bmad.core`
   - `docs/gptExportNEW/**`        → `jarvis.gpt_export`
   - `CyberSecurityPortfolio/**`   → `cyber.security`
   - `GenerativeDrive` / `GDFullDocument*.pdf` / `GenerativeDrive.pdf` → `gd.generative_drive`
   - File‑type hint kept as `doc_type_hint` (`docs.pdf`, `docs.markdown`, `docs.text`) for fallback.

3. **Title / section hints**
   - `epic`, `story`, `sprint-status` → reinforce `project.sprints`
   - `architecture`, `operating-manual` → `architecture.core`
   - `prd` / `product requirements` → `product.prd`

4. **GD / Sines hydrogen special block**
   - If `combined` mentions **Generative Drive**, **GD** + energy wording, or Sines hydrogen terms (PT/EN):
     - Set `primary_domain = "gd.generative_drive"` (or reinforce it if already chosen).
     - Add tags such as:
       - `generative_drive`, `sines`, `hydrogen`, `hydrogen_green`
       - `solar`, `wind`, `hydro`, `smart_grid`
       - `energy_model`, `energy_efficiency`, `energy_storage`
       - `water`, `water_loops`, `water_loop`
       - `ai`, `plastics`, `Portugal`, `infrastructure`, `scalability`

5. **“Chavões” keyword‑to‑domain map (only if still no primary)**

   If no strong signal yet, we scan for domain “chavões” (buzzwords) in PT/EN and map them to domains; examples:

   - Security / infra / dev:
     - `firewall`, `cisco asa`, `vpn`, `malware`, `mitre att&ck` → `cyber.security`, `network.cisco_asa`, `network.vpn`
     - `docker`, `compose` → `infra.docker`
     - `qdrant` → `infra.qdrant`
     - `postgres`, `sql`, `alembic` → `infra.postgres`
     - `spring boot` → `dev.spring_boot`
   - Energy:
     - `hydrogen`, `H2`, `fuel cell` → `energy.hydrogen`
     - `solar`, `photovoltaic`, `painéis solares` → `energy.solar`
     - `wind`, `eólico` → `energy.wind`
     - `hydro`, `dam`, `barragem`, `hydropower` → `energy.hydro`
     - `smart grid`, `rede inteligente` → `energy.smart_grid`
   - Math / science:
     - `Riemann`, `tensor`, `curvature` → `math.riemann_geometry` / `science.physics`
     - `integral`, `derivative`, `cálculo` → `math.calculus`
     - Physics/biology/chemistry keywords → `science.physics`, `science.biology`, `science.chemistry`, `science.neurology`
   - Other:
     - `rocket`, `orbit`, `trajectory` → `engineering.rocketry`
     - `zodiac`, `astrology` → `culture.astrology`

   These create topics like `cyber.security`, `energy.*`, `math.*`, `science.*` without any LLM call when the text is clear enough.

6. **Doc‑type fallback**
   - If still no domain after all signals and we have a `doc_type_hint`, use that:
     - `docs.pdf` / `docs.markdown` / `docs.text`

7. **Header tagging**
   - `chunk_index` 0 or 1 gets a `doc_header` tag to help future heuristics treat it as a document header.

The heuristic returns `ChunkDomainMetadata` with:

- `primary_domain` (never empty after the full pipeline)
- `secondary_domains` (we can layer in e.g. `energy.*` as secondary for GD chunks)
- `tags` (the tag universe described above)
- `confidence` (default `0.5` for heuristic‑only outcomes)

This is applied **before** the Gemini classifier; if heuristics find a strong primary, we skip the LLM entirely for that chunk.

#### 5.5.2 Document‑Level Profiles (`catalog-docs`)

File: `src/jarvis/cli/analytics.py` (`catalog-docs` command) + `catalog_documents` in `domain_catalog.py`.

Goal: stabilize domains/tags at the **document** level and propagate them to all chunks.

Steps:

1. Group points by “document key”:
   - Files: `doc_key = "file::<source_file>"`
   - Conversations: `doc_key = "conv::<conversation_id>"`

2. For each document:
   - Count `primary_domain` occurrences from all its chunks.
   - Pick `doc_primary_domain` via majority vote:
     - Prefer non‑`docs.*` domains (e.g., `gd.generative_drive`, `cyber.security`, `project.sprints`).
   - Aggregate tags from all chunks into `doc_tags` (deduplicated, capped).

3. Write back into **every chunk** in that document:
   - `doc_key`
   - `doc_primary_domain`
   - `doc_tags`
   - If a chunk’s `primary_domain` is empty or `generic.unknown`, inherit `doc_primary_domain`.
   - Ensure the chunk’s `primary_domain` is present in its `domains` list, and merge `doc_tags` into chunk‑level `tags`.

This is what produced the current document‑level stats (example run, after heuristics + doc catalog):

```text
PRIMARY_DOMAIN set: 43715
PRIMARY_DOMAIN missing: 0
Top domains:
  conversations.jarvis : 20826
  cyber.security       : 10962
  gd.generative_drive  : 3927
  docs.pdf             : 2764
  bmad.method          : 2714
  docs.markdown        : 1399
  project.sprints      : 295
  docs.text            : 233
  architecture.core    : 151
  product.prd          : 111
  jarvis.core          : 88
  bmad.core            : 46
  infra.docker/postgres/qdrant : ~40 each
```

And for GD chunks specifically, we see rich energy tags (example tag histogram for `primary_domain = "gd.generative_drive"`):

```text
generative_drive      3 800+
solar                 3 700+
hydrogen              3 700+
hydro                 3 600+
sines                 3 500+
wind                  3 500+
energy_model          2 800+
smart_grid            1 300+
ai                    1 100+
water                 ~900
hydrogen_green        ~500
plastics              ~200
water_loops           ~90
renewable_energy      ~30
math_calculus         ~30
energy_efficiency     ~10
energy_storage        ~10
...
```

#### 5.5.3 How to Inspect Domains/Tags Quickly

Inside `jarvis-app`:

```bash
cd /workspace
export PYTHONPATH=/workspace/src

# Top primary domains
python -m jarvis.cli.main analytics catalog-domains --collection knowledge --dry-run

# Sample tags for a specific domain (e.g., gd.generative_drive)
python - << 'PY'
from collections import Counter
from jarvis.database.qdrant import get_qdrant_client

client = get_qdrant_client()
cursor = None
tags = Counter()

while True:
    points, cursor = client.scroll(
        collection_name="knowledge",
        limit=512,
        with_payload=True,
        with_vectors=False,
        offset=cursor,
    )
    if not points:
        break
    for p in points:
        payload = p.payload or {}
        if payload.get("primary_domain") == "gd.generative_drive":
            for t in payload.get("tags") or []:
                tags[t] += 1
    if cursor is None:
        break

for tag, count in tags.most_common(30):
    print(f"{tag:24} {count}")
PY
```

These tools give us a reproducible, inspectable view of how the enrichment and catalog heuristics are shaping the “Jarvis brain” without having to re‑read the entire source code.

---

## 6. Tests & Validation Runs

Key tests we ran during this work (inside `jarvis-app` container):

- Unit tests:
  - `poetry run pytest tests/unit/memory/test_ingest.py -q`
  - `poetry run pytest tests/unit/memory/test_search.py tests/unit/cli/test_query.py -q`

- Integration tests (memory/query):
  - `poetry run pytest tests/integration/memory/test_hybrid_retrieval_integration.py -m integration -q`
  - `poetry run pytest tests/integration/memory/test_expanded_search_integration.py -m "integration" -q`
  - `poetry run pytest tests/integration/cli/test_query_integration.py -m integration -q`

- Integration tests (MCP provenance / conversations):
  - `poetry run pytest tests/integration/api/test_mcp_provenance_integration.py -m integration -q`
    - Ensured 503 conversation API issues were fixed rather than masked by tests.

We observed and fixed:

- Expanded search sometimes failed due to PyTorch “meta tensor” issues in SentenceTransformers on Python 3.13; we now catch `NotImplementedError` and treat that variant as an empty result instead of failing the whole search.
- CLI JSON output integration tests exposed logging noise in stdout; we adjusted `jarvis cli query` to produce clean JSON when `--json-output` is set, keeping logs separate.

---

## 7. Trade‑offs, Findings, and Next Steps

### 7.1 Trade‑offs

- **Latency & Cost vs. Robustness:**
  - Windowing (1200 chars, 2 windows) increases LLM calls per long chunk, but substantially reduces catastrophic failures and makes cataloging long PDFs/documents possible.
  - Cross‑encoder rerank and expanded search improve retrieval quality at the cost of multi‑second query latency. For an internal brain/prototype, this is acceptable.

- **Precision vs. Simplicity:**
  - Chunking is primarily length‑based, not structurally aware (e.g., per heading/section). This is “good enough” for now but leaves some recall/precision on the table for complex PDFs or tables.

- **External Dependencies:**
  - We rely on OpenRouter, Perplexity, and GoogleAI behaviours and quotas; quirks like Gemini’s `MAX_TOKENS` + empty `Part` responses surface as warnings.
  - Logging and simulation mitigate risk by keeping cost visible and bounded.

### 7.2 Key Findings

- Jarvis can now answer deeply contextual questions over mixed sources (GD Sines, cyber portfolio, BMAD workflows, personal history) with grounded citations.
- Strict mode plus tailored system prompts prevent hallucinations around project status and epic/story completion.
- Gemini is effective as an offline classifier/enricher when driven with careful windowing and JSON‑only instructions, but it will still produce empty outputs when pushed near token limits.
- Our usage so far is well under budget; even the full catalog + enrichment run sits comfortably within a small portion of the available Gemini credits.

### 7.3 Next Steps (Candidate Epics/Stories)

- **Doc‑level Profiles & Contextual Bias:**
  - Compute a “document profile” (primary_domain, tags, doc_type) once per `source_file` / `conversation_id` and feed that into window‑level prompts as `Document context` to stabilize classification of small fragments.

- **Operator UX & Analytics:**
  - Add commands/scripts to summarize domain distributions, tags, and persona coverage.
  - Expose health/status for catalog/enrichment jobs and last‑run metadata.

- **Local Model Track:**
  - Introduce small local models (retrieval + rerank) behind the same APIs to gradually reduce dependence on external providers while leveraging our now “massaged” data.

- **Copilot / IDE Integration:**
  - Use MCP to make Jarvis the context builder for GitHub Copilot and other agents (Copilot → Jarvis → Copilot LLM → user), starting with read‑only flows.

Jarvis is now operating as a fully functional, multi‑domain RAG brain with a rich historical and personal corpus, plus offline catalog/enrichment jobs that make the knowledge graph more navigable for both humans and LLMs. This report marks the first major “whole‑brain” pass over that corpus using Gemini. 
