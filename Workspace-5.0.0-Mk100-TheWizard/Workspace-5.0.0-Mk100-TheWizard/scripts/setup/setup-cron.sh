#!/bin/bash
# JARVIS Memory Enhancements - Cron Job Setup
#
# This script sets up automated daily/weekly tasks for JARVIS:
# - Daily: Capture domain/system snapshots (2 AM)
# - Weekly: Mine keywords for heuristic learning (Sunday 3 AM)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "JARVIS Cron Setup"
echo "=========================================="
echo ""

# Check if running inside container or on host
if [ -f "/.dockerenv" ]; then
    CONTEXT="container"
    PYTHON_CMD="cd /workspace && PYTHONPATH=/workspace/src python"
else
    CONTEXT="host"
    PYTHON_CMD="docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python'"
fi

echo "Context: $CONTEXT"
echo ""

# Generate cron entries
cat > /tmp/jarvis-cron-jobs.txt <<'EOF'
# JARVIS Memory Enhancements - Automated Tasks

# Daily: Catalog documents and refine domains (1 AM UTC)
0 1 * * * cd /workspace && PYTHONPATH=/workspace/src python -c 'from jarvis.memory.domain_catalog import catalog_documents; catalog_documents("knowledge")' >> /var/log/jarvis-catalog.log 2>&1

# Daily: Capture domain evolution snapshots (2 AM UTC)
0 2 * * * cd /workspace && PYTHONPATH=/workspace/src python -c 'from jarvis.analytics import capture_domain_snapshot, capture_system_snapshot; capture_domain_snapshot("knowledge"); capture_system_snapshot("knowledge")' >> /var/log/jarvis-snapshots.log 2>&1

# Weekly: Mine keywords from LLM classifications (Sunday 3 AM UTC)
0 3 * * 0 cd /workspace && PYTHONPATH=/workspace/src python -c 'from jarvis.memory.keyword_miner import mine_llm_classified_keywords, format_keyword_suggestions; suggestions = mine_llm_classified_keywords("knowledge", min_occurrences=10); print(format_keyword_suggestions(suggestions, top_domains=10))' >> /var/log/jarvis-keywords.log 2>&1

EOF

echo "Generated cron jobs:"
echo ""
cat /tmp/jarvis-cron-jobs.txt
echo ""
echo "=========================================="
echo ""

if [ "$CONTEXT" = "container" ]; then
    echo "Running inside container - Installing cron jobs..."

    # Install cron if not present
    if ! command -v crontab &> /dev/null; then
        echo "Installing cron..."
        apt-get update && apt-get install -y cron
    fi

    # Add to crontab
    (crontab -l 2>/dev/null || true; cat /tmp/jarvis-cron-jobs.txt) | crontab -

    # Start cron service
    service cron start || cron

    echo "✓ Cron jobs installed and cron service started"
    echo ""
    echo "View installed jobs:"
    echo "  crontab -l"
    echo ""
    echo "View logs:"
    echo "  tail -f /var/log/jarvis-snapshots.log"
    echo "  tail -f /var/log/jarvis-keywords.log"

else
    echo "Running on host - Manual installation required"
    echo ""
    echo "To install these cron jobs:"
    echo ""
    echo "1. Copy the jobs to container:"
    echo "   docker cp /tmp/jarvis-cron-jobs.txt jarvis-app:/tmp/"
    echo ""
    echo "2. Install cron in container:"
    echo "   docker exec jarvis-app bash -c 'apt-get update && apt-get install -y cron'"
    echo ""
    echo "3. Add to crontab:"
    echo "   docker exec jarvis-app bash -c '(crontab -l 2>/dev/null || true; cat /tmp/jarvis-cron-jobs.txt) | crontab -'"
    echo ""
    echo "4. Start cron service:"
    echo "   docker exec jarvis-app bash -c 'service cron start'"
    echo ""
    echo "Or run this script inside the container:"
    echo "   docker exec -it jarvis-app bash /workspace/scripts/setup-cron.sh"
fi

echo ""
echo "=========================================="
echo "Alternative: Use CLI commands directly"
echo "=========================================="
echo ""
echo "Instead of cron, you can run these commands manually or via your own scheduler:"
echo ""
echo "# Daily snapshot"
echo "cd /workspace && poetry run jarvis analytics snapshot"
echo ""
echo "# Weekly keyword mining"
echo "cd /workspace && poetry run jarvis analytics mine-keywords"
echo ""
echo "# Optional: Health monitoring daemon (runs continuously)"
echo "cd /workspace && poetry run jarvis health monitor --interval 15 --discord-webhook <url>"
echo ""

rm -f /tmp/jarvis-cron-jobs.txt
