# Jarvis Knowledge Pipeline & Domain Catalog – Reference

This document describes the stable, reusable pieces of Jarvis’ knowledge pipeline: ingestion, vector storage, domain catalog, document profiles, and enrichment. It is meant as a **reference** for future development and for porting this design into other environments.

---

## 1. High‑Level Flow

End‑to‑end, the Jarvis “brain” is built in four stages:

1. **Ingestion → Qdrant**
   - Parse files and conversations into text chunks.
   - Store in Qdrant `knowledge` collection with rich payload (text + metadata).
2. **Chunk‑level domain catalog**
   - Assign `primary_domain`, `tags`, and (optionally) `secondary_domains` to each chunk via heuristics + Gemini.
   - Persist domain metadata back into Qdrant and into Postgres.
3. **Document‑level profiles**
   - Group chunks by document (`source_file` / `conversation_id`).
   - Derive a `doc_primary_domain` and `doc_tags`.
   - Propagate these doc‑level fields down to all chunks.
4. **Chunk enrichment**
   - Use Gemini to generate summaries and “facts” per chunk.
   - Enrich Qdrant payload with higher‑level views for downstream RAG queries.

All of this happens **offline**; query‑time retrieval only reads the enriched payloads and doesn’t call Gemini directly.

---

## 2. Ingestion → Qdrant

### 2.1 Components

- Code: `src/jarvis/memory/ingest.py`
- Default collection: `knowledge` in Qdrant.
- CLI:
  - `python -m jarvis.cli.main memory add PATH`
  - `bash scripts/ingest-all-docs.sh`

### 2.2 Supported Inputs

- Markdown: `.md`, `.markdown`
- Plain text: `.txt`
- PDF: `.pdf` (via PyPDF‑style extraction)
- GPT exports:
  - `docs/gptExportNEW/conversations.json` → ingested via `scripts/bootstrap_jarvis_memory.py`
  - `docs/gptExportNEW/memory.core.md` → ingested as a core memory file

### 2.3 Chunk Payload Schema (Qdrant)

Each Qdrant point in `knowledge` has:

- `text`: normalized chunk text
- `source_file`: path for file‑based sources (if any)
- `section`: section label (e.g. file name, PDF page, heading)
- `domain`: original ingestion domain (`jarvis-conversations`, `jarvis-core`, `md`, `pdf`, `txt`, etc.)
- `ingested_at`: ISO timestamp of ingestion
- `hash`: content hash for idempotency
- Optional derived fields added later:
  - `primary_domain`, `secondary_domains`, `tags`, `domain_confidence`
  - `doc_key`, `doc_primary_domain`, `doc_tags`
  - `summary`, `facts`, `doc_type`

---

## 3. Chunk‑Level Domain Catalog

### 3.1 Entry Points

- Code: `src/jarvis/memory/domain_catalog.py`
- CLI: `python -m jarvis.cli.main analytics catalog-domains [...]`
- Script: `scripts/run_gemini_catalog_enrichment.sh` (Step 1)

### 3.2 Heuristic Classifier (Fast Path)

Function: `_heuristic_metadata_from_payload(payload: dict, text: str) -> ChunkDomainMetadata | None`

Inputs:

- `payload["domain"]` (ingestion domain)
- `payload["source_file"]`, `payload["section"]`, `payload["title"]`, `payload["chunk_index"]`
- `combined` text: prefix of the chunk (first ~2 000 characters)

Responsibility:

- Try to assign:
  - `primary_domain` – stable key like `conversations.jarvis`, `gd.generative_drive`, `cyber.security`, `project.sprints`, `docs.pdf`, etc.
  - `tags` – short strings for filtering (`generative_drive`, `hydrogen`, `sines`, `smart_grid`, `spring_boot`, etc.).
  - Optionally `secondary_domains` (e.g. `energy.hydrogen` in addition to `gd.generative_drive`).

Ordering (simplified):

1. **Direct mapping from ingestion domain:**
   - `jarvis-core` → `jarvis.core`
   - `jarvis-conversations` → `conversations.jarvis`
   - `jarvis-insights` → `jarvis.insights`

2. **Path‑based hints:**
   - `docs/jarvis/**` → `jarvis.core`, `jarvis.playbooks`
   - `docs/sprints/**` → `project.sprints`
   - `.bmad/**` → `bmad.method` / `bmad.core`
   - `docs/gptExportNEW/**` → `jarvis.gpt_export`
   - `CyberSecurityPortfolio/**` → `cyber.security`
   - `GenerativeDrive` / `GDFullDocument*.pdf` → `gd.generative_drive`

3. **Title/section hints:**
   - `epic`, `story`, `sprint-status` → `project.sprints`
   - `architecture`, `operating-manual` → `architecture.core`
   - `prd` / `product requirements` → `product.prd`

