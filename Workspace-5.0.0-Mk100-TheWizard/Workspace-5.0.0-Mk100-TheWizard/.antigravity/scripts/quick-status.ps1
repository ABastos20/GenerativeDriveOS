# Quick status check for Antigravity
# Shows: Git status, Docker status, Recent sprint files

Write-Host "=== Jarvis Workspace Quick Status ===" -ForegroundColor Cyan

# Git Status
Write-Host "`n[Git Status]" -ForegroundColor Yellow
git status --short

# Current Branch
$branch = git rev-parse --abbrev-ref HEAD
Write-Host "`n[Current Branch] $branch" -ForegroundColor Green

# Recent Sprint Files
Write-Host "`n[Recent Sprint Activity]" -ForegroundColor Yellow
Get-ChildItem -Path "docs\sprints" -Filter "*.md" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 5 | 
    ForEach-Object { 
        Write-Host "  - $($_.Name) (Modified: $($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm')))"
    }

# Docker Status (if available)
Write-Host "`n[Docker Status]" -ForegroundColor Yellow
try {
    $containers = docker ps --format "table {{.Names}}`t{{.Status}}" 2>$null
    if ($containers) {
        Write-Host $containers
    } else {
        Write-Host "  No containers running or Docker not available"
    }
} catch {
    Write-Host "  Docker not available"
}

Write-Host "`n[+] Status check complete!" -ForegroundColor Green
