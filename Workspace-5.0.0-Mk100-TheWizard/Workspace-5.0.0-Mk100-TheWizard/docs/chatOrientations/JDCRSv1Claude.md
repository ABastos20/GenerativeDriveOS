# JDCRS for Claude

All commands MUST run inside the Docker container using Poetry.

MANDATORY format:
docker exec jarvis-app bash -c "poetry run <cmd>"

Never run `python`, `pytest`, `poetry`, or any project command on the host.
Never assume host venv.

If you produce a command, APPLY the above format automatically.
If it violates environment rules, DO NOT run — fix it.

Default behaviour = container + poetry.
