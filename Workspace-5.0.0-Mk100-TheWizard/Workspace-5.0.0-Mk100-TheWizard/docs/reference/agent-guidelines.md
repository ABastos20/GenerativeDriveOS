# Agent Guidelines (BMAD Multi-Agent Cooperation)

This file provides a concise, machine- and agent-friendly checklist for any automated agent or tool that will make changes in this repository.

1. Announce intent
   - Create an issue or draft PR titled `agent/<agent-name>: intent - short summary` describing exactly which files will be modified and why.

2. Documentation-first
   - Update or add documentation in `docs/` describing the behavioral change, runbook steps, and any new environment variables.
   - Include a short `Operational Impact` section that lists runtime behaviors (ports, endpoints, migrations).

3. Migrations & infra changes
   - For DB extension or schema changes, add an Alembic revision and include a `CREATE EXTENSION IF NOT EXISTS ...` step if needed.
   - Do not attempt to create DB extensions on managed services without explicit permission. Document privilege requirements.

4. Secrets
   - Never write secret values into files. If the agent needs to test with secrets, use the environment and a temporary secret store; record only the environment variable names in the docs.

5. Health checks
   - Add or update health endpoints for new services and document the health signal semantics.

6. Single-writer coordination
   - If multiple agents may change the same file (docker-compose, entrypoint, config templates), coordinate via the issue/PR; one agent should be assigned as the owner for the merge.

7. Tests & CI
   - Add unit tests and, if applicable, a lightweight integration test that can run in CI. Update `README_BMAD.md` with the CI expectation.

8. Cleanup
   - Move dev utilities to `dev/` and add `.gitignore` entries for ephemeral files. Leave a note in docs about dev utilities.

9. Jarvis Core Docs
   - When changing high-level behavior, architecture, or long-term strategy, consult:
     - `docs/jarvis/persona.md`
     - `docs/jarvis/operating-manual.md`
     - Relevant files under `docs/jarvis/playbooks/`
   - Keep these docs in sync with any major behavioral change you introduce.

Failure mode: If an agent cannot comply (e.g., lacks permission to create an Alembic migration or cannot access secrets), it must file the issue and stop.

These guidelines are intentionally short and prescriptive to make programmatic enforcement easy for other agents. Agents should reference `docs/agent-coordination.md` and `README_BMAD.md` for broader operational context.
