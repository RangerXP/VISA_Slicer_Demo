param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Stop-ServerOnPort {
    param(
        [Parameter(Mandatory = $true)][int]$ListenPort
    )

    $listeners = Get-NetTCPConnection -LocalPort $ListenPort -State Listen -ErrorAction SilentlyContinue
    if (-not $listeners) {
        Write-Host "No demo server listener found on port $ListenPort."
        return
    }

    $stopped = @()
    foreach ($listener in $listeners) {
        try {
            Stop-Process -Id $listener.OwningProcess -Force -ErrorAction Stop
            $stopped += $listener.OwningProcess
        } catch {
            Write-Host "Failed to stop PID $($listener.OwningProcess) on port ${ListenPort}: $($_.Exception.Message)"
        }
    }

    if ($stopped.Count -gt 0) {
        $uniqueIds = $stopped | Sort-Object -Unique
        Write-Host "Stopped demo server process(es) on port ${ListenPort}: $($uniqueIds -join ', ')"
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$stdoutLog = Join-Path $repoRoot ".demo-server.out.log"
$stderrLog = Join-Path $repoRoot ".demo-server.err.log"

Stop-ServerOnPort -ListenPort $Port

if (Test-Path $stdoutLog) {
    Remove-Item $stdoutLog -Force
    Write-Host "Removed $stdoutLog"
}

if (Test-Path $stderrLog) {
    Remove-Item $stderrLog -Force
    Write-Host "Removed $stderrLog"
}