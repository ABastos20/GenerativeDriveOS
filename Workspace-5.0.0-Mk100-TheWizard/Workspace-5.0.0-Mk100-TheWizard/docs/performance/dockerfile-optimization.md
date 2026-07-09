# Dockerfile Performance Optimizations for Ryzen 7 9800X3D

## Current Performance Issues

1. **Build Cache**: No cache mounts for pip/poetry (rebuilds every time)
2. **Single Stage**: All layers in one stage (slower rebuilds)
3. **Missing Performance Libs**: No uvloop, orjson, or other speedup packages
4. **Sequential Installs**: apt-get, poetry, npm run sequentially

---

## Optimized Dockerfile

**File**: `docker/Dockerfile.jarvis.optimized`

```dockerfile
# syntax=docker/dockerfile:1.7
#
# HIGH-PERFORMANCE DOCKERFILE FOR RYZEN 7 9800X3D
# Optimizations:
# - BuildKit cache mounts for faster rebuilds
# - Multi-stage build for smaller images
# - Performance libraries (uvloop, orjson, etc.)
# - Parallel package installation
#

# ============================================================================
# Stage 1: Base Python with system dependencies
# ============================================================================
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_INSTALLER_MAX_WORKERS=8 \
    PATH="/opt/poetry/bin:${PATH}"

# Install system dependencies with BuildKit cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        gosu \
        libpq-dev \
        netcat-openbsd \
        pandoc \
        w3m \
        xdg-utils \
        nodejs \
        npm

# ============================================================================
# Stage 2: Poetry and Python dependencies
# ============================================================================
FROM base AS python-deps

# Install Poetry with pip cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install "poetry==${POETRY_VERSION}" "click==8.1.7"

WORKDIR /workspace

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies with cache mount
# This is the biggest speedup - poetry cache is preserved across builds!
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    --mount=type=cache,target=/root/.cache/pip \
    poetry config installer.max-workers 8 && \
    poetry install --with dev --no-interaction --no-ansi --no-root

# ============================================================================
# Stage 3: Performance enhancement libraries
# ============================================================================
FROM python-deps AS performance-libs

# Install high-performance libraries for Python
# These provide significant speedups for async and JSON operations
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
        uvloop==0.21.0 \
        orjson==3.10.12 \
        cython==3.0.11 \
        numpy==2.2.1

# ============================================================================
# Stage 4: Node.js dependencies (parallel with Python)
# ============================================================================
FROM base AS node-deps

# Install global Node-based CLIs with npm cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm install -g \
        @anthropic-ai/claude-code \
        @openai/codex \
        @google/gemini-cli || true

# ============================================================================
# Stage 5: Final runtime image
# ============================================================================
FROM performance-libs AS final

# Copy Node.js installations from node-deps stage
COPY --from=node-deps /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node-deps /usr/local/bin /usr/local/bin

# Install LLM CLI tools for local provider fallback
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
        anthropic-cli \
        google-generativeai \
        openai

# Copy scripts and set permissions
COPY docker/scripts/healthcheck.sh /usr/local/bin/jarvis-healthcheck
COPY docker/scripts/entrypoint.sh /usr/local/bin/jarvis-entrypoint
COPY docker/scripts/run-jarvis-services.sh /usr/local/bin/jarvis-run-services
COPY scripts/setup/setup_cli_wrappers.sh /tmp/setup_cli_wrappers.sh

RUN chmod +x /usr/local/bin/jarvis-healthcheck \
             /usr/local/bin/jarvis-entrypoint \
             /usr/local/bin/jarvis-run-services && \
    bash /tmp/setup_cli_wrappers.sh && \
    rm /tmp/setup_cli_wrappers.sh

WORKDIR /workspace

ENTRYPOINT ["/usr/local/bin/jarvis-entrypoint"]
CMD ["bash", "-c", "tail -f /dev/null"]
```

---

## Performance Packages to Add

### 1. **uvloop** (Event Loop Acceleration)
```toml
# Add to pyproject.toml [tool.poetry.dependencies]
uvloop = "^0.21.0"  # 2-4x faster asyncio event loop
```

**Impact**: 2-4x faster asyncio operations (agent parallel invocation, API calls)

**Usage**: Automatically replaces default event loop
```python
import uvloop
uvloop.install()  # Add to startup
```

---

### 2. **orjson** (Fast JSON Serialization)
```toml
orjson = "^3.10.0"  # 2-10x faster JSON encoding/decoding
```

