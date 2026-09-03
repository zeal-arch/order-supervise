# Order Supervisor - Stop All Local Services
Write-Host "Stopping any running Order Supervisor services..." -ForegroundColor Yellow

# Kill Temporal, Python workers, and Next.js processes
Get-Process -Name "temporal" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Kill processes on standard ports (8000, 7233, 8233, 3000)
$Ports = @(8000, 7233, 8233, 3000)
foreach ($Port in $Ports) {
    $Connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($Conn in $Connections) {
        if ($Conn.OwningProcess -and $Conn.OwningProcess -ne 0) {
            Stop-Process -Id $Conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "All background services stopped." -ForegroundColor Green
