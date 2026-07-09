# JARVIS Enhancements - Quick Start Guide

**Date**: 2025-12-02
**Version**: 2.0

---

## 🚀 Quick Demo Scripts

### Inside Container
```bash
# Copy script into container
docker cp scripts/demo-enhancements-inside.sh jarvis-app:/workspace/

# Run inside container
docker exec -it jarvis-app bash /workspace/demo-enhancements-inside.sh
```

### Outside Container (Windows)
```powershell
.\scripts\demo-enhancements-outside.ps1
```

### Outside Container (Linux/Mac)
```bash
chmod +x scripts/demo-enhancements-outside.sh
./scripts/demo-enhancements-outside.sh
```

---

## 📊 Interactive Dashboard

### Access
```
http://localhost:8000/dashboard/
```

### First-Time Setup
Add to `src/jarvis/api/app.py` (around line 50-60):
```python
from jarvis.api.dashboard import router as dashboard_router
app.include_router(dashboard_router)
```

Then restart:
```bash
docker compose -f docker/docker-compose.yml restart jarvis-app
```

### API Endpoint
```bash
curl http://localhost:8000/dashboard/api/stats | jq
```

---

## 🏥 Health Monitoring

### Run Once (Manual Check)
```bash
docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.monitoring import HealthMonitor, format_health_report
m = HealthMonitor()
results = m.run_all_checks(\"jarvis-core\")
print(format_health_report(results))
'
"
```

### Run as Daemon (Continuous)
```bash
docker exec -d jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.monitoring import HealthMonitor, AlertConfig
config = AlertConfig(
    discord_webhook_url=\"YOUR_WEBHOOK_URL\",
    heuristic_hit_rate_min=65.0,
)
m = HealthMonitor(config)
m.run_daemon(check_interval_minutes=15)
'
"
```

### Configure Alerts
```python
# In Python
from jarvis.monitoring import AlertConfig

config = AlertConfig(
    qdrant_min_expected_points=40000,
    heuristic_hit_rate_min=65.0,
    enrichment_coverage_min=30.0,
    enrichment_coverage_max=60.0,
    discord_webhook_url="https://discord.com/api/webhooks/...",
    slack_webhook_url="https://hooks.slack.com/services/...",
)
```

---

## 🔍 Auto-Learning Heuristics

### Mine Keywords
```bash
docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.memory.keyword_miner import mine_llm_classified_keywords, format_keyword_suggestions
suggestions = mine_llm_classified_keywords(min_occurrences=10)
print(format_keyword_suggestions(suggestions, top_domains=10))
'
"
```

### Generate Code for Specific Domain
```bash
docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.memory.keyword_miner import mine_llm_classified_keywords, generate_heuristic_code
suggestions = mine_llm_classified_keywords()
if \"jarvis.memory.rag\" in suggestions:
    code = generate_heuristic_code(\"jarvis.memory.rag\", suggestions[\"jarvis.memory.rag\"], top_n=20)
    print(code)
'
"
```

---

## 🔗 Domain Relationships

### Get Related Domains
```python
from jarvis.memory.domain_relationships import get_related_domains

related = get_related_domains("jarvis.memory.rag", max_depth=2, min_strength=0.6)
# Returns: [("ai.embeddings", 0.9), ("ai.llm", 0.9), ...]
```

### Expand Domain Filter
```python
from jarvis.memory.domain_relationships import expand_domain_filter

expanded = expand_domain_filter(
    domains=["jarvis.memory.rag"],
    max_expansions=5,
    min_strength=0.6,
)
# Returns: ["jarvis.memory.rag", "ai.embeddings", "ai.llm", "ai.transformers", ...]
```

### Visualize Graph
```python
from jarvis.memory.domain_relationships import visualize_domain_graph

graph = visualize_domain_graph("jarvis.memory.rag", max_depth=2)
print(graph)
```

---

## 📈 Domain Evolution Tracking

### Create Tables (First Time Only)
```bash
docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.analytics import create_snapshot_tables
create_snapshot_tables()
'
"
```

### Capture Daily Snapshot
```bash
docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.analytics import capture_domain_snapshot, capture_system_snapshot
capture_domain_snapshot(\"jarvis-core\")
capture_system_snapshot(\"jarvis-core\")
'
"
```

### View Growth Report
```bash
docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.analytics import get_top_growing_domains, format_domain_growth_report
growth = get_top_growing_domains(days=7, limit=10)
print(format_domain_growth_report(growth))
'
"
```

### Set Up Daily Cron
```bash
# Add to crontab
0 2 * * * docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -c 'from jarvis.analytics import capture_domain_snapshot, capture_system_snapshot; capture_domain_snapshot(); capture_system_snapshot()'"
```

