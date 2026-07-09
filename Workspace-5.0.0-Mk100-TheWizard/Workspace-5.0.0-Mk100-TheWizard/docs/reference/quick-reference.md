# Jarvis Quick Reference Card

**Version**: 1.0.0
**Last Updated**: 2025-12-03

One-page reference for common Jarvis operations, commands, and configurations.

---

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Check service health
docker ps

# Access Web UI
http://localhost:8000/chat

# Test API
curl http://localhost:8000/dashboard/api/stats
```

---

## 📝 CLI Commands

### Memory Operations
```bash
# Add document to knowledge base
jarvis memory add docs/my-doc.md

# Add entire directory
jarvis memory add docs/

# Search memory
jarvis memory search "query text"

# Search with filters
jarvis memory search "query" --source gd.generative_drive --since 7d

# List all documents
jarvis memory list

# Compile conversation insights
jarvis memory compile 7d
jarvis memory compile --since 2025-11-01 --until 2025-11-30
```

### Query Commands
```bash
# Basic query
jarvis query "What is the RAG pipeline?"

# With retrieval options
jarvis query "..." -k 15 --retriever hybrid --weight 0.7

# With query expansion
jarvis query "..." --expand 3

# With grounding control
jarvis query "..." --grounding-level strict
jarvis query "..." --show-confidence

# Disable auto-grounding
jarvis query "..." --no-auto-grounding

# Output as JSON
jarvis query "..." --json

# Enable autonomous research
jarvis query "What's new in Qdrant 1.15?" --enable-research --coverage-threshold 0.6 --max-queries 5 --cost-cap 0.50

# Research analytics summary
jarvis analytics research-summary --since 7d
```

---

## 🌐 API Endpoints

### Chat Endpoint
```bash
POST /api/chat
{
  "message": "Your question here",
  "k": 15,
  "expand": 3,
  "auto_grounding": true,
  "show_confidence": false,
  "source": "gd.generative_drive",  // optional domain filter
  "grounding_level": null,  // null = auto-detect
  "retriever": "hybrid",  // semantic | keyword | hybrid
  "weight": 0.7,  // for hybrid retriever
  "enable_research": true,
  "research_config": {
    "coverage_threshold": 0.6,
    "max_queries": 5,
    "cost_cap_usd": 0.5
  }
}
```

**Response**:
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "query": "Your question",
  "response": "Answer with citations [1][2]",
  "sources": [
    {
      "id": 1,
      "content": "Source text...",
      "source_file": "path/to/file.md",
      "domain": "jarvis.core",
      "relevance_score": 0.85
    }
  ],
  "metadata": {
    "status": "ok",
    "llm_provider": "openrouter",
    "model": "google/gemini-2.0-flash-exp:free",
    "total_tokens": 1234,
    "cost_usd": 0.001,
    "grounding_level": "balanced"
  }
}
```

### Dashboard Stats
```bash
GET /dashboard/api/stats

# Returns: retrieval heatmap, cost tracking, timeline archetype
```

### Conversations
```bash
# List conversations
GET /api/conversations?limit=20

# Get conversation details
GET /api/conversations/{conversation_id}?page_size=100
```

---

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Required
POSTGRES_PASSWORD=your_password_here
OPENROUTER_API_KEY=your_key_here

# Optional
JARVIS_GROUNDING_LEVEL=balanced  # soft | balanced | strict
WORKSPACE_ROOT=/workspace
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=jarvis
POSTGRES_USER=jarvis
```

### Settings File (config/settings.yaml)
```yaml
project:
  name: "Jarvis"
  environment: "production"

query:
  default_retriever: "semantic"  # semantic | keyword | hybrid
  default_weight: 0.7  # for hybrid retriever
  default_strict_mode: false
  enable_expansion: false
  expansion_count: 2
  default_grounding_level: "balanced"  # soft | balanced | strict
```

---

## 🧠 Grounding Levels

| Level | When to Use | Behavior |
|-------|-------------|----------|
| **soft** | Brainstorming, ideation | Allow bridging, mark speculation |
| **balanced** | Explanations, technical docs | Every major claim cites |
| **strict** | Compliance, critical info | Zero hallucination, librarian mode |

**Auto-Selected By Intent**:
- "What is..." → **strict**
- "Explain..." → **balanced**
- "Brainstorm..." → **soft**

---

## 🔍 Search Retrievers

| Retriever | Best For | Speed |
|-----------|----------|-------|
| **semantic** | Conceptual similarity | Fast ⚡ |
| **keyword** | Exact terms, technical names | Fast ⚡ |
| **hybrid** | Balance of both (weight=0.7) | Medium ⏱️ |

---

## 📊 Domain Catalog

| Domain | Contains |
|--------|----------|
| `jarvis.core` | Core documentation, architecture |
| `jarvis.conversations` | Chat history, user interactions |
| `jarvis.gpt_export` | Exported GPT conversations |
| `gd.generative_drive` | GenerativeDrive projects (Sines, ValeBH2) |
| `project.sprints` | Epics, stories, sprint planning |
| `cyber.security` | Security docs, vulnerabilities |

**Auto-Inferred From**:
- Keywords in query (e.g., "game" → gd.generative_drive)
- Time references (e.g., "2024" → jarvis.conversations)
- Always includes: jarvis.conversations + jarvis.core

---

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart specific service
docker restart jarvis-app

# View logs
docker logs jarvis-app --tail 50 -f
docker logs jarvis-postgres --tail 30
docker logs jarvis-qdrant --tail 30

# Execute command in container
docker exec jarvis-app python -m jarvis.cli.main memory list
docker exec jarvis-app python -m jarvis.cli.main query "test"

# Check PostgreSQL
docker exec jarvis-postgres psql -U jarvis -d jarvis \
  -c "SELECT COUNT(*) FROM conversations;"

# Shell into container
docker exec -it jarvis-app bash
docker exec -it jarvis-postgres psql -U jarvis -d jarvis
```

