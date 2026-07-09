#!/bin/bash
# JARVIS Production Integration Verification Script
#
# Tests all new CLI commands and verifies successful integration

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "JARVIS Production Integration Verification"
echo "=========================================="
echo ""

ERRORS=0

# Function to run command and check result
test_command() {
    local name=$1
    local cmd=$2
    local expect_success=${3:-true}

    echo -n "Testing: $name ... "

    if eval "$cmd" > /dev/null 2>&1; then
        if [ "$expect_success" = true ]; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗ (expected to fail but succeeded)${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    else
        if [ "$expect_success" = false ]; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    fi
}

echo "=== Testing CLI Module Registration ==="
echo ""

test_command "jarvis --help" "docker exec jarvis-app poetry run jarvis --help"
test_command "jarvis analytics --help" "docker exec jarvis-app poetry run jarvis analytics --help"
test_command "jarvis health --help" "docker exec jarvis-app poetry run jarvis health --help"
test_command "jarvis watch --help" "docker exec jarvis-app poetry run jarvis watch --help"

echo ""
echo "=== Testing New Analytics Commands ==="
echo ""

test_command "jarvis analytics init-snapshots --help" "docker exec jarvis-app poetry run jarvis analytics init-snapshots --help"
test_command "jarvis analytics snapshot --help" "docker exec jarvis-app poetry run jarvis analytics snapshot --help"
test_command "jarvis analytics growth --help" "docker exec jarvis-app poetry run jarvis analytics growth --help"
test_command "jarvis analytics mine-keywords --help" "docker exec jarvis-app poetry run jarvis analytics mine-keywords --help"
test_command "jarvis analytics enrichment-roi --help" "docker exec jarvis-app poetry run jarvis analytics enrichment-roi --help"
test_command "jarvis analytics enrichment-recommendations --help" "docker exec jarvis-app poetry run jarvis analytics enrichment-recommendations --help"

echo ""
echo "=== Testing Health Commands ==="
echo ""

test_command "jarvis health check --help" "docker exec jarvis-app poetry run jarvis health check --help"
test_command "jarvis health monitor --help" "docker exec jarvis-app poetry run jarvis health monitor --help"

echo ""
echo "=== Testing Watch Commands ==="
echo ""

test_command "jarvis watch start --help" "docker exec jarvis-app poetry run jarvis watch start --help"

echo ""
echo "=== Testing Dashboard Route ==="
echo ""

# Test dashboard API endpoint
echo -n "Testing: Dashboard API endpoint ... "
if docker exec jarvis-app curl -s -f http://localhost:8000/dashboard/api/stats > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ (API may not be running or route not registered)${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Test dashboard HTML endpoint
echo -n "Testing: Dashboard HTML endpoint ... "
if docker exec jarvis-app curl -s -f http://localhost:8000/dashboard/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ (API may not be running or route not registered)${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=== Testing Python Module Imports ==="
echo ""

test_command "Import analytics module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.analytics import create_snapshot_tables\"'"
test_command "Import monitoring module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.monitoring import HealthMonitor\"'"
test_command "Import keyword_miner module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.memory.keyword_miner import mine_llm_classified_keywords\"'"
test_command "Import enrichment_scorer module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.memory.enrichment_scorer import calculate_enrichment_roi\"'"
test_command "Import domain_relationships module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.memory.domain_relationships import get_related_domains\"'"
test_command "Import file_watcher module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.memory.file_watcher import start_file_watcher\"'"
test_command "Import dashboard module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.api.dashboard import router\"'"

echo ""
echo "=== Testing Watchdog Dependency ==="
echo ""

test_command "Watchdog installed" "docker exec jarvis-app bash -c 'python -c \"import watchdog\"'"

echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Integration is complete and working correctly."
    echo ""
    echo "Next steps:"
    echo "  1. Access dashboard: http://localhost:8000/dashboard/"
    echo "  2. Run: docker exec jarvis-app poetry run jarvis health check"
    echo "  3. Run: docker exec jarvis-app poetry run jarvis analytics snapshot"
    echo "  4. Set up cron: docker exec -it jarvis-app bash /workspace/scripts/setup-cron.sh"
else
    echo -e "${YELLOW}⚠ $ERRORS test(s) failed${NC}"
    echo ""
    echo "Some components may need attention."
    echo "Check the errors above and consult docs/PRODUCTION-INTEGRATION-COMPLETE.md"
fi

echo ""
exit $ERRORS
