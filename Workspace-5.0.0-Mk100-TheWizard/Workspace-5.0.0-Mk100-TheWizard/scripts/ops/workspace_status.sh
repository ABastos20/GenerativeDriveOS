#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT}"

echo "== Workspace Status =="
echo

echo "Git:"
echo "  Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
echo

echo "Epic 3 Stories:"
grep -E 'epic-3:|3-1-query-command-response-envelope:|3-2-hybrid-retrieval-toggle:|3-3-query-expansion-multi-query-fusion:|3-4-citation-first-response-formatting:' docs/sprints/sprint-status.yaml || echo "  (epic-3 entries not found)"
echo

echo "Docker Compose:"
docker compose -f docker/docker-compose.yml ps || echo "  docker compose ps failed"
echo

echo "BMAD/BMM:"
if [ -f ".bmad/bmm/config.yaml" ]; then
  echo "  BMM config:"
  sed -n '1,6p' .bmad/bmm/config.yaml
else
  echo "  .bmad/bmm/config.yaml not found"
fi

