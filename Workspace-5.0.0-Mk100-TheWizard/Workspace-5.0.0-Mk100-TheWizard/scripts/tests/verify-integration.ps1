# JARVIS Production Integration Verification Script (Windows PowerShell)
#
# Tests all new CLI commands and verifies successful integration

$ErrorCount = 0

Write-Host "=========================================="
Write-Host "JARVIS Production Integration Verification"
Write-Host "=========================================="
Write-Host ""

function Test-Command {
    param(
        [string]$Name,
        [string]$Command,
        [bool]$ExpectSuccess = $true
    )

    Write-Host -NoNewline "Testing: $Name ... "

    try {
        Invoke-Expression $Command *>$null
        $success = $?
    } catch {
        $success = $false
    }

    if ($success -eq $ExpectSuccess) {
        Write-Host "✓" -ForegroundColor Green
    } else {
        Write-Host "✗" -ForegroundColor Red
        $script:ErrorCount++
    }
}

Write-Host "=== Testing CLI Module Registration ==="
Write-Host ""

Test-Command "jarvis --help" "docker exec jarvis-app jarvis --help"
Test-Command "jarvis analytics --help" "docker exec jarvis-app jarvis analytics --help"
Test-Command "jarvis health --help" "docker exec jarvis-app jarvis health --help"
Test-Command "jarvis watch --help" "docker exec jarvis-app jarvis watch --help"

Write-Host ""
Write-Host "=== Testing New Analytics Commands ==="
Write-Host ""

Test-Command "jarvis analytics init-snapshots --help" "docker exec jarvis-app jarvis analytics init-snapshots --help"
Test-Command "jarvis analytics snapshot --help" "docker exec jarvis-app jarvis analytics snapshot --help"
Test-Command "jarvis analytics growth --help" "docker exec jarvis-app jarvis analytics growth --help"
Test-Command "jarvis analytics mine-keywords --help" "docker exec jarvis-app jarvis analytics mine-keywords --help"
Test-Command "jarvis analytics enrichment-roi --help" "docker exec jarvis-app jarvis analytics enrichment-roi --help"
Test-Command "jarvis analytics enrichment-recommendations --help" "docker exec jarvis-app jarvis analytics enrichment-recommendations --help"

Write-Host ""
Write-Host "=== Testing Health Commands ==="
Write-Host ""

Test-Command "jarvis health check --help" "docker exec jarvis-app jarvis health check --help"
Test-Command "jarvis health monitor --help" "docker exec jarvis-app jarvis health monitor --help"

Write-Host ""
Write-Host "=== Testing Watch Commands ==="
Write-Host ""

Test-Command "jarvis watch start --help" "docker exec jarvis-app jarvis watch start --help"

Write-Host ""
Write-Host "=== Testing Dashboard Route ==="
Write-Host ""

# Test dashboard API endpoint
Write-Host -NoNewline "Testing: Dashboard API endpoint ... "
try {
    $result = docker exec jarvis-app curl -s -f http://localhost:8000/dashboard/api/stats 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓" -ForegroundColor Green
    } else {
        Write-Host "⚠ (API may not be running or route not registered)" -ForegroundColor Yellow
        $ErrorCount++
    }
} catch {
    Write-Host "⚠ (API may not be running or route not registered)" -ForegroundColor Yellow
    $ErrorCount++
}

# Test dashboard HTML endpoint
Write-Host -NoNewline "Testing: Dashboard HTML endpoint ... "
try {
    $result = docker exec jarvis-app curl -s -f http://localhost:8000/dashboard/ 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓" -ForegroundColor Green
    } else {
        Write-Host "⚠ (API may not be running or route not registered)" -ForegroundColor Yellow
        $ErrorCount++
    }
} catch {
    Write-Host "⚠ (API may not be running or route not registered)" -ForegroundColor Yellow
    $ErrorCount++
}

Write-Host ""
Write-Host "=== Testing Python Module Imports ==="
Write-Host ""

Test-Command "Import analytics module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c ""from jarvis.analytics import create_snapshot_tables""'"
Test-Command "Import monitoring module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c ""from jarvis.monitoring import HealthMonitor""'"
Test-Command "Import keyword_miner module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c ""from jarvis.memory.keyword_miner import mine_llm_classified_keywords""'"
Test-Command "Import enrichment_scorer module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c ""from jarvis.memory.enrichment_scorer import calculate_enrichment_roi""'"
Test-Command "Import domain_relationships module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c ""from jarvis.memory.domain_relationships import get_related_domains""'"
Test-Command "Import file_watcher module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c ""from jarvis.memory.file_watcher import start_file_watcher""'"
Test-Command "Import dashboard module" "docker exec jarvis-app bash -c 'cd /workspace && PYTHONPATH=/workspace/src python -c ""from jarvis.api.dashboard import router""'"

Write-Host ""
Write-Host "=== Testing Watchdog Dependency ==="
Write-Host ""

Test-Command "Watchdog installed" "docker exec jarvis-app python -c 'import watchdog'"

Write-Host ""
Write-Host "=========================================="
Write-Host "Verification Summary"
Write-Host "=========================================="
Write-Host ""

if ($ErrorCount -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Integration is complete and working correctly."
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Access dashboard: http://localhost:8000/dashboard/"
    Write-Host "  2. Run: docker exec jarvis-app jarvis health check"
    Write-Host "  3. Run: docker exec jarvis-app jarvis analytics snapshot"
    Write-Host "  4. Set up cron: .\scripts\setup-cron.ps1"
} else {
    Write-Host "⚠ $ErrorCount test(s) failed" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Some components may need attention."
    Write-Host "Check the errors above and consult docs/PRODUCTION-INTEGRATION-COMPLETE.md"
}

Write-Host ""

if ($ErrorCount -gt 0) {
    exit 1
}
