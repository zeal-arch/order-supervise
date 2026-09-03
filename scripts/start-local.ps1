# Order Supervisor - Unified In-Terminal Launcher (No Separate Windows)
# All services run in the background within this terminal session.

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Starting Order Supervisor Services (In-Terminal)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Temporal Server
Write-Host "[1/4] Starting Temporal Server on port 7233..." -ForegroundColor Yellow

$TemporalCmd = $null
if (Test-Path ".\.venv\Scripts\temporal.exe") {
    $TemporalCmd = ".\.venv\Scripts\temporal.exe"
} elseif (Get-Command "temporal" -ErrorAction SilentlyContinue) {
    $TemporalCmd = "temporal"
} elseif (Get-Command "temporal.exe" -ErrorAction SilentlyContinue) {
    $TemporalCmd = "temporal.exe"
} else {
    Write-Host "    Temporal CLI not found. Auto-downloading standalone Temporal server..." -ForegroundColor Cyan
    try {
        $DownloadUrl = "https://temporal.download/cli/archive/latest?platform=windows&arch=amd64"
        $TempZip = Join-Path $env:TEMP "temporal_cli.zip"
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempZip -UseBasicParsing
        $TargetDir = Join-Path $Root ".venv\Scripts"
        if (-not (Test-Path $TargetDir)) {
            New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
        }
        Expand-Archive -Path $TempZip -DestinationPath $TargetDir -Force
        Remove-Item $TempZip -Force -ErrorAction SilentlyContinue

        if (Test-Path ".\.venv\Scripts\temporal.exe") {
            $TemporalCmd = ".\.venv\Scripts\temporal.exe"
            Write-Host "    [OK] Temporal CLI auto-installed to .venv\Scripts\temporal.exe" -ForegroundColor Green
        }
    } catch {
        Write-Host "    [!] Auto-download failed ($($_.Exception.Message)). Attempting Docker fallback..." -ForegroundColor Yellow
        docker-compose up -d temporal 2>$null | Out-Null
    }
}

$TemporalProc = $null
if ($TemporalCmd) {
    $TemporalProc = Start-Process -FilePath $TemporalCmd `
        -ArgumentList "server", "start-dev", "--port", "7233", "--ui-port", "8233", "--ip", "127.0.0.1" `
        -PassThru -NoNewWindow
}

# Wait for Temporal Server port 7233 to open (up to 15 seconds)
for ($i = 0; $i -lt 30; $i++) {
    try {
        $TcpClient = New-Object System.Net.Sockets.TcpClient
        $AsyncResult = $TcpClient.BeginConnect("127.0.0.1", 7233, $null, $null)
        $Success = $AsyncResult.AsyncWaitHandle.WaitOne(300)
        if ($Success -and $TcpClient.Connected) {
            $TcpClient.EndConnect($AsyncResult)
            $TcpClient.Close()
            break
        }
        $TcpClient.Close()
    } catch {}
    Start-Sleep -Milliseconds 500
}

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
    
    # Also clean up any node/uvicorn/temporal subprocesses
    Get-Process -Name "temporal", "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "All services stopped cleanly." -ForegroundColor Green
}
