# JARVIS Memory Ingestion Guide

This guide shows how to bootstrap JARVIS's memory system with core documentation and GPT conversations.

## Prerequisites

- Docker Compose running (PostgreSQL, Qdrant, Redis, jarvis-app)
- GPT export at `docs/gpt export/conversations.json`
- Jarvis core docs at `docs/jarvis/`

## Quick Start (Recommended)

Run the master bootstrap script inside the jarvis-app container:

```bash
# From project root
docker compose -f docker/docker-compose.yml run --rm jarvis python scripts/bootstrap_jarvis_memory.py
```

This will:
1. ✅ Initialize Qdrant collection "knowledge" (if needed)
2. ✅ Ingest Jarvis core docs (persona.md, operating-manual.md)
3. ✅ Ingest 16 GPT conversations with embeddings
4. ✅ Validate collection health

**Expected duration:** 5-10 minutes (embedding generation is the slowest part)

## Options

### Dry Run (See What Would Be Ingested)

```bash
docker compose -f docker/docker-compose.yml run --rm jarvis python scripts/bootstrap_jarvis_memory.py --dry-run
```

### Skip GPT Conversations (Just Core Docs)

```bash
docker compose -f docker/docker-compose.yml run --rm jarvis python scripts/bootstrap_jarvis_memory.py --skip-gpt
```

### Custom GPT Export Path

```bash
docker compose -f docker/docker-compose.yml run --rm jarvis python scripts/bootstrap_jarvis_memory.py --gpt-export "path/to/conversations.json"
```

## Step-by-Step (Manual)

If you prefer to run each step individually:

### 1. Initialize Qdrant Collection

```bash
docker compose -f docker/docker-compose.yml run --rm jarvis python scripts/init_qdrant.py
```

### 2. Ingest Jarvis Core Docs

```bash
docker compose -f docker/docker-compose.yml run --rm jarvis python scripts/ingest_jarvis_docs.py
```

### 3. Ingest GPT Conversations

```bash
docker compose -f docker/docker-compose.yml run --rm jarvis python scripts/ingest_gpt_conversations.py
```

## Validation

Check collection health:

```bash
docker compose -f docker/docker-compose.yml exec jarvis-app python -c "
import sys
sys.path.insert(0, '/workspace/src')
from jarvis.database.qdrant import get_qdrant_client, get_collection_info
client = get_qdrant_client()
info = get_collection_info('knowledge', client=client)
print(f'Collection: knowledge')
print(f'Points: {info.points_count}')
print(f'Vector size: {info.config.params.vectors.size}')
print(f'Distance: {info.config.params.vectors.distance.value}')
"
```

Or use the doctor command:

```bash
docker compose -f docker/docker-compose.yml run --rm jarvis python -c "
import sys
sys.path.insert(0, '/workspace/src')
from jarvis.cli.doctor_checks import check_qdrant_collection
result = check_qdrant_collection('knowledge')
print(f'{result.name}: {result.message} (passed={result.passed})')
"
```

## Troubleshooting

### "Module 'jarvis' not found"

The scripts are designed to run **inside** the Docker container where Python paths are configured. Use:
```bash
docker compose -f docker/docker-compose.yml run --rm jarvis python scripts/...
```

### "Qdrant connection failed"

Ensure Qdrant service is running:
```bash
docker compose -f docker/docker-compose.yml ps qdrant
```

Start if needed:
```bash
docker compose -f docker/docker-compose.yml up -d qdrant
```

### "Conversations.json not found"

Verify GPT export location:
```bash
ls -la "docs/gpt export/conversations.json"
```

### Slow Embedding Generation

The sentence-transformers model generates 384-d embeddings for each chunk. For 16 conversations (~50-100 chunks), expect 3-5 minutes on CPU.

## What Gets Ingested

### Jarvis Core Docs (~2-5 chunks each)
- `docs/jarvis/persona.md` → domain: "jarvis-core"
- `docs/jarvis/operating-manual.md` → domain: "jarvis-core"
 - `docs/gptExportNEW/memory.core.md` → domain: "jarvis-core" (long-horizon Jarvis+user memory)

### GPT Conversations (~50-100 total chunks)
- 16 conversations from `docs/gpt export/conversations.json`
- Domain: "jarvis-conversations"
- Each conversation chunked to ~2000 chars
- Metadata: title, conversation_id, chunk_index, create_time

