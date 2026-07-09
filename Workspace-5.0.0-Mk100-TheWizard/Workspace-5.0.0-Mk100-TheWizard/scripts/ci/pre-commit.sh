#!/bin/sh
# Pre-commit hook to run Jarvis Linter
# Usage: ./scripts/pre-commit.sh

echo "🔍 Running Jarvis Code Quality Linter..."
python scripts/lint_check.py src

if [ $? -ne 0 ]; then
    echo "❌ Lint check failed. Please fix violations before committing."
    exit 1
fi

echo "✅ Lint check passed."
exit 0
