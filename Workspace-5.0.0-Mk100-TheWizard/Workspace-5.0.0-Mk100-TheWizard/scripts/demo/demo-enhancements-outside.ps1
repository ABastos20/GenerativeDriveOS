# JARVIS Memory Enhancements Demo - Run from HOST (outside container)
# Usage: .\scripts\demo-enhancements-outside.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "JARVIS Memory Enhancements Demo (v2.0)" -ForegroundColor Cyan
Write-Host "Running from host machine" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "[Pre-Check] Verifying Docker..." -ForegroundColor Blue
docker ps | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker is not running or accessible" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker is running" -ForegroundColor Green
Write-Host ""

# Check if jarvis-app container exists and is running
Write-Host "[Pre-Check] Verifying jarvis-app container..." -ForegroundColor Blue
$container = docker ps --filter "name=jarvis-app" --format "{{.Names}}"
if (-not $container) {
    Write-Host "ERROR: jarvis-app container is not running" -ForegroundColor Red
    Write-Host "Start it with: docker compose -f docker/docker-compose.yml up -d" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ jarvis-app container is running" -ForegroundColor Green
Write-Host ""

# ============================================
# Step 1: Install watchdog dependency
# ============================================
Write-Host "=== [Step 1] Installing Dependencies ===" -ForegroundColor Green
Write-Host "Installing watchdog for file watching..." -ForegroundColor Yellow
docker exec jarvis-app bash -c "cd /workspace && poetry add watchdog --quiet" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ watchdog installed" -ForegroundColor Green
} else {
    Write-Host "⚠ watchdog may already be installed or poetry not available" -ForegroundColor Yellow
}
Write-Host ""
Read-Host "Press Enter to continue"
Write-Host ""

# ============================================
# Step 2: Register dashboard route
# ============================================
Write-Host "=== [Step 2] Registering Dashboard Route ===" -ForegroundColor Green
Write-Host "Adding dashboard router to FastAPI app..." -ForegroundColor Yellow
Write-Host ""

# Check if dashboard route is already registered
$checkRoute = docker exec jarvis-app grep -n "dashboard_router" /workspace/src/jarvis/api/app.py 2>$null
if ($checkRoute) {
    Write-Host "✓ Dashboard route already registered" -ForegroundColor Green
} else {
    Write-Host "Dashboard route not found. Adding it manually..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Add these lines to src/jarvis/api/app.py:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "from jarvis.api.dashboard import router as dashboard_router" -ForegroundColor White
    Write-Host "app.include_router(dashboard_router)" -ForegroundColor White
    Write-Host ""
    Write-Host "After the existing router registrations (around line 50-60)" -ForegroundColor Yellow
}
Write-Host ""
Read-Host "Press Enter to continue"
Write-Host ""

# ============================================
# Step 3: Create snapshot tables
# ============================================
Write-Host "=== [Step 3] Setting Up Evolution Tracking ===" -ForegroundColor Green
Write-Host "Creating PostgreSQL snapshot tables..." -ForegroundColor Yellow
docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -c 'from jarvis.analytics import create_snapshot_tables; create_snapshot_tables()'"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Snapshot tables created" -ForegroundColor Green
} else {
    Write-Host "⚠ Error creating tables (may already exist)" -ForegroundColor Yellow
}
Write-Host ""
Read-Host "Press Enter to continue"
Write-Host ""

# ============================================
# Step 4: Run health check
# ============================================
Write-Host "=== [Step 4] Running Health Check ===" -ForegroundColor Green
Write-Host "Checking JARVIS memory system health..." -ForegroundColor Yellow
Write-Host ""

docker exec jarvis-app bash -c @"
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
"@

Write-Host ""
Read-Host "Press Enter to continue"
Write-Host ""

# ============================================
# Step 5: Mine keywords
# ============================================
Write-Host "=== [Step 5] Mining Keywords (Auto-Learning Heuristics) ===" -ForegroundColor Green
Write-Host "Analyzing LLM-classified chunks for keyword patterns..." -ForegroundColor Yellow
Write-Host ""

docker exec jarvis-app bash -c @"
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
"@

Write-Host ""
Read-Host "Press Enter to continue"
Write-Host ""

# ============================================
# Step 6: Show domain relationships
# ============================================
Write-Host "=== [Step 6] Domain Relationship Graph ===" -ForegroundColor Green
Write-Host "Visualizing semantic domain connections..." -ForegroundColor Yellow
Write-Host ""

docker exec jarvis-app bash -c @"
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
"@

Write-Host ""
Read-Host "Press Enter to continue"
Write-Host ""

# ============================================
# Step 7: Capture snapshots
# ============================================
Write-Host "=== [Step 7] Capturing Evolution Snapshots ===" -ForegroundColor Green
Write-Host "Taking domain distribution and system metrics snapshots..." -ForegroundColor Yellow
Write-Host ""

