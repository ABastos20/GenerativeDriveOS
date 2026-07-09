# Jarvis Troubleshooting Guide

**Last Updated**: 2025-12-03
**Status**: Production Reference

This guide documents common issues, their root causes, and proven solutions based on real production incidents.

---

## Quick Diagnostic Commands

```bash
# Check all services health
docker ps
docker logs jarvis-app --tail 50
docker logs jarvis-postgres --tail 30
docker logs jarvis-qdrant --tail 30

# Check API status
curl -s http://localhost:8000/dashboard/api/stats | jq .

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "k": 5}' | jq .

# Check database connections
docker exec jarvis-postgres psql -U jarvis -d jarvis \
  -c "SELECT count(*) as active, state FROM pg_stat_activity WHERE datname='jarvis' GROUP BY state;"

# Check Qdrant collection
curl -s http://localhost:6333/collections/knowledge | jq .
```

---

## Common Issues

### 1. 503 Service Unavailable on Chat API

**Symptoms**:
- Web UI chat returns 503 errors
- API logs show: `"POST /api/chat HTTP/1.1" 503 Service Unavailable`
- No database connection errors in PostgreSQL logs

**Root Causes**:

#### A. Missing Imports (CRITICAL)
**Error**: Python raises `NameError` when calling undefined functions
**Detection**: Check if imports match function calls in `src/jarvis/api/chat.py`

```python
# Required imports:
from jarvis.memory.confidence_scorer import score_response_confidence
from jarvis.memory.intent_analyzer import analyze_intent
```

**Fix**: Add missing imports to the file calling the functions.

**Prevention**:
- Run full integration tests (not just unit tests)
- Use static type checkers: `mypy src/`
- Add import validation to pre-commit hooks

#### B. Undefined Variables
**Error**: Variable used before definition (e.g., `default_grounding_level`)

```python
# Example error:
effective_grounding_level = default_grounding_level  # ❌ Not defined!

# Fix:
default_grounding_level = getattr(
    getattr(settings, "query", None),
    "default_grounding_level",
    "balanced",
)
effective_grounding_level = default_grounding_level  # ✅ Now defined
```

#### C. Actual Database Connection Issues
**Detection**: Check PostgreSQL logs for connection errors

```bash
docker logs jarvis-postgres --tail 50 | grep -i error
```

**Common causes**:
- Pool exhaustion (check with diagnostic command above)
- Network issues between containers
- PostgreSQL not running

**Fix**:
```bash
# Restart database
docker restart jarvis-postgres

# Check connection from app
docker exec jarvis-app python -c "from src.jarvis.database.postgres import get_engine; get_engine()"
```

---

### 2. Timezone-Aware Datetime Comparison Errors

**Symptoms**:
- Dashboard timeline crashes
- Error: `can't compare offset-naive and offset-aware datetimes`
- Memory search with `--since` parameter fails

**Root Cause**: Comparing naive `datetime.utcnow()` with timezone-aware PostgreSQL timestamps

**Fix Pattern**:
```python
# ❌ WRONG (naive datetime)
from datetime import datetime, timedelta
cutoff = datetime.utcnow() - timedelta(days=7)

# ✅ CORRECT (timezone-aware)
from datetime import datetime, timedelta, timezone
cutoff = datetime.now(timezone.utc) - timedelta(days=7)
```

**Files to Check**:
- `src/jarvis/api/dashboard.py`
- `src/jarvis/cli/memory.py`
- Any file doing datetime comparisons with database timestamps

**Prevention**: Always use `datetime.now(timezone.utc)` instead of `datetime.utcnow()`

---

### 3. Docker Containers Not Starting

**Symptoms**:
- `docker ps` shows containers restarting or exited
- Services unreachable

**Diagnostic**:
```bash
# Check container status
docker ps -a

# Check logs for specific container
docker logs jarvis-app
docker logs jarvis-postgres
docker logs jarvis-qdrant

# Check docker compose status
docker-compose ps
```

**Common Causes**:

#### A. Port Conflicts
```bash
# Check if ports are already in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac
```

**Fix**: Stop conflicting processes or change ports in `docker-compose.yml`

#### B. Environment Variables Missing
Check `.env` file exists and has required vars:
```bash
cat .env | grep -E "POSTGRES_PASSWORD|OPENROUTER_API_KEY"
```

**Fix**: Copy from `.env.example` and fill in values:
```bash
cp .env.example .env
# Edit .env with actual values
```

#### C. Volume Permission Issues
```bash
# Check volume mounts
docker volume ls
docker volume inspect workspace_postgres_data
```

