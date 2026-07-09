#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=/workspace/src

echo "🔧 Pre-warming embedding model for memory search..."
python - << 'EOF' >/dev/null 2>&1 || true
from sentence_transformers import SentenceTransformer

# Load the default embedding model so the first query is fast.
SentenceTransformer("all-MiniLM-L6-v2")
EOF

uvicorn src.jarvis.api.app:app --host 0.0.0.0 --port 8000 --log-level info &
API_PID=$!

uvicorn src.jarvis.mcp_server:app --host 0.0.0.0 --port 8001 --log-level info &
MCP_PID=$!

wait -n "$API_PID" "$MCP_PID"
exit $?
