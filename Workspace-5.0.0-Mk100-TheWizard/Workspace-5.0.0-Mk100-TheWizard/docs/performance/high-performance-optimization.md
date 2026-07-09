# High-Performance Docker Optimization for Ryzen 7 9800X3D System

## System Specifications
- **CPU**: AMD Ryzen 7 9800X3D (8-core/16-thread, 4.7-5.2GHz)
- **RAM**: 64GB DDR5-6000MHz (2x32GB)
- **Storage**: Samsung 990 Pro 1TB NVMe PCIe Gen 4.0
- **Platform**: Windows with Docker Desktop

---

## Optimized Configuration

### 1. Docker Desktop Settings (Windows)

**Settings → Resources:**

```
CPUs: 12 (out of 16 threads - leave 4 for Windows)
Memory: 48GB (out of 64GB - leave 16GB for Windows)
Swap: 8GB
Disk image size: 200GB (you have 1TB)
```

**WSL 2 Configuration** (`%UserProfile%\.wslconfig`):

```ini
[wsl2]
# Use 12 of 16 threads
processors=12

# Use 48GB of 64GB RAM
memory=48GB

# Swap for safety
swap=8GB

# Performance tuning
localhostForwarding=true

# Disable page reporting for performance
pageReporting=false

# Use nested virtualization
nestedVirtualization=true
```

---

### 2. Optimized docker-compose.yml

```yaml
services:
  jarvis:
    # ... existing config ...
    
    # OPTIMIZED: Resource allocation for your beast system
    deploy:
      resources:
        limits:
          cpus: '10'      # Use 10 of your 16 threads
          memory: 32G     # Plenty of RAM for all operations
        reservations:
          cpus: '6'       # Guarantee 6 cores minimum
          memory: 8G      # Guarantee 8GB minimum
    
    # OPTIMIZED: Volume mounts with delegated mode for maximum performance
    volumes:
      - ../:/workspace:delegated  # CHANGED from :cached to :delegated (faster writes)
      - jarvis-home:/root/.jarvis
      - C:/Users/abast/OneDrive:/mnt/onedrive:ro
      
      # Consolidated LLM configs (removed duplicates)
      - ./docker/llmsCliConfigs/.codex:/root/.codex
      - ./docker/llmsCliConfigs/.gemini:/root/.gemini  
      - ./docker/llmsCliConfigs/.claude:/root/.claude
      
      # NEW: Add caches for performance
      - pip-cache:/root/.cache/pip
      - poetry-cache:/root/.cache/pypoetry
    
    # OPTIMIZED: Environment for parallel execution
    environment:
      # ... existing env vars ...
      - PYTHONUNBUFFERED=1
      - PYTEST_XDIST_AUTO_NUM_WORKERS=8  # Use 8 cores for pytest
      - PIP_NO_CACHE_DIR=0               # Enable pip cache
      - POETRY_INSTALLER_MAX_WORKERS=8   # Max parallel poetry workers

volumes:
  jarvis-home:
  postgres-data:
  qdrant-data:
  redis-data:
  pip-cache:      # NEW
  poetry-cache:   # NEW
```

---

### 3. Poetry Configuration (Aggressive)

```bash
# Run in container
docker exec jarvis-app bash -c "
poetry config installer.max-workers 8 &&
poetry config experimental.new-installer true &&
poetry config cache-dir /root/.cache/pypoetry
"
```

---

### 4. Pytest Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = [
    "-ra",
    "-q",
    "--strict-markers",
    "--strict-config",
    "--tb=short",
    "-n", "8",  # Use 8 cores for parallel testing
    "--dist=loadgroup",
    "--maxfail=3",
]
testpaths = ["tests"]
```

---

### 5. Quick Apply Commands

```bash
# 1. Update Poetry settings (in container)
docker exec jarvis-app bash -c "poetry config installer.max-workers 8"

# 2. Update WSL config (on Windows host - RUN THIS FIRST)
# Create/edit %UserProfile%\.wslconfig with content above

# 3. Restart WSL to apply new limits
wsl --shutdown
# Then restart Docker Desktop

# 4. Verify pytest-xdist is using parallel execution
docker exec jarvis-app bash -c "poetry run pytest tests/ -n 8 -v"
```

---

## Performance Expectations

### Current Performance (Baseline)
- **Test Suite**: ~160 seconds (2min 40s)
- **Poetry Install**: ~30-60 seconds
- **Docker Build**: ~2-3 minutes

### Expected with Optimizations
- **Test Suite**: **30-40 seconds** (4-5x faster with 8-core parallel)
- **Poetry Install**: **10-15 seconds** (3-4x faster with 8 workers)
- **Docker Build**: **45-90 seconds** (2x faster with more resources)

### Expected Resource Usage
- **CPU**: 60-80% of 16 threads during heavy operations
- **RAM**: 8-16GB for normal operations, up to 32GB for heavy tests
- **Disk I/O**: Maxed out on NVMe (very fast, bottleneck elsewhere)

---

## Immediate Actions (Priority Order)

### 🔥 **CRITICAL - Do First:**
1. Create `.wslconfig` in `%UserProfile%` with settings above
2. Run `wsl --shutdown` (closes all WSL instances)
3. Restart Docker Desktop

### ⚡ **High Impact:**
4. Update `docker-compose.yml` with resource limits and cache volumes
5. Run `docker compose down && docker compose up -d` to apply

### ✅ **Medium Impact:**
6. Set Poetry workers: `docker exec jarvis-app bash -c "poetry config installer.max-workers 8"`
7. Add pytest config to `pyproject.toml`

---

## Verification

```bash
# Check WSL resource allocation
wsl --status

# Check Docker resource usage
docker stats jarvis-app --no-stream

# Benchmark test speed
time docker exec jarvis-app bash -c "poetry run pytest tests/ -n 8"

# Expected: 30-45 seconds (vs current 160s)
```

---

## Notes for Your System

✅ **Your Ryzen 7 9800X3D is perfect for Docker** - 3D V-Cache helps with containerized workloads
✅ **64GB RAM is massive** - Can run multiple containers + heavy workloads simultaneously
✅ **990 Pro NVMe is blazing fast** - No storage bottleneck
✅ **DDR5-6000** - Excellent memory bandwidth for parallel operations

**Recommendation**: Use aggressive settings - your system can handle it! 🚀