**Fix**:
```bash
# Remove and recreate volumes
docker-compose down -v
docker-compose up -d
```

---

### 4. Memory Search Returns No Results

**Symptoms**:
- `jarvis query "..."` returns: "I could not find enough relevant context"
- Web UI shows no sources
- Even for queries that should match ingested docs

**Diagnostic**:
```bash
# Check Qdrant collection
curl http://localhost:6333/collections/knowledge | jq '.result.vectors_count'

# Check if documents are ingested
docker exec jarvis-app python -m jarvis.cli.main memory list
```

**Common Causes**:

#### A. Empty Collection
**Fix**: Ingest documents
```bash
docker exec jarvis-app python -m jarvis.cli.main memory add docs/
```

#### B. Embedding Model Issues
**Check**: Model loaded correctly
```bash
docker logs jarvis-app | grep "embedding"
```

**Fix**: Restart app to reload model
```bash
docker restart jarvis-app
```

#### C. Domain Mismatch
If using `--source` or domain filter, check domain exists:
```bash
# List all domains in Qdrant
curl http://localhost:6333/collections/knowledge/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "with_payload": true}' | jq '.result.points[].payload.domain' | sort -u
```

---

### 5. Web UI Not Loading

**Symptoms**:
- Browser shows blank page or loading spinner
- Console errors about failed API calls

**Diagnostic**:
```bash
# Check if API is running
curl http://localhost:8000/
curl http://localhost:8000/chat

# Check browser console for errors (F12 → Console)
```

**Common Causes**:

#### A. API Not Running
```bash
docker ps | grep jarvis-app
docker logs jarvis-app --tail 30
```

**Fix**:
```bash
docker restart jarvis-app
# Or
docker-compose restart jarvis-app
```

#### B. Port Mismatch
Check if accessing correct port:
- API: http://localhost:8000
- Not: http://localhost:8001 (that's the reload server)

#### C. CORS Issues
**Check**: Browser console for CORS errors

**Fix**: Verify CORS settings in `src/jarvis/api/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 6. Query Expansion Failing

**Symptoms**:
- `jarvis query "..." --expand 3` returns error
- Logs show expansion failure

**Diagnostic**:
```bash
docker logs jarvis-app | grep -i "expansion"
```

**Common Causes**:

#### A. LLM Provider Down
**Check**: OpenRouter or configured provider status
```bash
curl https://openrouter.ai/api/v1/models
```

**Fix**:
- Wait for provider to recover
- Switch to backup provider
- Disable expansion: `--expand 0`

#### B. API Key Invalid
```bash
# Check environment variable
docker exec jarvis-app env | grep OPENROUTER_API_KEY
```

**Fix**: Update `.env` with valid key and restart

---

### 7. Dashboard Stats Endpoint Errors

**Symptoms**:
- `/dashboard/api/stats` returns 500 error
- Timeline archetype not loading

**Diagnostic**:
```bash
curl http://localhost:8000/dashboard/api/stats
docker logs jarvis-app | grep "dashboard"
```

**Common Causes**:

#### A. Timezone Comparison Errors
See "Timezone-Aware Datetime Comparison Errors" section above.

#### B. Empty Database
**Check**:
```bash
docker exec jarvis-postgres psql -U jarvis -d jarvis \
  -c "SELECT COUNT(*) FROM conversations;"
```

**Fix**: Use the system to generate some conversations, then stats will populate.

---

## Performance Issues

### Slow Query Responses

**Symptoms**: Queries take >10 seconds to respond

**Diagnostic**:
```bash
# Check Qdrant response time
time curl http://localhost:6333/collections/knowledge

# Check database query time
docker exec jarvis-postgres psql -U jarvis -d jarvis \
  -c "SELECT COUNT(*) FROM conversations;" -c "\timing"
```

**Common Causes**:

#### A. Large k Value
**Check**: Using `k > 20` in queries
**Fix**: Reduce k to reasonable range (5-15)

#### B. Too Many Expansions
**Check**: Using `expand > 5`
**Fix**: Reduce to 2-3 expansions

#### C. Slow LLM Provider
**Check**: Which provider is being used
```bash
docker logs jarvis-app | grep "llm_call_start"
```

**Fix**:
- Switch to faster model: `--provider openrouter --model google/gemini-2.0-flash-exp:free`
- Use free tier models for development

---

## Debugging Workflow

When encountering an issue, follow this systematic approach:

### 1. Gather Information
```bash
# Service health
docker ps
docker-compose ps

# Recent logs
docker logs jarvis-app --tail 100
docker logs jarvis-postgres --tail 50
docker logs jarvis-qdrant --tail 30

