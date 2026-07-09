#!/usr/bin/env bash
set -euo pipefail

# Basic readiness check: ensure workspace is mounted and key docs exist.
if [[ ! -d "/workspace/docs" ]]; then
  echo "Workspace docs directory missing"
  exit 1
fi

if [[ ! -f "/workspace/docs/prd.md" ]]; then
  echo "PRD not found in workspace"
  exit 1
fi

echo "ok"
