# BMAD Workflow Initialization Script
# This script sets up agentic and formatting settings for your workspace

param(
    [string]$WorkspaceRoot = (Get-Location)
)

Write-Host "Initializing BMAD workflow..."

# Reference settings.json for agentic and formatting preferences
$settingsPath = Join-Path $WorkspaceRoot ".vscode\settings.json"
if (Test-Path $settingsPath) {
    Write-Host "Found VS Code settings: $settingsPath"
    Write-Host "Agentic features and formatters will follow workspace settings."
} else {
    Write-Host "No .vscode/settings.json found. Please add one for best results."
}

Write-Host "Workflow initialization complete."
