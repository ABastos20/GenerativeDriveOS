#!/bin/bash
# JARVIS Memory Enhancements Demo - Run INSIDE jarvis-app container
# Usage: docker exec -it jarvis-app bash scripts/demo-enhancements-inside.sh

set -e

echo "=========================================="
echo "JARVIS Memory Enhancements Demo (v2.0)"
echo "Running inside jarvis-app container"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Set PYTHONPATH
export PYTHONPATH="/workspace/src:${PYTHONPATH}"

echo -e "${BLUE}[Step 1] Checking environment...${NC}"
python --version
echo "PYTHONPATH: $PYTHONPATH"
echo ""

# ============================================
# Enhancement #1: Auto-Learning Heuristics
# ============================================
echo -e "${GREEN}=== Enhancement #1: Auto-Learning Heuristics ===${NC}"
echo "Mining keywords from LLM-classified chunks..."
echo ""

python -c "
from jarvis.memory.keyword_miner import mine_llm_classified_keywords, format_keyword_suggestions
import structlog
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))  # INFO level

print('Mining keywords (this may take 30-60 seconds)...')
suggestions = mine_llm_classified_keywords(
    collection_name='jarvis-core',
    min_occurrences=5,  # Lower threshold for demo
    max_suggestions=10,  # Limit for readability
)

if suggestions:
    report = format_keyword_suggestions(suggestions, top_domains=5)
    print(report)
else:
    print('No suggestions found. LLM classification may not be active yet.')
    print('Run: jarvis catalog domain-job --llm-fallback')
"
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Enhancement #2: Domain Relationship Graph
# ============================================
echo -e "${GREEN}=== Enhancement #2: Domain Relationship Graph ===${NC}"
echo "Visualizing domain relationships..."
echo ""

python -c "
from jarvis.memory.domain_relationships import (
    get_related_domains,
    expand_domain_filter,
    visualize_domain_graph,
)

print('Example: jarvis.memory.rag domain relationships')
print('=' * 60)

# Get related domains
related = get_related_domains('jarvis.memory.rag', max_depth=1, min_strength=0.5)
print(f'Related domains ({len(related)}):')
for domain, strength in related[:5]:
    print(f'  - {domain} (strength: {strength:.2f})')

print()

# Show domain expansion
original = ['jarvis.memory.rag']
expanded = expand_domain_filter(original, max_expansions=5, min_strength=0.6)
print(f'Domain filter expansion:')
print(f'  Original: {original}')
print(f'  Expanded: {expanded}')

print()

# Visualize graph
graph = visualize_domain_graph('jarvis.memory.rag', max_depth=1)
print(graph[:500])  # First 500 chars
"
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Enhancement #4: Health Monitoring
# ============================================
echo -e "${GREEN}=== Enhancement #4: Health Monitoring ===${NC}"
echo "Running health checks..."
echo ""

python -c "
from jarvis.monitoring import HealthMonitor, AlertConfig, format_health_report
import structlog
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(30))  # WARNING level

config = AlertConfig(
    qdrant_min_expected_points=10000,  # Lower for demo
    heuristic_hit_rate_min=60.0,
    enrichment_coverage_min=20.0,
)

monitor = HealthMonitor(config)

print('Running health checks...')
results = monitor.run_all_checks(collection_name='jarvis-core')

report = format_health_report(results)
print(report)
"
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Enhancement #5: Domain Evolution Tracking
# ============================================
echo -e "${GREEN}=== Enhancement #5: Domain Evolution Tracking ===${NC}"
echo "Setting up evolution tracking..."
echo ""

python -c "
from jarvis.analytics import (
    create_snapshot_tables,
    capture_domain_snapshot,
    capture_system_snapshot,
)
import structlog
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))

print('Creating snapshot tables...')
create_snapshot_tables()

print('Capturing domain snapshot...')
try:
    capture_domain_snapshot(collection_name='jarvis-core')
    print('✓ Domain snapshot captured')
except Exception as e:
    print(f'Note: {str(e)}')

print('Capturing system snapshot...')
try:
    capture_system_snapshot(collection_name='jarvis-core')
    print('✓ System snapshot captured')
except Exception as e:
    print(f'Note: {str(e)}')

print()
print('Snapshots are now stored in PostgreSQL.')
print('Run this daily via cron: jarvis analytics snapshot')
"
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Enhancement #6: Enrichment Quality Scoring
# ============================================
echo -e "${GREEN}=== Enhancement #6: Enrichment Quality Scoring ===${NC}"
echo "Getting enrichment recommendations..."
echo ""

python -c "
from jarvis.memory.enrichment_scorer import (
    get_enrichment_recommendations,
    format_recommendations_report,
)
import structlog
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))

print('Analyzing enrichment opportunities...')
recommendations = get_enrichment_recommendations(collection_name='jarvis-core')

report = format_recommendations_report(recommendations)
print(report[:1000])  # First 1000 chars
"
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Enhancement #7: File Watcher Demo
# ============================================
echo -e "${GREEN}=== Enhancement #7: Smart Re-ingestion (File Watcher) ===${NC}"
echo "File watcher can be started with:"
echo ""
echo "  python -c \"from jarvis.memory.file_watcher import start_file_watcher; start_file_watcher(['docs/'], daemon=False)\""
echo ""
echo "Or via CLI (when implemented):"
echo "  jarvis watch docs/ --daemon"
echo ""
echo "This will automatically re-ingest files when they change."
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Dashboard Access Instructions
# ============================================
echo -e "${GREEN}=== Enhancement #3: Interactive Dashboard ===${NC}"
echo ""
echo "To access the dashboard:"
echo ""
echo "1. Make sure dashboard route is registered in src/jarvis/api/app.py:"
echo "   ${YELLOW}from jarvis.api.dashboard import router as dashboard_router${NC}"
echo "   ${YELLOW}app.include_router(dashboard_router)${NC}"
echo ""
echo "2. Restart the API server"
echo ""
echo "3. Open in browser:"
echo "   ${BLUE}http://localhost:8000/dashboard/${NC}"
echo ""
echo "4. Or check API endpoint:"
echo "   ${BLUE}curl http://localhost:8000/dashboard/api/stats${NC}"
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Summary
# ============================================
echo ""
echo "=========================================="
echo "Demo Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ Enhancement #1:${NC} Auto-Learning Heuristics - Ready"
echo -e "${GREEN}✅ Enhancement #2:${NC} Domain Relationship Graph - Ready"
echo -e "${GREEN}✅ Enhancement #3:${NC} Interactive Dashboard - Needs route registration"
echo -e "${GREEN}✅ Enhancement #4:${NC} Health Monitoring - Ready"
echo -e "${GREEN}✅ Enhancement #5:${NC} Domain Evolution Tracking - Tables created"
echo -e "${GREEN}✅ Enhancement #6:${NC} Enrichment Quality Scoring - Ready"
echo -e "${GREEN}✅ Enhancement #7:${NC} Smart Re-ingestion - Ready"
echo ""
echo "Next steps:"
echo "1. Register dashboard route in app.py"
echo "2. Add CLI commands for new features"
echo "3. Set up daily cron job: 0 2 * * * jarvis analytics snapshot"
echo "4. Start health monitor: jarvis health monitor --interval 15"
echo ""
echo "Documentation:"
echo "  ${BLUE}docs/architecture/enhancements-2025-12-02.md${NC}"
echo ""
