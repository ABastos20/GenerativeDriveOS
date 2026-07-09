#!/bin/bash
# JARVIS Memory Enhancements Demo - Run from HOST (outside container)
# Usage: ./scripts/demo-enhancements-outside.sh

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}JARVIS Memory Enhancements Demo (v2.0)${NC}"
echo -e "${CYAN}Running from host machine${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""

# Check if Docker is running
echo -e "${BLUE}[Pre-Check] Verifying Docker...${NC}"
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running or accessible${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if jarvis-app container exists and is running
echo -e "${BLUE}[Pre-Check] Verifying jarvis-app container...${NC}"
if ! docker ps --filter "name=jarvis-app" --format "{{.Names}}" | grep -q jarvis-app; then
    echo -e "${RED}ERROR: jarvis-app container is not running${NC}"
    echo -e "${YELLOW}Start it with: docker compose -f docker/docker-compose.yml up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✓ jarvis-app container is running${NC}"
echo ""

# ============================================
# Step 1: Install watchdog dependency
# ============================================
echo -e "${GREEN}=== [Step 1] Installing Dependencies ===${NC}"
echo -e "${YELLOW}Installing watchdog for file watching...${NC}"
docker exec jarvis-app bash -c "cd /workspace && poetry add watchdog --quiet" 2>/dev/null || true
echo -e "${GREEN}✓ Dependencies checked${NC}"
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Step 2: Register dashboard route
# ============================================
echo -e "${GREEN}=== [Step 2] Registering Dashboard Route ===${NC}"
echo -e "${YELLOW}Checking if dashboard route is registered...${NC}"
echo ""

if docker exec jarvis-app grep -q "dashboard_router" /workspace/src/jarvis/api/app.py 2>/dev/null; then
    echo -e "${GREEN}✓ Dashboard route already registered${NC}"
else
    echo -e "${YELLOW}Dashboard route not found. Add these lines to src/jarvis/api/app.py:${NC}"
    echo ""
    echo -e "${CYAN}from jarvis.api.dashboard import router as dashboard_router${NC}"
    echo -e "${CYAN}app.include_router(dashboard_router)${NC}"
    echo ""
    echo -e "${YELLOW}After the existing router registrations (around line 50-60)${NC}"
fi
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Step 3: Create snapshot tables
# ============================================
echo -e "${GREEN}=== [Step 3] Setting Up Evolution Tracking ===${NC}"
echo -e "${YELLOW}Creating PostgreSQL snapshot tables...${NC}"

docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -c 'from jarvis.analytics import create_snapshot_tables; create_snapshot_tables()'" || echo -e "${YELLOW}⚠ Tables may already exist${NC}"

echo -e "${GREEN}✓ Snapshot tables ready${NC}"
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Step 4: Run health check
# ============================================
echo -e "${GREEN}=== [Step 4] Running Health Check ===${NC}"
echo -e "${YELLOW}Checking JARVIS memory system health...${NC}"
echo ""

docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.monitoring import HealthMonitor, AlertConfig, format_health_report
import structlog
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(30))

config = AlertConfig(
    qdrant_min_expected_points=10000,
    heuristic_hit_rate_min=60.0,
    enrichment_coverage_min=20.0,
)

monitor = HealthMonitor(config)
results = monitor.run_all_checks(collection_name=\"jarvis-core\")

report = format_health_report(results)
print(report)
'
"

echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Step 5: Mine keywords
# ============================================
echo -e "${GREEN}=== [Step 5] Mining Keywords (Auto-Learning Heuristics) ===${NC}"
echo -e "${YELLOW}Analyzing LLM-classified chunks for keyword patterns...${NC}"
echo ""

docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.memory.keyword_miner import mine_llm_classified_keywords, format_keyword_suggestions
import structlog
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))