4. **Generative Drive / Sines block:**
   - If text matches Generative Drive or the Sines hydrogen model (PT/EN vocab):
     - Set or reinforce `primary_domain = "gd.generative_drive"`.
     - Add tags such as:
       - `generative_drive`, `sines`, `hydrogen`, `hydrogen_green`
       - `solar`, `wind`, `hydro`, `smart_grid`, `energy_model`
       - `energy_efficiency`, `energy_storage`
       - `water`, `water_loops`, `plastics`, `Portugal`, `ai`

5. **Keyword (“chavões”) map:**
   - If no strong domain yet, scan text for PT/EN keywords and map to domains:
     - Security / infra / dev:
       - VPN, Cisco ASA, malware, MITRE ATT&CK → `cyber.security`, `network.cisco_asa`, `network.vpn`
       - Docker, Qdrant, Postgres → `infra.docker`, `infra.qdrant`, `infra.postgres`
       - Spring Boot → `dev.spring_boot`
     - Energy:
       - hydrogen / H2 / fuel cells → `energy.hydrogen`
       - solar / photovoltaic / “painéis solares” → `energy.solar`
       - wind / eolic / “eólico” → `energy.wind`
       - hydro / dam / “barragem” → `energy.hydro`
       - “smart grid” / “rede inteligente” → `energy.smart_grid`
     - Math / science (examples):
       - Riemann / curvature / tensor → `math.calculus` / `science.physics`
       - Generic calculus terms → `math.calculus`
       - Physics/biology/chemistry vocab → appropriate `science.*` domains.

6. **Doc‑type fallback:**
   - If still no domain, fall back to `docs.pdf` / `docs.markdown` / `docs.text`.

7. **Header tagging:**
   - `chunk_index` 0/1 get a `doc_header` tag.

If heuristic classification succeeds, the Gemini classifier is **not** called for that chunk, which keeps the catalog job cheap.

### 3.3 LLM Classifier (Gemini Fallback)

Function: `_default_classifier(text: str, provider: str, model: str) -> ChunkDomainMetadata`

Behaviour:

- Normalize whitespace and limit text length according to env:
  - `JARVIS_CATALOG_WINDOW_CHARS` (default ~1 500)
  - `JARVIS_CATALOG_MAX_WINDOWS` (default ~3)
- Split text into windows.
- For each window:
  - Call Gemini through `call_llm` with a **JSON‑only** system prompt:
    - Ask for: `primary_domain`, `secondary_domains`, `rick_personas`, `tags`, `confidence`.
  - Parse JSON; if parsing fails or Gemini returns no content (MAX_TOKENS case), treat window as `generic.unknown` with empty tags.
- Aggregate across windows:
  - Use majority vote for `primary_domain` (ignoring `generic.unknown` where possible).
  - Union tag sets with caps.
  - Average confidence scores.

Logging:

- For each window we log:
  - `domain_classification_call` (provider, model, text_chars, prefix preview).
- If `response.text` is empty and `finish_reason=MAX_TOKENS`:
  - Log `google_ai_empty_text` and `domain_classification_parse_failed`, but keep the job running.

---

## 4. Document‑Level Profiles

### 4.1 Purpose

Many chunks are too small or too generic to classify accurately in isolation. We therefore derive **document‑level profiles** and propagate them:

- `doc_key` – canonical id per document:
  - Files: `file::<source_file>`
  - Conversations: `conv::<conversation_id>`
- `doc_primary_domain` – majority domain for the whole document.
- `doc_tags` – union of top tags across all chunks in the document.

### 4.2 Command & Implementation

- CLI: `python -m jarvis.cli.main analytics catalog-docs --collection knowledge --batch-size 512`
- Code: `catalog_documents` in `src/jarvis/memory/domain_catalog.py`

Steps:

1. Scroll Qdrant `knowledge` collection, group points by `doc_key`.
2. For each group:
   - Count `primary_domain` occurrences; pick the most frequent non‑`docs.*` domain where possible.
   - Collect tags from each chunk; deduplicate and cap to a reasonable number.
3. Update each point in the group:
   - Set `doc_key`, `doc_primary_domain`, `doc_tags`.
   - If `primary_domain` is missing or `generic.unknown`, inherit `doc_primary_domain`.
   - Ensure `primary_domain` is included in `domains` and merge `doc_tags` into chunk `tags`.

After a successful `catalog-docs` run, nothing in the collection should have an empty `primary_domain`, and every chunk knows the “document topic” it belongs to.

---

## 5. Grounded Query Modes (CLI + API)

Jarvis responses can blend creativity with citations by choosing a **grounding level**. This is available in both the CLI (`jarvis query`) and the `/api/chat` endpoint.

- **soft** – You may add speculative glue (explicitly labeled) while citing real facts from retrieved sources. Never fabricate citations.
- **balanced** *(default)* – Every major factual claim must cite a retrieved source. If a fact is missing, say it is not in memory. Brief speculative glue is allowed but must be labeled as such.
- **strict** – No invention. Do not create new facts, metrics, people, or timelines. If context is insufficient, say so and optionally list the most relevant snippets instead of speculating.

