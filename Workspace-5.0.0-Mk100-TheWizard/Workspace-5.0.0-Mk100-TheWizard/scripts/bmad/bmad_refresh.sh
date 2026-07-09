#!/usr/bin/env bash
set -euo pipefail

# Reload key BMAD/BMM docs into the current shell/IDE context.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

echo "== BMAD / BMM Refresh =="
echo

if [ -f ".bmad/bmm/README.md" ]; then
  echo "# .bmad/bmm/README.md"
  sed -n '1,80p' .bmad/bmm/README.md
  echo
fi

if [ -f ".bmad/bmm/docs/README.md" ]; then
  echo "# .bmad/bmm/docs/README.md"
  sed -n '1,80p' .bmad/bmm/docs/README.md
  echo
fi

if [ -f ".bmad/quick-reference.md" ]; then
  echo "# .bmad/quick-reference.md"
  sed -n '1,120p' .bmad/quick-reference.md
  echo
fi

