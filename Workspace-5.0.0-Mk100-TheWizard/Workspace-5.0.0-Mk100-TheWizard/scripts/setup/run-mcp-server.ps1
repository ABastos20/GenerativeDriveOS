# PowerShell script to run the MCP server locally and show health
python -m pip install -r requirements-mcp.txt

# Start MCP server in background
Start-Process -NoNewWindow -FilePath python -ArgumentList 'src/jarvis/mcp_server.py'

Start-Sleep -Seconds 2

# Query health endpoint
try {
	$resp = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/mcp/health' -UseBasicParsing -ErrorAction Stop
	Write-Host "MCP Health:" ($resp | ConvertTo-Json -Compress)
} catch {
	Write-Host "Failed to query MCP health endpoint:" $_.Exception.Message
}
