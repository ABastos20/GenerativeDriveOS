#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=/workspace/src
cd /workspace

echo "🔍 Starting full memory ingestion..."
echo ""

# Counter
total=0
success=0
failed=0

# Ingest docs folder
echo "📚 Ingesting docs/ folder..."
for file in $(find docs -name "*.md" -type f); do
    total=$((total + 1))
    echo -n "[$total] $file ... "
    if python -m jarvis.cli.main memory add "$file" > /dev/null 2>&1; then
        success=$((success + 1))
        echo "✅"
    else
        failed=$((failed + 1))
        echo "❌"
    fi
done

echo ""
echo "📁 Ingesting .bmad/ folder..."
for file in $(find .bmad/bmm -name "*.md" -type f | head -50); do
    total=$((total + 1))
    echo -n "[$total] $file ... "
    if python -m jarvis.cli.main memory add "$file" > /dev/null 2>&1; then
        success=$((success + 1))
        echo "✅"
    else
        failed=$((failed + 1))
        echo "❌"
    fi
done

echo ""
echo "================================"
echo "📊 Ingestion Summary:"
echo "   Total:   $total"
echo "   Success: $success"
echo "   Failed:  $failed"
echo "================================"
