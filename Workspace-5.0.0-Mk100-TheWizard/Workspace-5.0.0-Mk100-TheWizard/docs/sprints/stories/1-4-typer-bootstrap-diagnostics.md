# Story 1.4 – Typer Bootstrap & Diagnostics

## Summary
Ship a `jarvis doctor` CLI (Typer-based) that validates the Docker stack, database migrations, workspace mount, and vector store readiness before development workflows begin. This gives developers a single command to confirm environment health and surfaces actionable remediation steps.

## Source Links
- `docs/epics.md` → Epic 1, Story 1.4.
- PRD FR5.1/FR6.1 (CLI integration + health checks).
- Architecture §“Development Workflow” and §“Container Health Checks”.
- Test plan `docs/test-design-system.md` (G1 Gate requires `jarvis doctor`).

## Objectives
1. Provide a Typer app (`jarvis doctor`) that can be invoked via `python -m jarvis.cli.doctor`.  
2. Perform checks:
   - Docker Compose stack running (services healthy).  
   - PostgreSQL reachable with migrations applied.  
   - Qdrant HTTP endpoint responsive.  
   - Workspace mount present, `.jarvis/` writable.  
   - Optional: check `README` and story docs exist to ensure workspace alignment.  
3. Emit structured output (JSON or friendly console) plus exit codes (0=OK, non-zero on failures).  
4. Provide reusable check functions (unit-testable) independent of Typer.  
5. Document usage in README and story notes.  
6. Update sprint status: drafted → ready → review.

## Implementation Plan
1. **Scaffold CLI package**
   - `src/jarvis/cli/__init__.py`, `doctor_checks.py`, `doctor.py`.  
   - `doctor.py`: Typer app orchestrating checks and formatting results.  
   - `doctor_checks.py`: pure-Python helpers performing subprocess calls / fs checks; unit tests cover this module (no Typer dependency).  
2. **Checks implemented**
   - `check_docker_service(service)` using `docker compose ps --format json` (fallback to `docker compose ps`).  
   - `check_postgres()` verifying lock file existence or running `docker compose exec -T postgres pg_isready`.  
   - `check_qdrant()` via HTTP GET to `http://localhost:6333/readyz`.  
   - `check_workspace()` verifying `/workspace` mount, `.jarvis` write permissions, story docs presence.  
3. **Output**
   - Typer command prints table/JSON; on failure exit with status 1.  
   - Provide `--json` flag for automation.  
4. **Documentation**
   - README “Typer Bootstrap” instructions.  
   - Story notes capturing sample output and manual verification steps.  
5. **Testing**
   - `tests/cli/test_doctor_checks.py` mocking subprocess/HTTP responses.  
6. **Status update**
   - Move Story 1.4 to `review` once implementation + tests complete.

## Testing & Validation
- Unit tests for `doctor_checks` verifying success/failure handling using fakes.  
- Manual validation:  
  ```bash
  python -m jarvis.cli.doctor run
  python -m jarvis.cli.doctor run --json
  ```  
  Confirm exit codes and output reflect container state (bring down a service to simulate failure).

## Definition of Done
- Typer CLI command available + documented.  
- Checks cover Docker, Postgres, Qdrant, workspace mount.  
- Tests pass (`python3 -m unittest tests.cli.test_doctor_checks`).  
- Story file updated with implementation notes; sprint status set to `review`.

## Story Readiness Checklist
- [x] Dependencies: requires Stories 1.1–1.3 (compose, workspace, config).  
- [x] Implementation plan ready (Typer CLI + helper module).  
- [x] Risk mitigation: Typer dependency noted (pip install).  
- [x] Testing plan captured.

---

## Implementation Notes (Dev Story)

- Added CLI package with Typer entrypoint (`src/jarvis/cli/doctor.py`) and pure helper module (`doctor_checks.py`).  
- Helpers cover docker service checks, HTTP readiness, workspace write test, and compose file existence.  
- New tests (`tests/cli/test_doctor_checks.py`) mock subprocess + HTTP calls to validate logic (run via `python3 -m unittest tests.cli.test_doctor_checks`).  
- README updated with `jarvis doctor` usage instructions and Typer dependency note (install `typer[all]` on host).  
- Sprint status updated; story moves to `review`.
