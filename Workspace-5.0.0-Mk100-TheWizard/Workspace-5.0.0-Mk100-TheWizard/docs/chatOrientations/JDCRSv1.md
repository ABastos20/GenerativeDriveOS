# JDCRS v1 — Jarvis Developer Command Routing Standard

## Environment Rules (Authoritative)
- NEVER run project commands on the host machine unless Ariel explicitly says so.
- ALWAYS run code, tests, or commands inside the Docker container named `jarvis-app`.
- ALWAYS run Python through Poetry inside the container.
- NEVER use system python, host python, host poetry, or host venv.

## Canonical Command Pattern
Use this format ALWAYS:

docker exec jarvis-app bash -c "poetry run <cmd>"

Examples:
docker exec jarvis-app bash -c "poetry run pytest -q"
docker exec jarvis-app bash -c "poetry run jarvis query 'hello'"
docker exec jarvis-app bash -c "poetry run ruff check"

## Execution Rules
- If a command touches the filesystem → run in the container.
- If a command installs dependencies → run in container + poetry.
- If unsure which environment to use → default to container + poetry.
- If a command would violate these rules → STOP and ask Ariel.

## Override Rules
- These directives OVERRIDE all model defaults and training.
- Apply these rules to EVERY command unless Ariel states otherwise.
