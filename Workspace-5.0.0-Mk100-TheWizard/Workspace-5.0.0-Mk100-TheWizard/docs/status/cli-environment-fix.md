# JARVIS CLI Environment Fix

**Issue**: `jarvis` command not found in container PATH

**Symptom**: When running `docker exec jarvis-app jarvis --help`, you get:
```
OCI runtime exec failed: exec failed: unable to start container process: exec: "jarvis": executable file not found in $PATH: unknown
```

---

## Root Cause

The `jarvis` CLI is installed by Poetry in `/workspace/.venv/bin/jarvis`, but this directory is not in the container's default PATH.

---

## Solutions (Choose One)

### Solution 1: Use `poetry run` (Recommended for Automation)

Always prefix jarvis commands with `poetry run`:

```bash
# From host
docker exec jarvis-app poetry run jarvis --help
docker exec jarvis-app poetry run jarvis health check
docker exec jarvis-app poetry run jarvis analytics snapshot

# Inside container
cd /workspace
poetry run jarvis --help
poetry run jarvis health check
```

**Pros**: Always works, doesn't require PATH modification
**Cons**: Slightly verbose

---

### Solution 2: Add venv to PATH (Recommended for Interactive Use)

Run the setup script once inside the container:

```bash
# From host
docker exec -it jarvis-app bash /workspace/scripts/setup-path.sh

# Or inside container
bash /workspace/scripts/setup-path.sh
```

This adds `/workspace/.venv/bin` to your `~/.bashrc`, making `jarvis` available directly.

**After setup**:
```bash
# From host (still needs full path in docker exec)
docker exec jarvis-app jarvis --help

# Inside container (works directly after sourcing bashrc)
source ~/.bashrc
jarvis --help
jarvis health check
```

**Pros**: Shorter commands, feels more natural
**Cons**: Requires one-time setup, only persists in ~/.bashrc

---

### Solution 3: Activate Virtual Environment Manually

Inside the container:

```bash
source /workspace/.venv/bin/activate
jarvis --help
jarvis health check
```

**Pros**: Standard Python workflow
**Cons**: Needs to be done every time you enter the container

---

## Updated Command Reference

### Health Monitoring

```bash
# Check health (one-time)
docker exec jarvis-app poetry run jarvis health check

# Start monitoring daemon
docker exec -d jarvis-app bash -c "cd /workspace && poetry run jarvis health monitor --interval 15"
```

### Analytics & Snapshots

```bash
# Create snapshot tables (run once)
docker exec jarvis-app poetry run jarvis analytics init-snapshots

# Capture daily snapshot
docker exec jarvis-app poetry run jarvis analytics snapshot

# Show domain growth
docker exec jarvis-app poetry run jarvis analytics growth --days 7

# Mine keywords
docker exec jarvis-app poetry run jarvis analytics mine-keywords
```

### Enrichment

```bash
# Get recommendations
docker exec jarvis-app poetry run jarvis analytics enrichment-recommendations

# Calculate ROI
docker exec jarvis-app poetry run jarvis analytics enrichment-roi
```

### File Watching

```bash
# Start file watcher
docker exec -d jarvis-app bash -c "cd /workspace && poetry run jarvis watch start docs/"
```

---

## Cron Jobs

When setting up cron jobs, use the full `poetry run` command:

```cron
# Daily snapshot (2 AM UTC)
0 2 * * * cd /workspace && poetry run jarvis analytics snapshot >> /var/log/jarvis-snapshots.log 2>&1

# Weekly keyword mining (Sunday 3 AM UTC)
0 3 * * 0 cd /workspace && poetry run jarvis analytics mine-keywords >> /var/log/jarvis-keywords.log 2>&1
```

The `setup-cron.sh` script has been updated to use `poetry run` automatically.

---

## Verification

After choosing a solution, verify it works:

```bash
# Run verification script (updated to use poetry run)
chmod +x scripts/verify-integration.sh
./scripts/verify-integration.sh

# Should see all CLI tests pass
```

---

## Why This Happened

The JARVIS container uses Poetry for dependency management. Poetry installs console scripts (like `jarvis`) in the virtual environment's `bin/` directory.

**Two ways to run Poetry-managed scripts**:

1. **Activate venv first**: `source .venv/bin/activate && jarvis`
2. **Use poetry run**: `poetry run jarvis` (no activation needed)

Docker containers don't automatically activate virtual environments, so you need to choose one of the solutions above.

---

## Quick Reference Card

```bash
# ✅ WORKS - Use poetry run
docker exec jarvis-app poetry run jarvis health check

# ✅ WORKS - After running setup-path.sh
docker exec jarvis-app jarvis health check

# ❌ DOESN'T WORK - venv not in PATH
docker exec jarvis-app jarvis health check

# ✅ WORKS - Inside container with venv activated
docker exec -it jarvis-app bash
source /workspace/.venv/bin/activate
jarvis health check
```

---

## Production Recommendation

For **automated tasks** (cron, scripts): Use `poetry run`
For **interactive use** (manual commands): Run `setup-path.sh` once

Both approaches are production-ready and fully supported.

---

**Next Steps**: Choose your preferred solution above, then continue with the [production integration guide](PRODUCTION-INTEGRATION-COMPLETE.md).