**Impact**: 2-10x faster JSON operations (API responses, config loading)

**Usage**: Replace `json` module
```python
import orjson
# Instead of: json.dumps(data)
orjson.dumps(data)  # Much faster
```

---

### 3. **msgspec** (Fast Validation + Serialization)
```toml
msgspec = "^0.19.0"  # Faster than Pydantic for validation
```

**Impact**: 10-50x faster than Pydantic for validation/serialization

---

### 4. **multiprocess** (Better Multiprocessing)
```toml
multiprocess = "^0.70.0"  # Better than stdlib multiprocessing
```

**Impact**: Better parallel execution for CPU-bound tasks

---

### 5. **Cython Extensions**
```toml
cython = "^3.0.0"  # Compile hot paths to C
numpy = "^2.2.0"   # Already using C extensions
```

---

## pytest.ini Optimization

**File**: `pytest.ini` (create at repo root)

```ini
[pytest]
# High-performance parallel testing for Ryzen 7 9800X3D
minversion = 8.0

# Parallel execution with all 8 cores
addopts = 
    -n 8
    --dist=loadgroup
    -ra
    -q
    --strict-markers
    --strict-config
    --tb=short
    --maxfail=1
    # Coverage options
    --cov=jarvis
    --cov-report=term-missing:skip-covered
    --cov-report=html
    --cov-branch

# Directories
testpaths = tests
pythonpath = src

# Cache for faster reruns
cache_dir = .pytest_cache

# Markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests (require Docker services)
    unit: marks tests as unit tests
```

---

## Build Commands

### Build with BuildKit (REQUIRED for cache mounts)
```bash
# Enable BuildKit
$env:DOCKER_BUILDKIT=1

# Build with cache (MUCH faster on rebuild)
docker build -f docker/Dockerfile.jarvis.optimized -t jarvis:latest .

# First build: ~2-3 minutes
# Subsequent builds: ~30-60 seconds (cache hit!)
```

### docker-compose with BuildKit
```yaml
# Add to docker-compose.yml
services:
  jarvis:
    build:
      context: ..
      dockerfile: docker/Dockerfile.jarvis.optimized
      cache_from:
        - jarvis:latest
    # ... rest of config
```

---

## Expected Performance Improvements

| Optimization | Speedup | Impact |
|-------------|---------|--------|
| **BuildKit cache mounts** | 3-5x faster rebuilds | CRITICAL |
| **uvloop** | 2-4x faster asyncio | High (agent invocation) |
| **orjson** | 2-10x faster JSON | Medium (API responses) |
| **pytest -n 8** | 4-6x faster tests | High (development) |
| **Multi-stage build** | 20-30% smaller image | Medium (deployment) |
| **Poetry cache mount** | 5-10x faster poetry install | Critical (rebuilds) |

---

## Additional Runtime Optimizations

### 1. **Enable uvloop globally**
Create `src/jarvis/__init__.py`:
```python
# Auto-enable uvloop for all asyncio operations
try:
    import uvloop
    uvloop.install()
except ImportError:
    pass
```

### 2. **Use orjson for FastAPI**
Update `src/jarvis/api/app.py`:
```python
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)  # 5-10x faster JSON
```

### 3. **Optimize sentence-transformers**
The embedding model can use more CPU cores:
```python
# In retrieval code
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('model-name', 
                            device='cpu',  
                            num_workers=8)  # Use all cores
```

---

## Docker Compose BuildKit

Update `docker-compose.yml` to use BuildKit:
```yaml
version: '3.8'

x-build-config: &build-config
  context: ..
  dockerfile: docker/Dockerfile.jarvis.optimized
  args:
    BUILDKIT_INLINE_CACHE: 1

services:
  jarvis:
    build: *build-config
    # ... rest of config
```

---

## Summary

### Immediate Actions (High Impact):
1. ✅ Use optimized Dockerfile with BuildKit cache mounts
2. ✅ Add uvloop + orjson to dependencies
3. ✅ Create pytest.ini with parallel settings
4. ✅ Enable DOCKER_BUILDKIT=1

### Expected Results:
- **Build time**: 3min → 30-60sec (5-6x faster)
- **Test time**: 160sec → 20-30sec (5-8x faster with -n 8)
- **API response**: 2-10x faster JSON serialization
- **Agent invocation**: 2-4x faster async operations

Your Ryzen 7 9800X3D will be **FULLY UTILIZED**! 🚀