### Point Payload Structure

```json
{
  "text": "chunk content",
  "source_file": "docs/jarvis/persona.md",
  "section": "persona.md",
  "domain": "jarvis-core",
  "ingested_at": "2025-11-21T14:52:00.000Z",
  "hash": "sha256..."
}
```

### Additional Sources (Workspace & OneDrive)

Beyond the bootstrap script, you can ingest additional knowledge sources:

- **Repo docs and BMAD artifacts:**
  - `scripts/ingest-all-docs.sh` walks `docs/**.md` and `.bmad/bmm/**.md` and ingests them into the `knowledge` collection via `jarvis memory add`.

- **Host OneDrive (mounted read-only inside Docker):**
  - `docker/docker-compose.yml` mounts your host OneDrive at `/mnt/onedrive:ro` inside `jarvis-app`.
  - From inside the container you can ingest markdown, text, and PDF files:

    ```bash
    cd /workspace
    export PYTHONPATH=/workspace/src

    find /mnt/onedrive -type f \( \
      -name '*.md' -o -name '*.markdown' -o -name '*.txt' -o -name '*.pdf' \
    \) ! -path '*/.git/*' ! -path '*/node_modules/*' ! -path '*/.venv/*' -print0 |
    xargs -0 -n1 -P2 python -m jarvis.cli.main memory add
    ```

  - Under the hood:
    - `.md` / `.markdown` / `.txt` are read directly and chunked.
    - `.pdf` is converted to text via PyPDF2 before chunking.

## Integration Plan Status

After running bootstrap script, update `docs/jarvis/integration-plan.md`:

- [x] Phase 1: Normalize GPT export into project docs
- [x] Phase 2: Wire Jarvis core into runtime (architecture references)
- [x] **Phase 3: Make Jarvis core searchable in memory** ← YOU ARE HERE
  - [x] Qdrant collection initialized
  - [x] Core docs ingested with domain tags
  - [x] GPT conversations embedded and stored
- [ ] Phase 4: Align assistants with Jarvis core
- [ ] Phase 5: Maintenance & evolution

## Dev Commands Cheat Sheet

### Run ingestion tests locally (WSL)

From project root, with `.venv` active and Qdrant on `localhost:6333`:

```bash
QDRANT_HOST=localhost QDRANT_PORT=6333 \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS='' \
python -m pytest -o addopts='' \
  tests/unit/memory/test_ingest.py \
  tests/integration/memory/test_ingest_integration.py
```

### Sanity-check retrieval inside jarvis-app

After bootstrapping memory, you can query the `knowledge` collection directly:

```bash
docker compose -f docker/docker-compose.yml exec jarvis-app bash -lc '
  export PYTHONPATH=/workspace/src QDRANT_HOST=qdrant QDRANT_PORT=6333
  python - << "PY"
from jarvis.memory import search

results = search.search_memory("jarvis core rules", k=3, domains=["jarvis-core"])
for r in results:
    print(r.score, r.domain, r.source_file, "->", r.text[:120].replace("\\n", " "))
PY
'
```

This should return snippets from `docs/jarvis/persona.md` and `docs/jarvis/operating-manual.md` with domain `jarvis-core`.

### CLI search from WSL venv

With `.venv` active and Qdrant running on localhost:

```bash
PYTHONPATH=src QDRANT_HOST=localhost QDRANT_PORT=6333 \
python -m jarvis.cli.memory search "jarvis core rules" --source jarvis-core --k 3
```

## Next Steps

1. **Query the memory:** Story 2.4 (Memory Retrieval Filters & API)
2. **Test semantic search:** Query for "GenerativeDrive" or "telemetry" to retrieve relevant GPT conversations
3. **Build CLI query command:** `jarvis ask "What is GenerativeDrive?"`

---

**Scripts:**
- [bootstrap_jarvis_memory.py](scripts/bootstrap_jarvis_memory.py) - Master script (recommended)
- [init_qdrant.py](scripts/init_qdrant.py) - Collection initialization
- [ingest_jarvis_docs.py](scripts/ingest_jarvis_docs.py) - Core docs only
- [ingest_gpt_conversations.py](scripts/ingest_gpt_conversations.py) - GPT conversations only

**Documentation:**
- [Integration Plan](docs/jarvis/integration-plan.md) - Full integration roadmap
- [Conversation Index](docs/jarvis/conversation-index.md) - List of ingested conversations
