param(
    [string]$WorkspaceRoot = (Get-Location)
)

$paths = @(
    ".bmad",
    ".bmad/core",
    ".bmad/core/agents",
    "docs/sprints"
)

foreach ($p in $paths) {
    $full = Join-Path $WorkspaceRoot $p
    if (-not (Test-Path $full)) { New-Item -ItemType Directory -Path $full -Force | Out-Null }
}

Write-Host "BMAD workspace initialized at $WorkspaceRoot"
Write-Host "Created directories: $($paths -join ', ')"
Write-Host "Files created: .bmad/config.yaml, .bmad/core/agents/bmad-master.md, docs/sprints/sprint-template.md"
Write-Host "Run `powershell -ExecutionPolicy Bypass -File .\scripts\init-bmad.ps1` to re-run this script."