# Database status
docker exec jarvis-postgres psql -U jarvis -d jarvis -c "SELECT COUNT(*) FROM conversations;"

# API health check
curl http://localhost:8000/dashboard/api/stats
```

### 2. Isolate the Problem
- [ ] Is it a Docker container issue?
- [ ] Is it a database issue?
- [ ] Is it an API endpoint issue?
- [ ] Is it a specific feature issue?
- [ ] Is it a configuration issue?

### 3. Check Documentation
- [ ] BUGFIXES.md - Known issues and fixes
- [ ] IMPLEMENTATION-SUMMARY.md - Feature status
- [ ] This troubleshooting guide

### 4. Test Systematically
```bash
# Test from simple to complex:
# 1. Can Docker reach the database?
docker exec jarvis-app ping jarvis-postgres

# 2. Can app connect to database?
docker exec jarvis-app python -c "from src.jarvis.database.postgres import get_engine; get_engine()"

# 3. Can API respond to health check?
curl http://localhost:8000/

# 4. Can API handle simple query?
curl -X POST http://localhost:8000/api/chat -d '{"message": "test", "k": 1}'

# 5. Can API handle complex query?
curl -X POST http://localhost:8000/api/chat -d '{"message": "Explain the architecture", "k": 15, "expand": 3}'
```

### 5. Fix and Verify
- Apply fix
- Restart relevant services
- Re-run failing test case
- Document in BUGFIXES.md if novel issue

---

## Prevention Best Practices

### 1. Always Test Before Commit
```bash
# Run integration tests
pytest tests/integration/

# Test CLI
jarvis query "test"

# Test API
curl -X POST http://localhost:8000/api/chat -d '{"message": "test", "k": 5}'

# Test Web UI manually (visual check)
```

### 2. Use Type Checking
```bash
# Check for type errors
mypy src/

# Check for undefined variables
pylint src/
```

### 3. Monitor Logs
```bash
# Run in development with logs visible
docker-compose up

# Watch for warnings/errors in real-time
docker logs -f jarvis-app
```

### 4. Keep Documentation Updated
When fixing bugs:
1. Document in `docs/BUGFIXES.md`
2. Update this troubleshooting guide if new pattern emerges
3. Add tests to prevent regression

---

## Emergency Recovery

### Complete System Reset

If everything is broken and you need to start fresh:

```bash
# 1. Stop all containers
docker-compose down

# 2. Remove volumes (⚠️ DELETES ALL DATA)
docker-compose down -v

# 3. Rebuild images
docker-compose build

# 4. Start services
docker-compose up -d

# 5. Wait for services to be ready
sleep 10

# 6. Re-ingest documentation
docker exec jarvis-app python -m jarvis.cli.main memory add docs/

# 7. Verify health
curl http://localhost:8000/dashboard/api/stats
```

### Restore from Backup

If you have backups:

```bash
# Stop services
docker-compose down

# Restore PostgreSQL backup
docker run --rm -v postgres_data:/data -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xvf /backup/postgres-backup.tar"

# Restore Qdrant backup
docker run --rm -v qdrant_data:/data -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xvf /backup/qdrant-backup.tar"

# Restart services
docker-compose up -d
```

---

## Getting Help

### 1. Check Existing Issues
- Review `docs/BUGFIXES.md` for known issues
- Check GitHub issues: https://github.com/ABastos20/Workspace/issues

### 2. Gather Debug Info
Before asking for help, collect:
```bash
# System info
docker version
docker-compose version
uname -a  # Linux/Mac
systeminfo | findstr /C:"OS"  # Windows

# Service logs
docker logs jarvis-app > jarvis-app.log
docker logs jarvis-postgres > jarvis-postgres.log
docker logs jarvis-qdrant > jarvis-qdrant.log

# Configuration (redact secrets!)
cat docker-compose.yml
cat .env | grep -v "PASSWORD\|API_KEY"
```

### 3. Document Your Findings
If you discover a new bug:
1. Add entry to `docs/BUGFIXES.md`
2. Update this troubleshooting guide
3. Commit with descriptive message
4. Consider opening GitHub issue if it's a framework bug

---

## Reference

- [Bug Fixes Log](BUGFIXES.md)
- [Variable Grounding System](VARIABLE-GROUNDING-SYSTEM.md)
- [Implementation Summary](../IMPLEMENTATION-SUMMARY.md)
- [Session Notes](sessions/2025-12-03-BREAKTHROUGH-SESSION.md)

---

**Generated by**: Claude (Anthropic)
**Last Updated**: 2025-12-03
**Maintainer**: Ariel Bastos (@ABastos20)
