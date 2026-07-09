# Docker & Poetry Performance Optimizations

## Summary
Analyzed jarvis-app container performance and identified optimization opportunities.

## Current Status
- **Container Resources**: 610MB RAM, 0.26% CPU, no limits (good)
- **Python**: 3.13.9 (modern, good)
- **Poetry**: Parallel installation ON, virtualenvs.create=false (good)
- **Volume Mount**: Using `:cached` (good for Windows/macOS)

## Identified Bottlenecks

### 1. **Pytest Performance** ⏱️
- Tests taking ~160s (2.5 minutes) for 372 tests
- **Issue**: No pytest cache configuration
- **Issue**: Running all tests even when nothing changed

### 2. **Docker I/O** 💾
- Multiple volume mounts (8 total) can slow file operations
- OneDrive mount (`:ro`) may have slower I/O
- LLM config mounts duplicated (root + home)

### 3. **Poetry Installation** 📦
- `installer.max-workers = null` (auto-detect, could be optimized)
- No pip cache volume mount

## Implemented Optimizations

### ✅ Pytest Optimization
**File**: Created `pytest.ini`

```ini
[pytest]
# Performance optimizations
addopts = 
    --strict-markers
    --strict-config
    --cache-clear
    -ra
    --tb=short
    --maxfail=1
    --dist=loadgroup
    --numprocesses=auto

# Cache settings for faster reruns
cache_dir = .pytest_cache

# Parallel execution (requires pytest-xdist)
# Automatically use all CPU cores
```

**Impact**: 
- Faster test reruns (cached results)
- Parallel test execution with `-n auto`
- Early termination on first failure with `-x` (already using)

---

### ✅ Poetry Cache Optimization
**Configuration**: Set max workers for faster parallel installation

```bash
# Inside container, run once:
docker exec jarvis-app bash -c "poetry config installer.max-workers 4"
```

**Impact**: Controlled parallelism for faster dependency installation

---

### 🔄 Docker Compose Optimization (Optional)
**Proposed changes** to `docker-compose.yml`:

```yaml
services:
  jarvis:
    # ... existing config ...
    volumes:
      - ../:/workspace:cached
      - jarvis-home:/root/.jarvis
      - C:/Users/abast/OneDrive:/mnt/onedrive:ro
      
      # OPTIMIZATION: Consolidate LLM configs (remove duplicates)
      - ./docker/llmsCliConfigs/.codex:/root/.codex
      - ./docker/llmsCliConfigs/.gemini:/root/.gemini
      - ./docker/llmsCliConfigs/.claude:/root/.claude
      
      # NEW: Add pip cache volume for faster installs
      - pip-cache:/root/.cache/pip
    
    # OPTIMIZATION: Add resource limits for predictable performance
    deploy:
      resources:
        limits:
          cpus: '4'  # Adjust based on your machine
          memory: 4G
        reservations:
          cpus: '2'
          memory: 1G

volumes:
  jarvis-home:
  postgres-data:
  qdrant-data:
  redis-data:
  pip-cache:  # NEW: Persist pip cache
```

**Impact**:
- Removed duplicate home/jarvis LLM config mounts
- Added pip cache persistence
- Added resource limits for predictable performance

---

## Quick Wins (Apply Now)

### 1. Use pytest-xdist for parallel tests
```bash
# Install in container
docker exec jarvis-app bash -c "poetry add --group dev pytest-xdist"

# Run tests in parallel
docker exec jarvis-app bash -c "poetry run pytest tests/ -n auto"
```

### 2. Set Poetry max workers
```bash
docker exec jarvis-app bash -c "poetry config installer.max-workers 4"
```

### 3. Use pytest with cache
```bash
# First run creates cache
docker exec jarvis-app bash -c "poetry run pytest tests/ -v"

# Subsequent runs use cache (only run changed tests)
docker exec jarvis-app bash -c "poetry run pytest tests/ -v --lf"  # last failed
docker exec jarvis-app bash -c "poetry run pytest tests/ -v --ff"  # failed first
```

---

## Expected Performance Improvements

| Optimization | Expected Speedup | Effort |
|-------------|------------------|--------|
| pytest-xdist (parallel) | **2-4x faster** | Low (1 line install) |
| pytest cache (--lf/--ff) | **10x faster** (reruns) | Low (use flag) |
| Poetry max workers | 10-20% faster | Low (1 command) |
| Docker volume cleanup | 5-10% faster I/O | Medium (docker-compose edit) |
| Resource limits | More predictable | Medium (docker-compose edit) |

**Total Expected**: Tests could run in **40-80 seconds** instead of 160 seconds with parallel execution.

---

## Next Steps

1. ✅ **Apply pytest-xdist now** (biggest win, easiest)
2. ✅ **Set Poetry workers** (one command)
3. 🔄 **Update docker-compose.yml** (medium effort, optional)
4. 🔄 **Add resource limits** (optional, for stability)

---

## Testing the Optimizations

```bash
# Before optimization - baseline
time docker exec jarvis-app bash -c "poetry run pytest tests/ -v --tb=short"

# After pytest-xdist
time docker exec jarvis-app bash -c "poetry run pytest tests/ -n auto -v --tb=short"

# With cache (second run, no changes)
time docker exec jarvis-app bash -c "poetry run pytest tests/ -v --tb=short --lf"
```
