# JARVIS Memory Enhancements - Automated Task Setup (Windows)
#
# This script helps set up automated tasks for JARVIS on Windows using Task Scheduler
# or provides instructions for Docker-based cron setup

Write-Host "=========================================="
Write-Host "JARVIS Automated Task Setup (Windows)"
Write-Host "=========================================="
Write-Host ""

Write-Host "Since you're on Windows, you have two options:"
Write-Host ""

Write-Host "Option 1: Docker Container Cron (Recommended)"
Write-Host "=============================================="
Write-Host ""
Write-Host "Set up cron inside the Docker container:"
Write-Host ""
Write-Host "1. Copy setup script to container:"
Write-Host "   docker cp scripts/setup-cron.sh jarvis-app:/workspace/scripts/"
Write-Host ""
Write-Host "2. Run setup inside container:"
Write-Host "   docker exec -it jarvis-app bash /workspace/scripts/setup-cron.sh"
Write-Host ""

Write-Host "Option 2: Windows Task Scheduler"
Write-Host "================================="
Write-Host ""
Write-Host "Create scheduled tasks that run these commands:"
Write-Host ""
Write-Host "Daily Snapshot (2 AM):"
Write-Host "  docker exec jarvis-app bash -c `"cd /workspace && PYTHONPATH=/workspace/src python -c 'from jarvis.analytics import capture_domain_snapshot, capture_system_snapshot; capture_domain_snapshot(`\"knowledge`\"); capture_system_snapshot(`\"knowledge`\")'`""
Write-Host ""
Write-Host "Weekly Keyword Mining (Sunday 3 AM):"
Write-Host "  docker exec jarvis-app bash -c `"cd /workspace && PYTHONPATH=/workspace/src python -c 'from jarvis.memory.keyword_miner import mine_llm_classified_keywords; mine_llm_classified_keywords(`\"knowledge`\")'`""
Write-Host ""

Write-Host "Option 3: Manual CLI Commands"
Write-Host "=============================="
Write-Host ""
Write-Host "Run these commands manually when needed:"
Write-Host ""
Write-Host "# Daily snapshot"
Write-Host "docker exec jarvis-app jarvis analytics snapshot"
Write-Host ""
Write-Host "# Weekly keyword mining"
Write-Host "docker exec jarvis-app jarvis analytics mine-keywords"
Write-Host ""
Write-Host "# Health monitoring (continuous)"
Write-Host "docker exec -d jarvis-app jarvis health monitor --interval 15"
Write-Host ""

Write-Host "=========================================="
Write-Host "Recommended Setup for Windows"
Write-Host "=========================================="
Write-Host ""
Write-Host "Use Option 1 (Docker container cron) for best results."
Write-Host "This keeps all automation inside the container."
Write-Host ""

$response = Read-Host "Do you want to set up cron inside the container now? (y/n)"

if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    Write-Host "Setting up cron in container..."
    Write-Host ""

    # Copy setup script
    docker cp scripts/setup-cron.sh jarvis-app:/workspace/scripts/

    # Run setup
    docker exec -it jarvis-app bash /workspace/scripts/setup-cron.sh

    Write-Host ""
    Write-Host "✓ Cron setup complete!"
} else {
    Write-Host ""
    Write-Host "Skipping automatic setup."
    Write-Host "Follow the instructions above to set up manually."
}

Write-Host ""
