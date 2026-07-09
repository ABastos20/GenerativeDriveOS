# Repository Guidelines

## Project Structure & Module Organization
- Source lives under `src/jarvis/` (CLI in `cli/`, FastAPI in `api/`, memory + LLM logic in `memory/` and `llm/`, database config in `database/`).
- Tests mirror the tree in `tests/` (`unit/`, `integration/`, `cli/`, `config/`, `workspace/`), using `test_*.py` naming.
- Infra and scripts: `docker/` for compose stack and service configs, `scripts/` for setup/ingestion helpers, `config/settings.example.yaml` for runtime defaults, and `docs/` for PRD, architecture, and sprint plans.

## Build, Test, and Development Commands
- `poetry install --with dev` – install runtime + tooling (Python 3.13).
- `poetry run jarvis --help` – view Typer CLI entrypoints; run subcommands from repo root.
- `poetry run uvicorn src.jarvis.api.app:app --reload --port 8000` – start the API locally.
- `docker compose -f docker/docker-compose.yml up --build -d` – bring up app + Postgres + Qdrant + Redis; use `down -v` to reset volumes.
- `poetry run pytest` – run all tests; add `-m "not integration"` to skip services.
- `poetry run ruff check .`, `poetry run black .`, `poetry run mypy src` – lint/format/type-check gate.

## Coding Style & Naming Conventions
- Python: Black-formatted, 100-char lines; Ruff enforces pyflakes/bugbear/isort/pyupgrade; mypy requires typed defs (`disallow_untyped_defs = true`).
- Prefer snake_case for functions/vars, PascalCase for classes, UPPER_SNAKE for constants.
- Use structured logging via `structlog` and reuse helpers under `jarvis/core` where available.
- Place new configs in `config/settings.yaml` shape (JSON-valid YAML) and load via `jarvis.config.load_settings`.

## Testing Guidelines
- Framework: pytest with `--strict-markers`, coverage via `--cov=jarvis --cov-report=term-missing`; expectation is no unexpected missing lines.
- Mark slow/external checks with `@pytest.mark.integration` or `@pytest.mark.slow`; default runs should pass without containers.
- Mirror module paths in `tests/`, favor fixtures over global state, and add regression cases with feature changes.

## Commit & Pull Request Guidelines
- Commit messages follow short, imperative subjects (e.g., `Add scheduled memory compilation scaffolding`); keep scope focused per commit.
- PRs should include: behavior summary, linked issue/story, test evidence (`pytest` output or integration notes), and screenshots/log snippets for API/CLI changes when relevant.
- Keep diffs small and documented: call out config/schema changes, migrations, or new env vars in the description.

## Configuration & Security
- Copy `config/settings.example.yaml` to `config/settings.yaml` and `.env.example` to `.env` for secrets; never commit populated secrets.
- Set host UID/GID when using Docker on Linux (`HOST_UID=$(id -u) HOST_GID=$(id -g)`) to align file ownership.
- Run `gitleaks-bin detect --source .` before publishing if adding credentials-adjacent files.