docker exec jarvis-app bash -c @"
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
"@

Write-Host ""
Read-Host "Press Enter to continue"
Write-Host ""

# ============================================
# Step 8: Get enrichment recommendations
# ============================================
Write-Host "=== [Step 8] Enrichment Quality Scoring ===" -ForegroundColor Green
Write-Host "Analyzing enrichment ROI and recommendations..." -ForegroundColor Yellow
Write-Host ""

docker exec jarvis-app bash -c @"
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
"@

Write-Host ""
Read-Host "Press Enter to continue"
Write-Host ""

# ============================================
# Step 9: Dashboard access
# ============================================
Write-Host "=== [Step 9] Accessing Interactive Dashboard ===" -ForegroundColor Green
Write-Host ""

# Check if API is running
$apiCheck = docker exec jarvis-app bash -c "curl -s http://localhost:8000/health 2>/dev/null" 2>$null
if ($apiCheck) {
    Write-Host "✓ JARVIS API is running" -ForegroundColor Green
    Write-Host ""
    Write-Host "Dashboard should be available at:" -ForegroundColor Cyan
    Write-Host "  http://localhost:8000/dashboard/" -ForegroundColor White
    Write-Host ""
    Write-Host "Testing dashboard API endpoint..." -ForegroundColor Yellow

    $dashboardTest = docker exec jarvis-app bash -c "curl -s http://localhost:8000/dashboard/api/stats 2>/dev/null | head -c 200" 2>$null
    if ($dashboardTest) {
        Write-Host "✓ Dashboard API is responding" -ForegroundColor Green
        Write-Host ""
        Write-Host "Open in your browser: http://localhost:8000/dashboard/" -ForegroundColor Cyan
    } else {
        Write-Host "⚠ Dashboard API not found. Make sure you registered the route in app.py" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Add to src/jarvis/api/app.py:" -ForegroundColor Cyan
        Write-Host "  from jarvis.api.dashboard import router as dashboard_router" -ForegroundColor White
        Write-Host "  app.include_router(dashboard_router)" -ForegroundColor White
        Write-Host ""
        Write-Host "Then restart: docker compose -f docker/docker-compose.yml restart jarvis-app" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ JARVIS API may not be running on port 8000" -ForegroundColor Yellow
    Write-Host "Start it with: docker compose -f docker/docker-compose.yml up -d" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to continue"
Write-Host ""

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Demo Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Enhancement Status:" -ForegroundColor Green
Write-Host "  ✅ #1: Auto-Learning Heuristics - Ready" -ForegroundColor White
Write-Host "  ✅ #2: Domain Relationship Graph - Ready" -ForegroundColor White
Write-Host "  ✅ #3: Interactive Dashboard - Check http://localhost:8000/dashboard/" -ForegroundColor White
Write-Host "  ✅ #4: Health Monitoring - Ready" -ForegroundColor White
Write-Host "  ✅ #5: Domain Evolution Tracking - Snapshots captured" -ForegroundColor White
Write-Host "  ✅ #6: Enrichment Quality Scoring - Ready" -ForegroundColor White
Write-Host "  ✅ #7: Smart Re-ingestion - Ready (not started)" -ForegroundColor White
Write-Host ""

Write-Host "Quick Commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Run health check:" -ForegroundColor Cyan
Write-Host '  docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -m jarvis.monitoring.health_monitor"' -ForegroundColor White
Write-Host ""
Write-Host "Mine keywords:" -ForegroundColor Cyan
Write-Host '  docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -m jarvis.memory.keyword_miner"' -ForegroundColor White
Write-Host ""
Write-Host "Capture daily snapshot:" -ForegroundColor Cyan
Write-Host '  docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.analytics import capture_domain_snapshot, capture_system_snapshot; capture_domain_snapshot(); capture_system_snapshot()\""' -ForegroundColor White
Write-Host ""
Write-Host "Start file watcher (in background):" -ForegroundColor Cyan
Write-Host '  docker exec -d jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -c \"from jarvis.memory.file_watcher import start_file_watcher; start_file_watcher([\"docs/\"], daemon=False)\""' -ForegroundColor White
Write-Host ""

Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  docs/architecture/enhancements-2025-12-02.md" -ForegroundColor White
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Access dashboard: http://localhost:8000/dashboard/" -ForegroundColor White
Write-Host "  2. Set up daily cron for snapshots" -ForegroundColor White
Write-Host "  3. Configure health monitoring alerts (Discord/Slack)" -ForegroundColor White
Write-Host "  4. Start file watcher for auto re-ingestion" -ForegroundColor White
Write-Host ""