Usage:
- CLI: `jarvis query "..." --grounding-level soft|balanced|strict` (and `--strict-mode` as a hard override to strict).
- API: set `grounding_level` in the request body (`soft|balanced|strict`). The legacy `strict_mode` flag still forces strict.

---

## 5. Enrichment (Summaries & Facts)

### 5.1 Entry Points

- Code: `src/jarvis/memory/enrich.py`
- CLI: `python -m jarvis.cli.main analytics enrich-chunks [...]`
- Script: `scripts/run_gemini_catalog_enrichment.sh` (Step 2)

### 5.2 Enricher Behaviour

Function: `_default_enricher(text: str, payload: dict, provider: str, model: str) -> ChunkEnrichment`

Inputs:

- Chunk text.
- Enriched payload fields:
  - `primary_domain`, `secondary_domains`, `tags`
  - `doc_primary_domain`, `doc_tags`
  - `source_file`, `section`

Prompt structure:

- Build a `Metadata` block that describes:
  - Document primary domain and tags.
  - Chunk primary domain and domains list.
  - Source file / section (if any).
- Append the raw chunk text.
- Ask Gemini to return a compact JSON with:
  - `summary` – 1–3 sentence, chunk‑level summary.
  - `facts` – list of short, atomic bullet‑like facts (optional).

Output:

- Enrichment result is written back into the Qdrant payload:
  - `summary`: short description of the chunk.
  - `facts`: list of strings (may be empty).

We typically restrict enrichment to specific domains (via env such as `JARVIS_ENRICH_DOMAINS`) to focus on high‑value content (e.g. Jarvis core, GD, sprints, BMAD docs) and keep cost bounded.

---

## 6. Operational Commands (Inside `jarvis-app`)

### 6.1 Ingestion

```bash
cd /workspace
export PYTHONPATH=/workspace/src

# Core GPT export
python scripts/bootstrap_jarvis_memory.py --gpt-export "docs/gptExportNEW/conversations.json"

# Core memory file
python - << 'PY'
from pathlib import Path
from jarvis.memory.ingest import ingest_file
ingest_file(Path("docs/gptExportNEW/memory.core.md"), domain="jarvis-core")
PY

# Workspace docs
bash scripts/ingest-all-docs.sh

# OneDrive (read‑only mount)
find /mnt/onedrive -type f \( \
  -name '*.md' -o -name '*.markdown' -o -name '*.txt' -o -name '*.pdf' \
\) ! -path '*/.git/*' ! -path '*/node_modules/*' ! -path '*/.venv/*' -print0 |
xargs -0 -P2 -I{} python -m jarvis.cli.main memory add "{}"
```

### 6.2 Domain Catalog

```bash
cd /workspace
export PYTHONPATH=/workspace/src \
       JARVIS_CATALOG_WINDOW_CHARS=1500 \
       JARVIS_CATALOG_MAX_WINDOWS=3

python -m jarvis.cli.main analytics catalog-domains \
  --collection knowledge \
  --batch-size 64

python -m jarvis.cli.main analytics catalog-docs \
  --collection knowledge \
  --batch-size 512
```

### 6.3 Enrichment

Example: Gemini 2.5 Pro enrichment for selected domains:

```bash
cd /workspace
export PYTHONPATH=/workspace/src \
       JARVIS_ENRICH_PROVIDER=google-ai \
       JARVIS_ENRICH_MODEL=gemini-2.5-pro \
       JARVIS_ENRICH_DOMAINS="gd.generative_drive,jarvis.core,project.sprints,bmad.method" \
       JARVIS_USAGE_PROVIDER=google-ai

python -m jarvis.cli.main analytics enrich-chunks \
  --collection knowledge \
  --batch-size 16
```

Or run the full catalog + enrichment workflow:

```bash
cd /workspace
export PYTHONPATH=/workspace/src \
       JARVIS_ENRICH_PROVIDER=google-ai \
       JARVIS_ENRICH_MODEL=gemini-2.5-pro \
       JARVIS_USAGE_PROVIDER=google-ai

bash scripts/run_gemini_catalog_enrichment.sh
```

---

## 7. How to Extend This Design

- **Add new domains**  
  Extend the heuristic keyword maps in `domain_catalog.py` (preferably in a centralized map) and re‑run `catalog-domains` + `catalog-docs`. Consider moving these maps to a YAML config for non‑code tuning.

- **Add document‑level analytics**  
  Introduce a `KnowledgeDocument` table in Postgres keyed by `doc_key` to store `primary_domain`, `tags`, size metrics, and language; use it for reporting and API filters.

- **Tune for other LLMs**  
  Swap Gemini for another provider in `call_llm` by adjusting the `provider`/`model` for classification and enrichment, respecting each model’s token limits and JSON‑only behaviours.

This pipeline is intentionally modular: ingestion, domain catalog, document profiling, and enrichment can be reused as building blocks in corporate “brain” projects beyond Jarvis itself.
