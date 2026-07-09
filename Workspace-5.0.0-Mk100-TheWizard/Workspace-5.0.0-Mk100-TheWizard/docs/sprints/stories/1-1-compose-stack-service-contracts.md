# Story 1.1 – Compose Stack & Service Contracts

## Summary
Stand up the foundational Docker Compose stack so all core services (jarvis app, PostgreSQL, Qdrant, Redis) run locally with shared health contracts. This unblocks every downstream epic by establishing a repeatable environment with consistent logging, env management, and volumes.

## Source Links
- Epic reference: `docs/epics.md` → Epic 1, Story 1.1.
- Requirements: `docs/prd.md` (FR5 Docker Containerization, FR6 CLI bootstrap expectations).
- Architecture guidance: `docs/architecture.md` (“Docker Compose Setup”, “Deployment Architecture”).

## Objectives
1. Create `docker/docker-compose.yml` mirroring the architecture doc (services, versions, volumes, health checks, restart policies).
2. Provide Dockerfiles/init scripts: `docker/Dockerfile.jarvis`, `docker/postgres/init-db.sql`, `docker/qdrant/config.yaml`, `docker/redis/*.conf` as needed.
3. Parameterize secrets via `.env`/environment variables (OPENROUTER_API_KEY, TOGETHER_API_KEY, POSTGRES_PASSWORD, etc.).
4. Configure structured logging defaults (structlog) and ensure container logs output JSON.
5. Verify `docker compose up --build` starts all services successfully and expose health endpoints.

## Detailed Requirements
- **Service definitions**: jarvis-app, postgres:18.1, qdrant/qdrant:v1.15.5, redis:latest.
- **Volumes**: host project mount to `/workspace`, persistent volumes (`jarvis-home`, `postgres-data`, `qdrant-data`, `redis-data`).
- **Networking**: bridged `jarvis-network`, exposing only necessary debug ports.
- **Health checks**:
  - PostgreSQL: `pg_isready -U jarvis`.
  - Qdrant: HTTP `/readyz`.
  - Redis: `redis-cli ping`.
  - jarvis-app: script hitting CLI health or `/healthz`.
- **Env handling**: Compose references `.env`, jarvis container uses typed `pydantic-settings`.
- **Commands**: Document `docker compose up -d`, `docker compose down`, `docker compose exec` instructions in README or docs.

## Deliverables
1. `docker/` directory containing Compose file, Dockerfile, and service configs.
2. README update (if needed) pointing to new compose commands.
3. Screenshot/log snippet or CI proof that `docker compose up --build` succeeds.
4. Update `docs/sprints/sprint-status.yaml` status for `1-1-compose-stack-service-contracts` to `drafted`.

## Implementation Plan
1. **Scaffold files**
   - Create `docker/docker-compose.yml` with services/volumes/network definitions.
   - Add `docker/Dockerfile.jarvis` building the Python 3.13 app image (install Poetry/pip, copy source).
2. **Configure service assets**
   - Write Postgres init SQL (database, user, extensions).
   - Provide Qdrant config (if required) and ensure storage paths.
   - Include Redis config for persistence (appendonly).
3. **Environment & logging**
   - Ensure `.env.example` lists required env vars; integrate with Compose.
   - Configure structlog logger to output JSON to stdout.
4. **Verification**
   - Run `docker compose up --build` locally.
   - Confirm logs show healthy startup, run `docker compose ps` + health checks.
5. **Documentation**
   - Add run instructions to README (if additional detail needed).
   - Link to this story file under `docs/sprints/stories`.

## Definition of Done
- Compose file + Docker assets match architecture decisions.
- Running `docker compose up --build` on a clean clone starts all services with healthy statuses.
- Secrets/config are externalized; no hard-coded keys in Compose/Dockerfiles.
- Logging is structured JSON per service (at least jarvis-app).
- Story status updated to `drafted` in sprint file; implementation notes recorded if applicable.

---

## Dev Execution Plan

### Current Context
- No `docker/` folder yet; story will introduce it and all dependency files.
- `.env`/config scaffolding referenced in architecture but not implemented.
- README already explains setup expectations; will need minor updates once commands are final.

### Task Breakdown
1. **Bootstrap docker workspace**
   - Create `docker/` with subfolders for `postgres/`, `qdrant/`, `redis/`.
   - Add `.dockerignore` (reuse `gitignore` patterns plus venv artifacts).
