# Jarvis Dataset Rules

**Version:** 1.0  
**Scope:** Workspace `docs/*` ingestion into Postgres + Qdrant  
**Goal:** Keep Jarvis’s *brain* (system docs) and *corpus* (knowledge docs) cleanly separated, typed, and queryable.

---

## 1. Objectives

1. Make ingestion deterministic and reproducible.
2. Separate **system-level cognition** from normal knowledge:
   - `is_system = true` → core Jarvis brain (how it thinks, memory architecture, operating manual).
   - `is_system = false` → everything else (content Jarvis reasons *about*).
3. Encode **versioning**, **recency**, and **importance** in payload/meta:
   - `is_latest`, `version`, `priority`, `jarvis_core`, `semantic_family`.
4. Use **domains** and **tags** as stable axes for:
   - Retrieval filtering.
   - UI domain/tag selectors.
   - Gap detection and autonomous research later.

---

## 2. Canonical Payload Schema

### 2.1 Qdrant Payload (per chunk)

Every chunk stored in Qdrant must *at minimum* include:

```jsonc
{
  "doc_key": "string",          // stable identifier for the document
  "domain": "string",           // see domain taxonomy
  "tags": ["string", "..."],    // normalised tags
  "is_latest": true,            // versioning / lineage
  "version": 1,                 // integer version (monotonic per doc_key)
  "is_system": false,           // system plane vs corpus plane
  "jarvis_core": false,         // is this core to Jarvis identity/operation?
  "priority": 0.0,              // 0.0–1.0: retrieval importance
  "semantic_family": "string"   // cluster: "core-memory", "playbook", "session-log", etc.
}
````

Additional fields (optional but recommended):

* `session_date` for session logs.
* `stale_factor` for archived material.
* Any domain-specific metadata (e.g. `epic_id`, `story_id`).

### 2.2 Postgres `documents` Table

Minimum required fields for ingestion:

* `doc_key : TEXT UNIQUE`
* `domain : TEXT`
* `version : INTEGER NOT NULL DEFAULT 1`
* `is_latest : BOOLEAN NOT NULL DEFAULT TRUE`
* `is_system : BOOLEAN NOT NULL DEFAULT FALSE`
* `jarvis_core : BOOLEAN NOT NULL DEFAULT FALSE`
* `priority : FLOAT DEFAULT 0.5`

The ingest pipeline is responsible for maintaining:

* `version` monotonic per `doc_key`.
* `is_latest = true` only on newest version per `doc_key`.

---

## 3. Global Ingestion Rules

1. **Chunking**

   * Markdown → semantic chunks ~500–1200 tokens.
   * Sessions may be chunked larger (up to ~1500 tokens) to keep conversational context.

2. **is_latest / version**

   * New ingest of existing `doc_key`:

     * Increment `version`.
     * Set previous `is_latest = false` in Postgres (and Qdrant payload update when practical).
   * Backfill scripts MUST ensure:

     * For each `doc_key` there is exactly one `is_latest = true` version.

3. **System vs Corpus**

   * `is_system = true` → only for **core Jarvis brain**.
   * Retrieval MUST exclude `is_system = true` by default.
   * `allow_system = true` only for:

     * Introspection / “how do you work?” questions.
     * Explicit domain filter `jarvis-core`.

4. **Priorities**

   * `priority` is a soft hint used in ranking / tie-breaking:

     * `1.0` → absolutely central.
     * `0.8–0.9` → very important.
     * `0.5–0.7` → normal.
     * `<0.3` → legacy / archive / peripheral.

---

## 4. Domain Taxonomy

### 4.1 `architecture`

**Path:** `docs/architecture/*` and `docs/architecture.md`
**Role:** High-level and detailed architecture of Jarvis and memory pipeline.

* `domain = "architecture"`
* Tags (base): `["architecture", "jarvis", "design", "memory"]`
* `semantic_family = "architecture"`
* `priority = 0.9` (architecture.md, jarvis-memory-architecture.md, jarvis-knowledge-pipeline.md)
* Examples:

  * `jarvis-memory-architecture.md` → `["memory_core", "arches"]`
  * `memory-pipeline-flow.md` → `["pipeline_flow"]`
  * `domain-taxonomy.md` → `["domain_taxonomy"]`

**Flags:**

* `is_system = false`
* `jarvis_core = false` (important but not the core memory ontology itself)

---

### 4.2 `archive`

**Path:** `docs/archive/*`
**Role:** Legacy blueprints, early plans, obsolete results.

* `domain = "archive"`
* Tags (base): `["archive", "legacy", "historical", "old_blueprint"]`
* `semantic_family = "archive"`
* `is_latest = false`
* `stale_factor = 1.0`
* `priority ≈ 0.2`

**Usage:**

* Should **not** appear in normal answers.
* Only used when:

  * `--allow-stale` or equivalent flag.
  * Explicit domain filter `archive`.

---

### 4.3 `features`

**Path:** `docs/features/*`, selected root docs (e.g. `AUTONOMOUS-RESEARCH.md`, `VARIABLE-GROUNDING-SYSTEM.md`, `research-ui-walkthrough.md`)
**Role:** Describes Jarvis feature set and UX.

* `domain = "features"`
* Tags (base): `["features", "ui", "jarvis"]`
* `semantic_family = "feature"`
* `priority ≈ 0.7–0.8`

Examples:

* `advanced-conversation-management.md` → add `["conversation_management"]`
* `conversation-pagination-search.md` → `["pagination", "search"]`
* `ui-collapsible-panels.md` → `["panels", "research_ui"]`
* `AUTONOMOUS-RESEARCH.md` → `["autonomous_research", "research"]`
* `VARIABLE-GROUNDING-SYSTEM.md` → `["variable_grounding"]`

**Flags:**

* `is_system = false`
* `jarvis_core = false`

---

### 4.4 `jarvis-core` (SYSTEM BRAIN)

**Path:** `docs/jarvis/*` **excluding** `docs/jarvis/playbooks/*`
**Role:** This is **Jarvis’s core cognitive identity and operation**.

* `domain = "jarvis-core"`
* Tags (base): `["jarvis", "core", "arches", "cognition", "memory"]`
* `semantic_family = "core-memory"`
* `priority = 1.0`
* `jarvis_core = true`
* `is_system = true`

Special cases:

* `memory.core.md` → `["memory_core", "ontology", "priority_high"]`
* `operating-manual.md` → `["operating_manual", "ops"]`
* `persona.md` → `["personas", "council"]`
* `gd-overview.md` → `["generative_drive", "gd_core"]`
* `integration-plan.md` → `["integration", "roadmap"]`
* `conversation-index.md` → `["conversation_index"]`
* `user-export-snapshot.md` → `["user_export_snapshot"]`

**Retrieval:**

* Default Qdrant filter:

  * `is_latest = true`
  * `is_system = false`  → **jarvis-core is excluded by default**
* To include `jarvis-core`:

  * Set `allow_system = true` in `_build_qdrant_filter`.
  * Or explicitly filter `domain = "jarvis-core"` via UI/domain filter.
* Only used for:

  * Introspection queries (“how do you work?”, “explain your memory pipeline”).
  * System debugging.

---

### 4.5 `jarvis-playbooks`

**Path:** `docs/jarvis/playbooks/*`
**Role:** Applied playbooks for concrete scenarios (energy, infra, meetings, etc.).

* `domain = "jarvis-playbooks"`
* Tags (base): `["jarvis", "playbook"]`
* `semantic_family = "playbook"`
* `priority ≈ 0.8`
* `jarvis_core = false`
* `is_system = false`

Examples:

* `architect-meeting-prep.md` → `["meetings", "architecture"]`
* `gd-energy-partnerships.md` → `["generative_drive", "energy", "partnership"]`
* `gd-hydrogen-and-water-loop.md` → `["hydrogen", "water_loop", "gd_energy"]`
* `gd-telemetry-and-infra.md` → `["telemetry", "infrastructure", "netops"]`

These may appear in normal answers when relevant.

---

### 4.6 `sessions`

**Path:** `docs/sessions/*`
**Role:** High-value session logs (breakthroughs, design decisions, council outcomes).

* `domain = "sessions"`
* Tags (base): `["session_log", "temporal", "jarvis_session"]`
* `semantic_family = "session-log"`
* `priority ≈ 0.4–0.6` depending on importance
* `is_system = false`
* `jarvis_core = false`

Filename-driven metadata:

* Parse leading `YYYY-MM-DD-*` → `session_date = ISO8601`.
* Add tags from name:

  * `BREAKTHROUGH-SESSION` → `["breakthrough"]`
  * `COUNCIL-AND-DOC-VIEWER` → `["council", "doc_viewer"]`
  * `DOMAIN-FILTERING` → `["domain_filtering"]`

---

### 4.7 `story` (BMAD Stories & Context)

**Path:** `docs/sprints/stories/*`
**Role:** Implementation stories and context for BMAD epics.

* `domain = "story"`
* Tags (base): `["story", "bmad"]`
* `semantic_family = "story"`
* `priority ≈ 0.6` (Markdown bodies), `~0.4` (context XML)

Extra tags:

* From filename prefix:

  * `1-*` → `["epic_1"]`
  * `2-*` → `["epic_2"]`
  * `4-5-*` → `["epic_4_5", "arches"]`
* `*.context.xml` → add `["story_context", "xml"]`

**Flags:**

* `is_system = false`
* `jarvis_core = false`

---

### 4.8 `epic` / `process`

**Path:** `docs/sprints/epic-*.md`, `sprint-status.yaml`, `sprint-template.md`, retrospectives, etc.

* Epic docs:

  * `domain = "epic"`
  * Tags (base): `["epic", "bmad"]`
  * If filename contains `retro` → add `["retrospective"]`
  * If contains `arches-stabilization` → add `["arches"]`
  * `priority ≈ 0.7`
* Process docs (`sprint-status.yaml`, template, etc.):

  * `domain = "process"`
  * Tags: `["bmad", "process"]` (+ `["sprint_status"]` where relevant)
  * `priority ≈ 0.5–0.6`

---

### 4.9 Root Docs (`docs/*.md`)

Treat as specialised domains when obvious, otherwise `domain = "docs"`:

Examples:

* `architecture.md`

  * `domain = "architecture"`
  * Tags: `["architecture", "overview", "jarvis_architecture"]`
  * `priority = 0.9`
* `jarvis-knowledge-pipeline.md`

  * `domain = "architecture"`
  * Tags: `["knowledge_pipeline", "memory"]`
  * `priority = 0.9`
* `LLM_*`

  * `domain = "llm"`
  * Tags: `["llm", "models"]`
* `BUGFIXES.md`, `TROUBLESHOOTING.md`

  * `domain = "troubleshooting"`
  * Tags: `["bugfix"]` / `["troubleshooting"]`
* `README.md`, `QUICK-REFERENCE.md`, `ENHANCEMENTS-QUICK-START.md`

  * `domain = "docs"`
  * Tags: `["readme", "quick_start"]`
  * `priority ≈ 0.7`
* Everything else:

  * `domain = "docs"`
  * Tags: `["docs"]` + filename-based tag.

---

## 5. Retrieval Rules

### 5.1 Default Filter (QA / Normal Use)

When building the Qdrant filter (`_build_qdrant_filter`):

* Always apply:

```python
if not include_stale:
    is_latest == True

if not allow_system:
    is_system == False
```

* And apply domain / tag filters as requested.

**Default behaviour:**

* Excludes:

  * `archive` (`is_latest=false`)
  * `jarvis-core` (`is_system=true`)
* Includes:

  * architecture, features, playbooks, sessions, stories, epics, process, root docs.

### 5.2 Historical / Stale Mode

For historical queries (`--allow-stale` or similar):

* Drop or relax `is_latest == True`.
* Still keep `is_system == False` unless explicitly doing system introspection.

### 5.3 System / Introspection Mode

When user asks about **Jarvis itself** or explicitly targets `jarvis-core`:

* Set `allow_system = True` in `_build_qdrant_filter`.
* Optionally restrict `domain = "jarvis-core"` to avoid noise.

---

## 6. Ingestion Script Contract

The ingestion script (`scripts/ingest_workspace_docs.py`) MUST:

1. Walk `docs/` tree.
2. For each eligible file (`.md`, `.xml`, `.yaml`, `.yml`):

   * Compute `domain, tags, meta = classify(path)`.
   * Ensure `meta` contains:

     * `is_latest`, `version` (via ingest pipeline), `is_system`, `jarvis_core`, `priority`, `semantic_family`.
3. Call the core ingest function:

   * Which:

     * Upserts `documents` in Postgres with correct `version` & `is_latest`.
     * Writes chunks to Qdrant with full payload.

---

## 7. Testing & Validation

1. **Dry Runs**

   * Always run in “print only” mode first:

     * For 5–10 files in:

       * `docs/jarvis/*`  
       * `docs/jarvis/playbooks/*`
       * `docs/archive/*`
       * `docs/features/*`
       * `docs/sprints/stories/*`
   * Verify manually:

     * Domains, tags, `is_system`, `jarvis_core`, `semantic_family`, `priority`.

2. **Sanity Queries**

   * Normal QA:

     * Confirm `jarvis-core` does NOT appear in random content answers.
   * Introspection:

     * Confirm `jarvis-core` appears only when `allow_system = True` or domain filter is set.
   * Archive:

     * Confirm archive content only appears when explicitly allowed.

---

## 8. Future Extensions

Planned fields and behaviours (not mandatory yet):

* `topic_cluster` / `graph_component` for semantic networking.
* `source_system` (e.g., “workspace-docs”, “cgd”, “ntt-data”).
* Per-domain `recency_half_life` tuning for freshness scoring.

---

## 9. Migration History

### v2 - Vision Mode (2025-12-06)

Reset internal collections and re-ingested via `ingest_workspace_docs.py`.

**Mandatory fields from v2:**
- `domain` - Canonical domain taxonomy
- `tags` - Normalized tag list
- `is_system` - System vs corpus plane
- `semantic_family` - Cluster grouping
- `priority` - Retrieval importance (0.0-1.0)

**New temporal fields:**
- `session_date` - For session logs (YYYY-MM-DD)
- `story_date` - For stories/epics (YYYY-MM-DD)

**RetrievalMode:**
- `NORMAL` - Default QA, excludes system, excludes archive
- `META` - Introspection, includes jarvis-core
- `TIME_SLICE` - Temporal navigation, filters by date
- `HISTORICAL` - Archive mode, allows stale versions

---

**Owner:** Jarvis Architect, Ariel Bastos, Generative Drive  
**Last updated:** 2025-12-06 (Vision Mode v2)

```