---

## 🔧 Debugging

### Quick Health Check
```bash
# All services up?
docker ps | grep jarvis

# API responding?
curl http://localhost:8000/

# Database connected?
docker exec jarvis-app python -c "from src.jarvis.database.postgres import get_engine; get_engine()"

# Qdrant accessible?
curl http://localhost:6333/collections/knowledge | jq .
```

### Common Error Patterns

**503 Service Unavailable**:
- Check missing imports in `src/jarvis/api/chat.py`
- Verify database connection: `docker logs jarvis-postgres`

**Datetime Comparison Error**:
- Use `datetime.now(timezone.utc)` instead of `datetime.utcnow()`

**No Search Results**:
- Check collection has vectors: `curl http://localhost:6333/collections/knowledge | jq '.result.vectors_count'`
- Verify documents ingested: `jarvis memory list`

**Slow Queries**:
- Reduce k value (use k=5-15)
- Reduce expansion count (use expand=0-3)
- Check LLM provider performance

---

## 📚 File Structure

```
workspace/
├── src/jarvis/
│   ├── api/
│   │   ├── app.py              # FastAPI application
│   │   ├── chat.py             # Chat endpoint (⚠️ check imports!)
│   │   ├── dashboard.py        # Dashboard stats
│   │   └── schemas.py          # Pydantic models
│   ├── cli/
│   │   ├── query.py            # CLI query command
│   │   └── memory.py           # CLI memory commands
│   ├── memory/
│   │   ├── search.py           # RAG search functions
│   │   ├── intent_analyzer.py  # Autonomous grounding
│   │   └── confidence_scorer.py # In-line confidence tags
│   ├── database/
│   │   ├── postgres.py         # Database connection
│   │   └── models.py           # SQLAlchemy models
│   └── config/
│       └── settings.py         # Configuration loader
├── docs/
│   ├── VARIABLE-GROUNDING-SYSTEM.md
│   ├── BUGFIXES.md
│   ├── TROUBLESHOOTING.md
│   └── sessions/
│       └── 2025-12-03-BREAKTHROUGH-SESSION.md
├── config/
│   └── settings.example.yaml
├── docker-compose.yml
└── .env
```

---

## 🔐 Security Notes

- Never commit `.env` with real credentials
- Use `.env.example` for templates
- Rotate API keys regularly
- Use `JARVIS_ALLOW_CREATIVE_FALLBACK=false` in production for strict mode

---

## 📖 Documentation Links

- [Variable Grounding System](VARIABLE-GROUNDING-SYSTEM.md)
- [Implementation Summary](../IMPLEMENTATION-SUMMARY.md)
- [Bug Fixes Log](BUGFIXES.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Session Notes](sessions/2025-12-03-BREAKTHROUGH-SESSION.md)

---

## 🎯 Quick Wins

### Improve Search Quality
```bash
# Increase retrieval
-k 15

# Add query expansion
--expand 3

# Use hybrid retriever
--retriever hybrid --weight 0.7

# Filter to specific domain
--source gd.generative_drive
```

### Speed Up Responses
```bash
# Reduce retrieval
-k 5

# Disable expansion
--expand 0

# Use semantic only
--retriever semantic

# Use faster model
--provider openrouter --model google/gemini-2.0-flash-exp:free
```

### Debug Issues
```bash
# Enable JSON output
--json

# Show confidence tags
--show-confidence

# Increase verbosity
--verbose  # if available
```

---

## 🚨 Emergency Commands

### Complete Reset
```bash
docker-compose down -v  # ⚠️ DELETES ALL DATA
docker-compose up -d
docker exec jarvis-app python -m jarvis.cli.main memory add docs/
```

### Restart Single Service
```bash
docker restart jarvis-app
```

### Check Logs for Errors
```bash
docker logs jarvis-app 2>&1 | grep -i error
docker logs jarvis-postgres 2>&1 | grep -i error
```

---

## 💡 Pro Tips

1. **Always check imports** when adding new features to `chat.py`
2. **Use timezone-aware datetimes** with `datetime.now(timezone.utc)`
3. **Test API endpoints** after code changes, not just CLI
4. **Monitor logs** during development: `docker logs -f jarvis-app`
5. **Keep k reasonable** (5-15 for most queries)
6. **Use auto-grounding** unless you have specific needs
7. **Enable confidence tags** during development/debugging
8. **Compile memory regularly** to generate insights: `jarvis memory compile 7d`

---

**Generated by**: Claude (Anthropic)
**Maintainer**: Ariel Bastos (@ABastos20)
**Version**: 1.0.0 (2025-12-03)