2. **Compose stack (core deliverable)**
   - Author `docker/docker-compose.yml` replicating architecture (services, networks, volumes).
   - Wire environment variables via `.env` and Compose `env_file`.
3. **Jarvis image build**
   - Create `docker/Dockerfile.jarvis` (Python 3.13 slim, Poetry/pip, copy source, install dependencies, set entrypoint).
   - Include healthcheck script referencing CLI command (e.g., `jarvis doctor --json` once available) or stub for now.
4. **Database assets**
   - `docker/postgres/init-db.sql` for schema bootstrap (database, user, extensions like pg_trgm).
   - Document manual migration step until Alembic exists.
5. **Qdrant/Redis configs**
   - Provide default `docker/qdrant/config.yaml` if custom settings needed; otherwise mount data volume only.
   - Add `docker/redis/redis.conf` enabling appendonly.
6. **Logging defaults**
   - Ensure jarvis container uses structlog JSON by referencing env var (e.g., `LOG_FORMAT=json`).
   - Confirm Compose routes logs to stdout (no extra mounts required).
7. **Documentation & verification**
   - Update README quick start w/ `docker compose` commands.
   - Capture sample `docker compose ps` output in PR/notes.
   - Run `docker compose up --build` locally (or describe verification if CI).

### Testing & Validation
- `docker compose config` (lint) should pass.
- `docker compose up --build` yields healthy services; run `docker compose ps` to confirm state = healthy/running.
- `docker compose logs jarvis` should show structlog JSON lines.
- For Postgres, exec `docker compose exec postgres pg_isready -U jarvis`.
- For Qdrant, curl `http://localhost:6333/readyz`.

### Tooling / Commands Cheat Sheet
```bash
docker compose -f docker/docker-compose.yml config
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml logs -f jarvis
docker compose -f docker/docker-compose.yml exec postgres pg_isready -U jarvis
docker compose -f docker/docker-compose.yml down
```

### Dependencies & Coordination
- Story 1.2 depends on these volumes/mounts—coordinate interface (path `/workspace`, `.jarvis/` volume).
- Story 1.3 will piggyback on `.env`/config—ensure env names match PRD (OPENROUTER_API_KEY, TOGETHER_API_KEY, etc.).
- Provide placeholders for tests so Story 1.4 can hook into `jarvis doctor`.

### Risks / Mitigation
- **Windows volume permissions:** document `:cached` or `:delegated` options if necessary.
- **Image size/time:** adopt Poetry cache & multi-stage build to keep rebuilds fast.
- **Secrets leakage:** double-check Compose file references `${VAR}` only; add `.env.example`.

### Open Questions
- Do we include a `docker/.env` template or reuse root `.env`? (Leaning: reuse root for simplicity.)
- Should jarvis container expose ports? Only if CLI->HTTP bridging needed; currently not required.

Answer these before implementation; update story notes as decisions solidify.

---

## Story Readiness Checklist

- [x] Context gathered (PRD FR5, architecture compose spec, epics doc).  
- [x] Detailed plan documented with deliverables, tasks, and test strategy.  
- [x] Dependencies identified (workspace mounts for Story 1.2, config for Story 1.3).  
- [x] Risks surfaced with mitigation notes.
- [x] No blockers outstanding; implementation can begin.

---

## Implementation Notes (Dev Story)

- Added `.env.example` so developers can generate `.env` before running the stack.  
- Compose defaults now set internally (no required secrets; `.env` overrides optional).  
- Created `docker/` workspace containing:
  - `docker/docker-compose.yml` (jarvis, postgres, qdrant, redis w/ healthchecks + volumes).  
  - `docker/Dockerfile.jarvis` (Python 3.13 base, Poetry, workspace mount, healthcheck script).  
  - Service configs (`postgres/init-db.sql`, `qdrant/config.yaml`, `redis/redis.conf`, `scripts/healthcheck.sh`).  
- Updated `README.md` with Docker usage instructions and repository layout references.  
- Compose services verified locally via `docker compose -f docker/docker-compose.yml config` + `up --build`; containers stay running with healthy status.  
- Next stories (1.2–1.4) can now build on the mounted workspace, config management, and CLI diagnostics.
- Postgres mount updated to `/var/lib/postgresql` per v18 requirements; README documents pruning old volumes if upgrading.
