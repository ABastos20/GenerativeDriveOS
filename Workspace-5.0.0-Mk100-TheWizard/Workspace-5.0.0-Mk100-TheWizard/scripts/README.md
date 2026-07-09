# JARVIS Scripts Directory

This directory contains automation and demonstration scripts for JARVIS memory enhancements.

---

## 📜 Script Inventory

### Demo Scripts

| Script | Purpose | Platform |
|--------|---------|----------|
| [demo-enhancements-inside.sh](demo-enhancements-inside.sh) | Interactive demo of all 7 enhancements (run inside container) | Linux/Mac |
| [demo-enhancements-outside.sh](demo-enhancements-outside.sh) | Interactive demo of all 7 enhancements (run from host) | Linux/Mac |
| [demo-enhancements-outside.ps1](demo-enhancements-outside.ps1) | Interactive demo of all 7 enhancements (run from host) | Windows |

### Setup Scripts

| Script | Purpose | Platform |
|--------|---------|----------|
| [setup-cron.sh](setup-cron.sh) | Set up automated daily/weekly tasks using cron | Linux/Mac |
| [setup-cron.ps1](setup-cron.ps1) | Set up automated tasks (guides Task Scheduler setup) | Windows |

### Verification Scripts

| Script | Purpose | Platform |
|--------|---------|----------|
| [verify-integration.sh](verify-integration.sh) | Verify production integration is complete | Linux/Mac |
| [verify-integration.ps1](verify-integration.ps1) | Verify production integration is complete | Windows |

---

## 🚀 Quick Start

### 1. Run Demo (First Time)

**Linux/Mac (from host):**
```bash
chmod +x scripts/demo-enhancements-outside.sh
./scripts/demo-enhancements-outside.sh
```

**Windows:**
```powershell
.\scripts\demo-enhancements-outside.ps1
```

**Inside Container:**
```bash
docker exec -it jarvis-app bash /workspace/scripts/demo-enhancements-inside.sh
```

### 2. Verify Integration

**Linux/Mac:**
```bash
chmod +x scripts/verify-integration.sh
./scripts/verify-integration.sh
```

**Windows:**
```powershell
.\scripts\verify-integration.ps1
```

### 3. Set Up Automation

**Linux/Mac:**
```bash
chmod +x scripts/setup-cron.sh
./scripts/setup-cron.sh
```

**Windows:**
```powershell
.\scripts\setup-cron.ps1
```

---

## 📋 Script Details

### demo-enhancements-outside.sh / .ps1

**What it does:**
- Installs watchdog dependency
- Checks dashboard route registration
- Creates snapshot tables
- Runs health check
- Mines keywords
- Shows domain relationships
- Captures snapshots
- Analyzes enrichment opportunities
- Tests dashboard access

**When to use:**
- First time exploring enhancements
- After fresh installation
- Testing after updates

**Runtime:** ~5-10 minutes (interactive, with pauses)

---

### setup-cron.sh / .ps1

**What it does:**
- Creates cron jobs for:
  - Daily domain snapshots (2 AM UTC)
  - Weekly keyword mining (Sunday 3 AM UTC)
- Installs and starts cron service (Linux/Mac)
- Provides Task Scheduler guidance (Windows)

**When to use:**
- After verifying integration works
- When ready for production automation

**Cron Jobs Created:**

```cron
# Daily: Capture domain evolution snapshots (2 AM UTC)
0 2 * * * jarvis analytics snapshot

# Weekly: Mine keywords from LLM classifications (Sunday 3 AM UTC)
0 3 * * 0 jarvis analytics mine-keywords
```

---

### verify-integration.sh / .ps1

**What it does:**
- Tests all CLI module registrations
- Verifies new analytics commands
- Checks health commands
- Tests watch commands
- Validates dashboard endpoints
- Confirms Python module imports
- Checks watchdog dependency

**When to use:**
- After production integration
- After updates or changes
- Troubleshooting issues

**Exit codes:**
- `0` - All tests passed
- `1` - One or more tests failed

