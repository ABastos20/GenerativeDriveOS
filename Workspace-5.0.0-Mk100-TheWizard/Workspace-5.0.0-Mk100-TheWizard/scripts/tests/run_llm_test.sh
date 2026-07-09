#!/usr/bin/env bash
set -euo pipefail

# Load .env file
if [ -f /workspace/.env ]; then
    export $(grep -v '^#' /workspace/.env | xargs)
fi

# Run the test
python /workspace/scripts/test_llm_free.py
