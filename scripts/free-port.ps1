param(
    [int]$Port = 8000
)
$ErrorActionPreference = "Continue"
$conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $conns) {
    Write-Host "Nothing is listening on port $Port."
    exit 0
}
$ids = $conns.OwningProcess | Sort-Object -Unique
foreach ($procId in $ids) {
    Write-Host "Stopping PID $procId (port $Port)"
    try {
        Stop-Process -Id $procId -Force -ErrorAction Stop
    } catch {
        Write-Warning "Could not stop PID ${procId}: $_"
        Write-Host "Try: taskkill /PID $procId /F /T   (run PowerShell as Administrator if needed)"
    }
}
Start-Sleep -Seconds 1
$left = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($left) {
    Write-Warning "Port $Port may still be in use. Check: netstat -ano | findstr `":$Port`""
} else {
    Write-Host "Port $Port is free."
}