---

## ✨ Enrichment Quality Scoring

### Get Recommendations
```bash
docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.memory.enrichment_scorer import get_enrichment_recommendations, format_recommendations_report
recs = get_enrichment_recommendations(\"jarvis-core\")
print(format_recommendations_report(recs))
'
"
```

### Calculate ROI
```bash
docker exec jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.memory.enrichment_scorer import calculate_enrichment_roi, format_enrichment_report
scores = calculate_enrichment_roi(\"jarvis-core\", lookback_days=30)
print(format_enrichment_report(scores))
'
"
```

---

## 📁 Smart File Watching

### Start Watcher (Foreground)
```bash
docker exec -it jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.memory.file_watcher import start_file_watcher
start_file_watcher([\"docs/\", \"src/jarvis/\"], daemon=False)
'
"
```

### Start Watcher (Background Daemon)
```bash
docker exec -d jarvis-app bash -c "
cd /workspace && PYTHONPATH=/workspace/src python -c '
from jarvis.memory.file_watcher import start_file_watcher
start_file_watcher([\"docs/\"], daemon=False)
'
"
```

---

## 🔧 Dependencies

### Install watchdog (Required for File Watching)
```bash
docker exec jarvis-app bash -c "cd /workspace && poetry add watchdog"
```

---

## 📚 Documentation

- **Complete Guide**: [docs/architecture/enhancements-2025-12-02.md](architecture/enhancements-2025-12-02.md)
- **Memory Architecture**: [docs/architecture/jarvis-memory-architecture.md](architecture/jarvis-memory-architecture.md)
- **Domain Taxonomy**: [docs/architecture/domain-taxonomy.md](architecture/domain-taxonomy.md)
- **Pipeline Flows**: [docs/architecture/memory-pipeline-flow.md](architecture/memory-pipeline-flow.md)

---

## 🎯 Common Workflows

### Daily Operations
```bash
# 1. Check health
docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -c 'from jarvis.monitoring import HealthMonitor; m=HealthMonitor(); results=m.run_all_checks(); print([r.status for r in results])'"

# 2. View dashboard
# Open: http://localhost:8000/dashboard/

# 3. Check for new keyword patterns (weekly)
docker exec jarvis-app bash -c "cd /workspace && PYTHONPATH=/workspace/src python -c 'from jarvis.memory.keyword_miner import mine_llm_classified_keywords; suggestions=mine_llm_classified_keywords(min_occurrences=10); print(len(suggestions), \"domains have keyword suggestions\")'"
```

### Weekly Optimization
```bash
# 1. Mine keywords
# 2. Review and add to heuristics/*.py
# 3. Re-run domain catalog job
# 4. Get enrichment recommendations
# 5. Enrich high-priority docs only
```

### Monthly Analysis
```bash
# 1. Review domain growth trends (30 days)
# 2. Analyze enrichment ROI
# 3. Update heuristic thresholds
# 4. Review health monitoring alerts
```

---

## 💡 Troubleshooting

### Dashboard Not Loading
```bash
# 1. Check if route is registered
docker exec jarvis-app grep -n "dashboard_router" /workspace/src/jarvis/api/app.py

# 2. If not found, add to app.py:
#    from jarvis.api.dashboard import router as dashboard_router
#    app.include_router(dashboard_router)

# 3. Restart API
docker compose -f docker/docker-compose.yml restart jarvis-app
```

### Health Check Fails
```bash
# Check Qdrant
docker ps --filter "name=jarvis-qdrant"
curl http://localhost:6333/collections

# Check PostgreSQL
docker exec jarvis-postgres psql -U jarvis -c "SELECT COUNT(*) FROM conversations;"
```

### File Watcher Not Triggering
```bash
# 1. Check watchdog is installed
docker exec jarvis-app bash -c "poetry show watchdog"

# 2. Check file permissions
# 3. Verify file is in watched path
```

---

## 📊 Expected Metrics

| Metric | Target | Alert If |
|--------|--------|----------|
| Heuristic Hit Rate | 70-85% | <65% |
| Enrichment Coverage | 30-50% | <30% or >60% |
| Query Latency p95 | <1s | >2s |
| Daily LLM Cost | <$5 | >$5 |
| Qdrant Points | 40k+ | Drops >10% |

---

## 🎉 Success Indicators

✅ Dashboard loads at http://localhost:8000/dashboard/
✅ Health checks return all "ok" status
✅ Daily snapshots captured in PostgreSQL
✅ Keyword suggestions showing 5+ domains
✅ Enrichment recommendations available
✅ File watcher responding to changes

---

**Ready to scale!** 🚀
