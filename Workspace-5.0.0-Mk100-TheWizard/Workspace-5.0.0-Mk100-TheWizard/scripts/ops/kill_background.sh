#!/usr/bin/env bash
set -euo pipefail

# Kill common long-running background processes (e.g. docker builds) for this repo.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

echo "== Killing background docker build / compose processes for this workspace =="

PIDS=$(ps aux | grep -E "docker (build|compose)" | grep -v grep | awk '{print $2}')

if [ -z "${PIDS}" ]; then
  echo "No docker build/compose processes found."
  exit 0
fi

echo "Found PIDs: ${PIDS}"
kill ${PIDS} || true

echo "Sent SIGTERM to background docker build/compose processes."