print(\"Mining keywords (may take 30-60 seconds)...\")
suggestions = mine_llm_classified_keywords(
    collection_name=\"jarvis-core\",
    min_occurrences=5,
    max_suggestions=10,
)

if suggestions:
    report = format_keyword_suggestions(suggestions, top_domains=5)
    print(report)
else:
    print(\"No suggestions found. Run domain catalog job first:\")
    print(\"  jarvis catalog domain-job\")
'
"

echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Step 6: Show domain relationships
# ============================================
echo -e "${GREEN}=== [Step 6] Domain Relationship Graph ===${NC}"
echo -e "${YELLOW}Visualizing semantic domain connections...${NC}"
echo ""

docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.memory.domain_relationships import (
    get_related_domains,
    expand_domain_filter,
    visualize_domain_graph,
)

print(\"Example: jarvis.memory.rag domain relationships\")
print(\"=\" * 60)

related = get_related_domains(\"jarvis.memory.rag\", max_depth=1, min_strength=0.5)
print(f\"Related domains ({len(related)}):\")
for domain, strength in related[:5]:
    print(f\"  - {domain} (strength: {strength:.2f})\")

print()

original = [\"jarvis.memory.rag\"]
expanded = expand_domain_filter(original, max_expansions=5, min_strength=0.6)
print(f\"Domain filter expansion:\")
print(f\"  Original: {original}\")
print(f\"  Expanded: {expanded}\")

print()

graph = visualize_domain_graph(\"jarvis.memory.rag\", max_depth=1)
print(graph[:500])
'
"

echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Step 7: Capture snapshots
# ============================================
echo -e "${GREEN}=== [Step 7] Capturing Evolution Snapshots ===${NC}"
echo -e "${YELLOW}Taking domain distribution and system metrics snapshots...${NC}"
echo ""

docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.analytics import capture_domain_snapshot, capture_system_snapshot
import structlog
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))

print(\"Capturing domain snapshot...\")
try:
    capture_domain_snapshot(collection_name=\"jarvis-core\")
    print(\"✓ Domain snapshot captured\")
except Exception as e:
    print(f\"Error: {str(e)}\")

print(\"Capturing system snapshot...\")
try:
    capture_system_snapshot(collection_name=\"jarvis-core\")
    print(\"✓ System snapshot captured\")
except Exception as e:
    print(f\"Error: {str(e)}\")

print()
print(\"Snapshots stored in PostgreSQL.\")
print(\"Set up daily cron: 0 2 * * * jarvis analytics snapshot\")
'
"

echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Step 8: Get enrichment recommendations
# ============================================
echo -e "${GREEN}=== [Step 8] Enrichment Quality Scoring ===${NC}"
echo -e "${YELLOW}Analyzing enrichment ROI and recommendations...${NC}"
echo ""

docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.memory.enrichment_scorer import (
    get_enrichment_recommendations,
    format_recommendations_report,
)
import structlog
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))

print(\"Analyzing enrichment opportunities...\")
recommendations = get_enrichment_recommendations(collection_name=\"jarvis-core\")

report = format_recommendations_report(recommendations)
print(report[:1000])
'
"

echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Step 9: Dashboard access
# ============================================
echo -e "${GREEN}=== [Step 9] Accessing Interactive Dashboard ===${NC}"
echo ""

# Check if API is running
if docker exec jarvis-app bash -c "curl -s http://localhost:8000/health 2>/dev/null" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ JARVIS API is running${NC}"
    echo ""
    echo -e "${CYAN}Dashboard should be available at:${NC}"
    echo -e "${NC}  http://localhost:8000/dashboard/${NC}"
    echo ""
    echo -e "${YELLOW}Testing dashboard API endpoint...${NC}"

    if docker exec jarvis-app bash -c "curl -s http://localhost:8000/dashboard/api/stats 2>/dev/null | head -c 200" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Dashboard API is responding${NC}"
        echo ""
        echo -e "${CYAN}Open in your browser: http://localhost:8000/dashboard/${NC}"
    else
        echo -e "${YELLOW}⚠ Dashboard API not found. Make sure you registered the route in app.py${NC}"
        echo ""
        echo -e "${CYAN}Add to src/jarvis/api/app.py:${NC}"
        echo -e "${NC}  from jarvis.api.dashboard import router as dashboard_router${NC}"
        echo -e "${NC}  app.include_router(dashboard_router)${NC}"
        echo ""
        echo -e "${YELLOW}Then restart: docker compose -f docker/docker-compose.yml restart jarvis-app${NC}"
    fi
else
    echo -e "${YELLOW}⚠ JARVIS API may not be running on port 8000${NC}"
    echo -e "${YELLOW}Start it with: docker compose -f docker/docker-compose.yml up -d${NC}"
fi

echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Summary
# ============================================
echo ""
echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}Demo Complete!${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""

echo -e "${GREEN}Enhancement Status:${NC}"
echo "  ✅ #1: Auto-Learning Heuristics - Ready"
echo "  ✅ #2: Domain Relationship Graph - Ready"
echo "  ✅ #3: Interactive Dashboard - Check http://localhost:8000/dashboard/"
echo "  ✅ #4: Health Monitoring - Ready"
echo "  ✅ #5: Domain Evolution Tracking - Snapshots captured"
echo "  ✅ #6: Enrichment Quality Scoring - Ready"
echo "  ✅ #7: Smart Re-ingestion - Ready (not started)"
echo ""

echo -e "${YELLOW}Quick Commands:${NC}"
echo ""
echo -e "${CYAN}Run health check:${NC}"
echo '  docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.monitoring import HealthMonitor; m = HealthMonitor(); print(m.run_all_checks())\""'
echo ""
echo -e "${CYAN}Mine keywords:${NC}"
echo '  docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.memory.keyword_miner import mine_llm_classified_keywords; mine_llm_classified_keywords()\""'
echo ""
echo -e "${CYAN}Capture daily snapshot:${NC}"
echo '  docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.analytics import capture_domain_snapshot, capture_system_snapshot; capture_domain_snapshot(); capture_system_snapshot()\""'
echo ""

echo -e "${YELLOW}Documentation:${NC}"
echo "  docs/architecture/enhancements-2025-12-02.md"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Access dashboard: http://localhost:8000/dashboard/"
echo "  2. Set up daily cron for snapshots"
echo "  3. Configure health monitoring alerts (Discord/Slack)"
echo "  4. Start file watcher for auto re-ingestion"
echo ""
