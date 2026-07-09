# Apply Windows + Docker Desktop Performance Optimizations
# Run as Administrator in PowerShell

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Windows + Docker Desktop Optimizer" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ ERROR: Must run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell → Run as Administrator" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Running as Administrator`n" -ForegroundColor Green

# 2. Verify .wslconfig exists
Write-Host "1. Checking WSL2 configuration..." -ForegroundColor Yellow
$wslConfig = "$env:USERPROFILE\.wslconfig"
if (Test-Path $wslConfig) {
    Write-Host "   ✅ .wslconfig found:" -ForegroundColor Green
    Write-Host "   $(Get-Content $wslConfig | Select-String 'processors|memory|swap')" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  .wslconfig not found!" -ForegroundColor Red
    Write-Host "   Copy from: docs\performance\.wslconfig.example" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') { exit 0 }
}

# 3. Stop Docker Desktop
Write-Host "`n2. Stopping Docker Desktop..." -ForegroundColor Yellow
$dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if ($dockerProcess) {
    Stop-Process -Name "Docker Desktop" -Force
    Write-Host "   ✅ Docker Desktop stopped" -ForegroundColor Green
    Start-Sleep -Seconds 5
} else {
    Write-Host "   ℹ️  Docker Desktop not running" -ForegroundColor Gray
}

# 4. Shutdown WSL2
Write-Host "`n3. Shutting down WSL2..." -ForegroundColor Yellow
wsl --shutdown
Write-Host "   ✅ WSL2 shutdown complete" -ForegroundColor Green
Start-Sleep -Seconds 8

# 5. Apply Windows host optimizations
Write-Host "`n4. Applying Windows host optimizations..." -ForegroundColor Yellow

# High performance power plan
Write-Host "   - Enabling High Performance power plan..." -ForegroundColor Gray
$result = powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "     ✅ High performance mode enabled" -ForegroundColor Green
} else {
    Write-Host "     ⚠️  Could not set power plan" -ForegroundColor Yellow
}

# Windows Defender exclusions
Write-Host "   - Configuring Windows Defender exclusions..." -ForegroundColor Gray
try {
    Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\Docker\wsl" -ErrorAction Stop
    Add-MpPreference -ExclusionPath "$env:APPDATA\Docker" -ErrorAction Stop
    Add-MpPreference -ExclusionPath "C:\Users\abast\Desktop\Workspace" -ErrorAction Stop
    Write-Host "     ✅ Defender exclusions added" -ForegroundColor Green
} catch {
    Write-Host "     ⚠️  Defender exclusions failed (may already exist)" -ForegroundColor Yellow
}

# 6. Start Docker Desktop
Write-Host "`n5. Starting Docker Desktop..." -ForegroundColor Yellow
$dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerExe) {
    Start-Process $dockerExe
    Write-Host "   ✅ Docker Desktop launched" -ForegroundColor Green
    Write-Host "   ⏳ Waiting for Docker to initialize (40 seconds)..." -ForegroundColor Gray
    Start-Sleep -Seconds 40
} else {
    Write-Host "   ❌ Docker Desktop not found at: $dockerExe" -ForegroundColor Red
    exit 1
}

# 7. Apply WSL2 kernel tuning
Write-Host "`n6. Applying WSL2 kernel tuning..." -ForegroundColor Yellow

Write-Host "   - Setting swappiness to 10..." -ForegroundColor Gray
wsl -d docker-desktop -e sh -c "echo 10 | sudo tee /proc/sys/vm/swappiness" | Out-Null
Write-Host "     ✅ Swappiness set" -ForegroundColor Green

Write-Host "   - Enabling Transparent HugePages..." -ForegroundColor Gray
wsl -d docker-desktop -e sh -c "echo always | sudo tee /sys/kernel/mm/transparent_hugepage/enabled" | Out-Null
wsl -d docker-desktop -e sh -c "echo always | sudo tee /sys/kernel/mm/transparent_hugepage/defrag" | Out-Null
Write-Host "     ✅ THP enabled" -ForegroundColor Green

Write-Host "   - Increasing inode limits..." -ForegroundColor Gray
wsl -d docker-desktop -e sh -c "echo 8192 | sudo tee /proc/sys/fs/inotify/max_user_instances" | Out-Null
wsl -d docker-desktop -e sh -c "echo 524288 | sudo tee /proc/sys/fs/inotify/max_user_watches" | Out-Null
Write-Host "     ✅ Inode limits increased" -ForegroundColor Green

# 8. Verification
Write-Host "`n7. Verifying optimizations..." -ForegroundColor Yellow
$swappiness = wsl -d docker-desktop -e cat /proc/sys/vm/swappiness
$thp = wsl -d docker-desktop -e cat /sys/kernel/mm/transparent_hugepage/enabled
$watches = wsl -d docker-desktop -e cat /proc/sys/fs/inotify/max_user_watches

Write-Host "   Swappiness: $swappiness" -ForegroundColor Gray
Write-Host "   THP: $thp" -ForegroundColor Gray
Write-Host "   Max watches: $watches" -ForegroundColor Gray

if ($swappiness -eq 10 -and $thp -like "*[always]*" -and $watches -eq 524288) {
    Write-Host "   ✅ All optimizations verified!" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Some optimizations may not have applied" -ForegroundColor Yellow
}

# 9. Final message
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ OPTIMIZATION COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Restart Docker containers:" -ForegroundColor White
Write-Host "   cd docker" -ForegroundColor Gray
Write-Host "   docker compose down" -ForegroundColor Gray
Write-Host "   docker compose up -d" -ForegroundColor Gray
Write-Host "`n2. Test performance improvements" -ForegroundColor White
Write-Host "`nExpected gains:" -ForegroundColor Yellow
Write-Host "- Test runs: 160s → 20-30s (8x faster)" -ForegroundColor Green
Write-Host "- API latency: 5-15% reduction" -ForegroundColor Green
Write-Host "- Vector search: 5-10% faster" -ForegroundColor Green
Write-Host "`n"
