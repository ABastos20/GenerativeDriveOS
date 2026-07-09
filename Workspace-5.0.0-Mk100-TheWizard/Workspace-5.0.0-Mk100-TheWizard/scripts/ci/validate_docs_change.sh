#!/usr/bin/env bash
# Utility script used by CI and local hooks to check for infra/API changes without docs updates.
set -euo pipefail

BASE=${1:-FETCH_HEAD}
HEAD=${2:-HEAD}

DIFF_FILES=$(git diff --name-only "$BASE"..."$HEAD")

infra_patterns='^docker/|^alembic/|^src/.*/api/|^src/.*/migrations|^docker/|Dockerfile|docker-compose.yml'
docs_patterns='^docs/|^README_BMAD.md|^README.md|^docs/agent-'

infra_changed=false
docs_changed=false

while IFS= read -r f; do
  if [[ $f =~ $infra_patterns ]]; then
    infra_changed=true
  fi
  if [[ $f =~ $docs_patterns ]]; then
    docs_changed=true
  fi
done <<< "$DIFF_FILES"

echo "infra_changed=$infra_changed, docs_changed=$docs_changed"

if [ "$infra_changed" = true ] && [ "$docs_changed" = false ]; then
  echo "ERROR: infra/API changes detected without docs updates."
  exit 1
fi

echo "Docs validation passed."
