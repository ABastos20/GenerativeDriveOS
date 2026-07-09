# Story 1.2 – Workspace Mount & File Access Controls

## Summary
Guarantee the Dockerized JARVIS instance can safely read and write the host workspace. This includes tightening the Compose volume configuration, enforcing `.gitignore`-aware ingestion, and ensuring all outbound writes land under `.jarvis/` with correct host permissions. With this in place, subsequent stories (config management, diagnostics) can trust that the container sees exactly what the developer sees—no more, no less.

## Source Links
- Epic reference: `docs/epics.md` → Epic 1, Story 1.2.
- PRD FR5.2 (“Workspace Connectivity”) & FR6 (CLI integration).
- Architecture §“Docker Workspace Mounting” (container mounts `./` → `/workspace`, respects `.gitignore`).
- Test plan `docs/test-design-system.md` (Controllability + Security criteria for mounts).

## Objectives
1. Ensure the Compose stack mounts the repo into `/workspace` with performance-friendly flags (`:cached` on macOS/Windows).  
2. Provide a workspace abstraction inside the app (e.g., `src/jarvis/filesystem/workspace.py`) that:  
   - Resolves real host paths.  
   - Honors `.gitignore`, `.dockerignore`, and optional allowlist/denylist.  
   - Offers read/write helpers pointing to `.jarvis/` for generated assets/logs.  
3. Set ownership/permissions so files written inside the container remain editable on the host (UID/GID passthrough or `chown` logic).  
4. Document the mount behavior and developer expectations (no secrets outside `.jarvis/`, how to override paths, troubleshooting on Windows).  
5. Provide verification commands/tests proving ingestion ignores ignored files and `.jarvis/` outputs are accessible.

## Detailed Requirements
- **Volume definition:** Keep `../:/workspace:cached` (or `:delegated` on macOS) and ensure `.git` metadata is accessible (needed for Story 6.2).  
- **Ignore handling:** Implement a parser using `.gitignore` + optional `.jarvisignore` semantics (gitwildmatch) so ingestion helpers skip restricted files. Provide CLI/SDK call `workspace.iter_documents()` returning only ingestable files.  
- **Write isolation:** All auto-generated content (logs, status files, embeddings, BMAD transcripts) goes under `/workspace/.jarvis/…`. Guard against accidental writes outside this subtree.  
- **Permissions:** On Linux, detect host UID/GID (via env or `stat`) and run jarvis process as that user to avoid root-owned files. On Windows, document the requirement for `git config core.autocrlf` and verify `:cached` works.  
- **Security:** Block traversal outside workspace root; sanitize ingestion paths to prevent `../` escapes.  
- **Observability:** Add structured log entries when ingestion skips a file because it’s ignored or denied.

## Deliverables
1. Workspace helper module + unit tests validating ignore logic and safe writes.  
2. Updated Compose or entrypoint script that sets UID/GID environment variables when available.  
3. Documentation updates (README + story notes) describing mount usage and troubleshooting.  
4. Demo commands (e.g., `docker compose exec jarvis ls /workspace` and a sample ingestion run) recorded in story notes.  
5. Sprint status update with this story set to `drafted`.

## Implementation Plan
1. **Finalize Compose mount semantics**
   - Confirm `docker/docker-compose.yml` uses the correct flags.
   - Add optional env overrides `WORKSPACE_HOST_PATH`, `WORKSPACE_CONTAINER_PATH`.
2. **Implement workspace abstraction**
   - Create `src/jarvis/workspace/__init__.py` (or similar) providing `Workspace` class.  
   - Class loads `.gitignore` + `.jarvisignore` patterns (gitwildmatch-style).  
   - Expose methods: `list_ingestable_files()`, `open_managed(path)`, `write_private(relative_path, data)`.
3. **Permission handling**
   - Add entrypoint script to detect host UID via env (e.g., `HOST_UID`) and `chown` `.jarvis/` before application start.  
   - Document instructions for Windows where UID mapping isn’t required.
4. **Logging & validation**
   - When files are skipped or written, emit structlog entries with reason.  
   - Add unit tests to `tests/workspace/test_workspace.py` verifying ignore patterns and safe writes.  
   - Provide manual test procedure (touch an ignored file, confirm it’s skipped).
5. **Docs & story updates**
   - README “Running the Docker Stack” → mention `.jarvis/` output folder and ignore behavior.  
   - Append verification steps + evidence to this story file.

## Testing & Validation
- Unit tests covering ignore patterns, path normalization, and `.jarvis/` writes (use temp directories).  
- Manual check:  
  ```bash
  docker compose exec jarvis bash -lc "printf 'secret' > /workspace/tmp.secret && jarvis workspace ingest"
  # Expected: log states file skipped due to .gitignore
  docker compose exec jarvis bash -lc "ls -la /workspace/.jarvis"
  ```
- Ensure `docker compose exec jarvis stat /workspace/.jarvis` shows host-accessible permissions (e.g., UID/GID 1000).  
- Validate Windows host can still edit files produced inside container.

## Definition of Done
- Workspace mount stable across OSes with documented flags and env overrides.  
- Application-level workspace helper delivered with tests and integrated into ingestion pipeline.  
- `.gitignore` (and potential `.jarvisignore`) fully respected; no accidental ingestion of secrets.  
- `.jarvis/` is the only write target for generated assets, with permissions matching host user.  
- README + story notes updated; sprint status reflects draft completion.

## Story Readiness Checklist
- [x] Dependencies clarified (needs Story 1.1 Compose stack, upcoming Story 1.3 config).  
- [x] Implementation plan reviewed with architecture + test strategy.  
- [x] Risk mitigations captured (permissions, Windows mount perf).  
- [x] Blockers resolved prior to moving to `ready-for-dev`.

---

## Implementation Notes (Dev Story)

- Added `src/jarvis/workspace/workspace.py` + `__init__.py` exposing a Workspace abstraction with gitwildmatch-style ignore handling, path normalization, `.jarvis/` writes, and host UID detection helpers.  
- Created `tests/workspace/test_workspace.py` (unittest) covering ignore logic, private writes, and path traversal guards (ran via `python3 -m unittest tests/workspace/test_workspace.py`).  
- Introduced `docker/scripts/entrypoint.sh` (gosu-based) so container processes run as host UID/GID when `HOST_UID/HOST_GID` are provided; Dockerfile now installs gosu and sets entrypoint.  
- README updated with UID/GID instructions; Compose instructions already highlight `.jarvis` volume behavior.  
- Workspace helper currently logs skip events; ingestion layers can adopt `Workspace.iter_ingestable_files()` to ensure `.gitignore`/`.jarvisignore` compliance.
