# Local 5-minute rotating SpiderRock scan loop (requires SPIDERROCK_API_KEY in env).
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

if (-not $env:SPIDERROCK_API_KEY) {
    Write-Error "Set SPIDERROCK_API_KEY before starting the loop."
}

Write-Host "Rotating scan loop: every 5 minutes. Ctrl+C to stop."
Write-Host "Repo: $RepoRoot"

while ($true) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host ""
    Write-Host "=== ROTATING SCAN TICK $stamp ==="
    python -u sniper_scanner/rotating_scan.py
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Scan exited with code $LASTEXITCODE"
    }
    if (Test-Path "scan_runs/latest_summary.json") {
        Get-Content "scan_runs/latest_summary.json" -Raw | Write-Host
    }
    Write-Host "AGENT_LOOP_TICK_rotating_scan {\"prompt\":\"Review rotating scan latest_summary.json and report top hits/errors to user.\"}"
    Start-Sleep -Seconds 300
}
