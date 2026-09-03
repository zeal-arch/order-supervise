# Order Supervisor - Unified In-Terminal Launcher (No Separate Windows)
# All services run in the background within this terminal session.

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Starting Order Supervisor Services (In-Terminal)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Temporal Server
Write-Host "[1/4] Starting Temporal Server on port 7233..." -ForegroundColor Yellow
$TemporalProc = Start-Process -FilePath ".\.venv\Scripts\temporal.exe" `
    -ArgumentList "server", "start-dev", "--port", "7233", "--ui-port", "8233", "--ip", "127.0.0.1" `
    -PassThru -NoNewWindow

Start-Sleep -Seconds 2

# 2. FastAPI Backend
Write-Host "[2/4] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
$ApiProc = Start-Process -FilePath ".\.venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "apps.api.app.main:app", "--port", "8000", "--host", "127.0.0.1" `
    -PassThru -NoNewWindow

# 3. Temporal Worker
Write-Host "[3/4] Starting Temporal Worker..." -ForegroundColor Yellow
$WorkerProc = Start-Process -FilePath ".\.venv\Scripts\python.exe" `
    -ArgumentList "-m", "temporal.worker" `
    -PassThru -NoNewWindow

# 4. Next.js Frontend
Write-Host "[4/4] Starting Next.js Web UI on http://localhost:3000..." -ForegroundColor Yellow
$WebProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm run dev" `
    -WorkingDirectory "$Root\apps\web" `
    -PassThru -NoNewWindow

Write-Host "`nAll 4 services running directly inside VS Code!" -ForegroundColor Green
Write-Host "  - Frontend UI:   http://localhost:3000" -ForegroundColor White
Write-Host "  - Backend API:   http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  - Temporal UI:   http://localhost:8233" -ForegroundColor White
Write-Host "`nPress Ctrl+C in this terminal to stop all services.`n" -ForegroundColor Cyan

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`nStopping all Order Supervisor services..." -ForegroundColor Yellow
    if ($TemporalProc) { Stop-Process -Id $TemporalProc.Id -Force -ErrorAction SilentlyContinue }
    if ($ApiProc) { Stop-Process -Id $ApiProc.Id -Force -ErrorAction SilentlyContinue }
    if ($WorkerProc) { Stop-Process -Id $WorkerProc.Id -Force -ErrorAction SilentlyContinue }
    if ($WebProc) { Stop-Process -Id $WebProc.Id -Force -ErrorAction SilentlyContinue }
    
    # Also clean up any node/uvicorn subprocesses on standard ports
    Get-Process -Name "temporal", "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "All services stopped cleanly." -ForegroundColor Green
}