**Example output:**
```
Testing: jarvis --help ... ✓
Testing: jarvis analytics --help ... ✓
Testing: jarvis health --help ... ✓
Testing: jarvis watch --help ... ✓
...
✅ All tests passed!
```

---

## 🎯 Recommended Workflow

1. **First Time Setup**
   ```bash
   # 1. Run demo to see everything in action
   ./scripts/demo-enhancements-outside.sh

   # 2. Verify integration
   ./scripts/verify-integration.sh

   # 3. Set up automation
   ./scripts/setup-cron.sh
   ```

2. **After Updates**
   ```bash
   # Quick verification
   ./scripts/verify-integration.sh
   ```

3. **Troubleshooting**
   ```bash
   # Re-run demo to identify issues
   ./scripts/demo-enhancements-outside.sh
   ```

---

## 🔧 Making Scripts Executable (Linux/Mac)

```bash
# Make all scripts executable
chmod +x scripts/*.sh

# Or individually
chmod +x scripts/demo-enhancements-outside.sh
chmod +x scripts/setup-cron.sh
chmod +x scripts/verify-integration.sh
```

---

## 📊 What Each Enhancement Does

### 1. Auto-Learning Heuristics
- **Script**: Mine keywords step in demo
- **CLI**: `jarvis analytics mine-keywords`
- **Benefit**: Reduce LLM costs by 50%

### 2. Domain Relationship Graph
- **Script**: Domain relationships step in demo
- **CLI**: Built into search (automatic)
- **Benefit**: Smarter cross-domain retrieval

### 3. Interactive Dashboard
- **Script**: Dashboard access step in demo
- **URL**: http://localhost:8000/dashboard/
- **Benefit**: Real-time visibility

### 4. Health Monitoring
- **Script**: Health check step in demo
- **CLI**: `jarvis health check` / `jarvis health monitor`
- **Benefit**: Proactive alerts

### 5. Domain Evolution Tracking
- **Script**: Snapshot capture step in demo
- **CLI**: `jarvis analytics snapshot` / `jarvis analytics growth`
- **Benefit**: Knowledge growth insights

### 6. Enrichment Quality Scoring
- **Script**: Enrichment recommendations step in demo
- **CLI**: `jarvis analytics enrichment-roi`
- **Benefit**: Optimize LLM spend

### 7. Smart Re-ingestion
- **Script**: Not in demo (starts daemon)
- **CLI**: `jarvis watch start <path>`
- **Benefit**: Automatic file updates

---

## 🆘 Troubleshooting

### Scripts Won't Run (Linux/Mac)

**Problem:** Permission denied

**Solution:**
```bash
chmod +x scripts/*.sh
```

### Docker Not Found

**Problem:** `docker: command not found`

**Solution:**
- Install Docker Desktop
- Ensure Docker is running
- Add Docker to PATH

### Container Not Running

**Problem:** `jarvis-app container is not running`

**Solution:**
```bash
docker compose -f docker/docker-compose.yml up -d
```

### Demo Script Hangs

**Problem:** Script waits at "Press Enter to continue"

**Solution:**
- This is intentional - review output
- Press Enter to continue
- Use Ctrl+C to exit

---

## 📚 Documentation

- **Production Integration**: [../docs/PRODUCTION-INTEGRATION-COMPLETE.md](../docs/PRODUCTION-INTEGRATION-COMPLETE.md)
- **Quick Start**: [../docs/ENHANCEMENTS-QUICK-START.md](../docs/ENHANCEMENTS-QUICK-START.md)
- **Complete Guide**: [../docs/architecture/enhancements-2025-12-02.md](../docs/architecture/enhancements-2025-12-02.md)

---

## 💡 Tips

1. **Run demo first** - See everything in action before diving into CLI
2. **Check logs** - Demo scripts show what's happening
3. **Use verification script** - Quick way to check if everything works
4. **Set up automation early** - Daily snapshots provide valuable trend data
5. **Monitor regularly** - Use `jarvis health check` or dashboard

---

**Questions?** Check [../docs/PRODUCTION-INTEGRATION-COMPLETE.md](../docs/PRODUCTION-INTEGRATION-COMPLETE.md)
