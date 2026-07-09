#!/usr/bin/env bash
set -euo pipefail

# Lightweight helper to restart the jarvis-app services inside the container
# without touching Postgres/Qdrant/Redis.
#
# Usage (from repo root on host):
#   bash scripts/restart_jarvis_app.sh
#
# Requirements:
#   - docker daemon running
#   - jarvis-app container already created (e.g., via docker compose up)

CONTAINER_NAME="${JARVIS_APP_CONTAINER:-jarvis-app}"

echo "🔄 Restarting JARVIS app processes inside container: ${CONTAINER_NAME}"

docker exec "${CONTAINER_NAME}" bash -lc 'set -euo pipefail; \
  echo "  • Stopping existing uvicorn processes (if any)..."; \
  if command -v pkill >/dev/null 2>&1; then \
    pkill -f "uvicorn" || true; \
  else \
    echo "    pkill not available; existing processes will exit naturally."; \
  fi; \
  echo "  • Restarting services via jarvis-run-services..."; \
  cd /workspace && PYTHONPATH=/workspace/src jarvis-run-services >/workspace/jarvis-app.log 2>&1 & \
  echo "  • Restart command dispatched (check jarvis-app.log for details)."'

echo "✅ JARVIS app restart helper completed."

