# Contributing — BMAD Multi-Agent Projects

This repository follows the BMAD method and is developed by a combination of human engineers and automated agents. The goal of this document is to make it explicit how contributors (including automated agents) should coordinate changes to avoid conflicts and maintain operational safety.

How agents and humans should work together

- Announce intent before changing important files:
  - Create an issue or draft PR titled `agent/<agent-name>: intent - short summary` describing which files will change and why.
  - Include a short `Operational Impact` section describing runtime effects (ports, endpoints, migrations, required env vars).

- Documentation-first:
  - When making infra or API changes, update docs in `docs/` and `README_BMAD.md` alongside code changes. The repository contains CI and local hooks that enforce this.

- Secrets policy:
  - Never commit secret values. Use environment variables, CI secret stores, or a vault. Document the environment variable names in docs (never values).

- Migrations & DB extensions:
  - Add Alembic revisions for schema changes. If your migration needs `pgcrypto`, include `CREATE EXTENSION IF NOT EXISTS pgcrypto;` in the migration.
  - Coordinate DB extension creation with the platform team if running on managed DBs.

- Health checks & observability:
  - Add or update health endpoints for new services and document the semantics in `docs/agent-coordination.md`.

- Single-writer coordination for critical files:
  - For `docker/docker-compose.yml`, `docker/Dockerfile.*`, `alembic/versions/*`, and other operational files, coordinate by assigning an owner in an issue or PR to avoid conflicting changes.

- Tests & CI:
  - Add unit tests for logic changes and lightweight integration tests for infra changes. CI contains a `CI Smoke` job that runs the docs guard, applies migrations to a ephemeral Postgres service, and validates `/mcp/health`.

Local setup for maintainers

- Enable local pre-commit docs guard (optional):
  - `git config core.hooksPath .githooks`
  - The pre-commit hook checks staged infra/API changes for matching docs updates.

If an automated agent cannot proceed (lacks privileges, secrets, or cannot complete migrations), the agent must create an issue describing the blocker and not push changes.

Thank you for following these rules — they keep a multi-agent, multi-tool project safe and auditable.
