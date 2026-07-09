# Story 1.3 – Configuration & Secret Management

## Summary
Provide a typed configuration system so JARVIS loads project/workspace/provider metadata from YAML (JSON syntax) plus `.env` secrets. This ensures secrets stay outside git, runtime settings are validated, and downstream stories can rely on consistent `Settings` objects when bootstrapping CLI commands or services.

## Source Links
- `docs/epics.md` → Epic 1, Story 1.3.
- PRD FR5.3 (“Configuration Management”) and FR6 (CLI automation expects structured config).
- Architecture decisions (§Configuration) calling for YAML + pydantic-style validation and `.env` secrets.

## Objectives
1. Deliver a `config/settings.example.yaml` template and ignore the real `config/settings.yaml`.  
2. Implement a lightweight settings loader (standard library only) that reads JSON-compatible YAML + `.env`, exposes typed objects, and supports environment overrides.  
3. Ensure provider entries reference env variables for API keys (no secrets inside config).  
4. Document the workflow in README and story notes.  
5. Provide unit tests for configuration parsing + env override logic.  
6. Update sprint status (Story 1.3) through drafted → ready → review.

## Detailed Requirements
- `.gitignore` must exclude `.env` and `config/settings.yaml`.  
- Config template should include project metadata, workspace paths, and at least two provider definitions referencing env var names.  
- Loader should accept custom paths, default to `config/settings.yaml`, and fallback to the example file while warning (for dev convenience).  
- `.env` loader reads simple `KEY=VALUE` lines (# comments allowed) without extra dependencies.  
- Provide helper methods: e.g., `ProviderConfig.api_key()` to fetch runtime secret.  
- Support overrides via env variables (`WORKSPACE_ROOT`, `WORKSPACE_PRIVATE_DIR`).  
- Tests cover env fallback/override behavior and provider secret retrieval.

## Implementation Plan
1. **Scaffold artifacts**
   - Create `.gitignore` entries for `.env`, `config/settings.yaml`, `__pycache__/`.  
   - Add `config/settings.example.yaml` (JSON syntax).  
2. **Settings loader**
   - Module path: `src/jarvis/config/settings.py` + `__init__.py`.  
   - Data classes: `ProviderConfig`, `WorkspaceConfig`, `Settings` with helper methods.  
   - Implement `_load_dotenv`, `_load_json_like`, and `load_settings`.  
3. **Tests**
   - `tests/config/test_settings.py` with temporary directories verifying `.env` parsing and env overrides.  
4. **Documentation**
   - README “Configuration & Secrets” section.  
   - Story notes capturing verification steps.  
5. **Status updates**
   - Mark story drafted after plan, ready when dependencies resolved, review after implementation/testing.

## Testing & Validation
- `python3 -m unittest tests/config/test_settings.py`.  
- Manual verification checklist:  
  - Copy `config/settings.example.yaml` to `config/settings.yaml`.  
  - Populate `.env` with fake provider keys.  
  - Run a short Python REPL snippet:
    ```python
    from jarvis.config import load_settings
    settings = load_settings()
    print(settings.to_dict())
    ```
    Ensure workspace paths + provider metadata match config and secrets are read from env.

## Definition of Done
- Template + ignore rules committed.  
- Config loader + tests passing (only standard library).  
- README/Story updated with instructions + verification steps.  
- Story status advanced to `review`.

## Story Readiness Checklist
- [x] Dependencies identified (relies on Stories 1.1 & 1.2).  
- [x] Implementation approach defined (JSON-compatible YAML, dataclasses).  
- [x] Testing strategy defined.  
- [x] Risks logged (no third-party dependencies, fallback behavior).

---

## Implementation Notes (Dev Story)

- Added `.gitignore` to cover `.env`, `config/settings.yaml`, and caches.  
- Introduced `config/settings.example.yaml` (JSON syntax valid YAML) describing project/workspace/provider defaults; developers copy to `config/settings.yaml`.  
- Implemented `src/jarvis/config/settings.py` with dataclasses + helper functions (dotenv parsing, env overrides, JSON loader) plus re-exports in `__init__.py`.  
- Added `tests/config/test_settings.py` verifying `.env` parsing, env overrides, and provider secret resolution (via `python3 -m unittest tests/config/test_settings.py`).  
- README updated with “Configuration & Secrets” instructions; story status moved to `review`.
