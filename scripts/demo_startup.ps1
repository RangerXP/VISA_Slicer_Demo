param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$NoBrowser,
    [switch]$SkipTokenWarmup,
    [switch]$UseDefaultBrowser
)

$ErrorActionPreference = "Stop"

function Test-PythonInstalled {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Python is not installed or not on PATH."
    }

    return $pythonCommand.Source
}

function Assert-LocalCredentialFile {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )

    $envPath = Join-Path $RepoRoot ".env.local"
    if (-not (Test-Path $envPath)) {
        throw ".env.local was not found. Copy .env.local.example to .env.local and fill in the real Power BI credentials first."
    }

    $secretLine = Get-Content $envPath | Where-Object { $_ -match '^PBI_CLIENT_SECRET=' } | Select-Object -First 1
    if (-not $secretLine) {
        throw ".env.local is missing PBI_CLIENT_SECRET."
    }

    $secretValue = ($secretLine -replace '^PBI_CLIENT_SECRET=', '').Trim()
    if (-not $secretValue -or $secretValue -eq 'YOUR_SECRET_VALUE_HERE') {
        throw ".env.local does not contain a real PBI_CLIENT_SECRET value."
    }
}

function Stop-ServerOnPort {
    param(
        [Parameter(Mandatory = $true)][int]$ListenPort
    )

    $listener = Get-NetTCPConnection -LocalPort $ListenPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        Stop-Process -Id $listener.OwningProcess -Force
        Write-Host "Stopped existing listener on port $ListenPort (PID $($listener.OwningProcess))."
    }
}

function Start-DemoServerProcess {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$PythonPath,
        [Parameter(Mandatory = $true)][string]$HostName,
        [Parameter(Mandatory = $true)][int]$Port
    )

    $serverScript = Join-Path $RepoRoot "src\demo_server.py"
    $stdoutLog = Join-Path $RepoRoot ".demo-server.out.log"
    $stderrLog = Join-Path $RepoRoot ".demo-server.err.log"

    if (Test-Path $stdoutLog) {
        Remove-Item $stdoutLog -Force
    }

    if (Test-Path $stderrLog) {
        Remove-Item $stderrLog -Force
    }

    $arguments = @(
        ('"{0}"' -f $serverScript),
        "--host",
        $HostName,
        "--port",
        $Port
    )
    $process = Start-Process -FilePath $PythonPath -ArgumentList $arguments -WorkingDirectory $RepoRoot -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -WindowStyle Hidden -PassThru
    Write-Host "Started demo server (PID $($process.Id))."

    return @{
        Process = $process
        StdOutLog = $stdoutLog
        StdErrLog = $stderrLog
    }
}

function Wait-ForDemoServer {
    param(
        [Parameter(Mandatory = $true)][string]$HealthUrl,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-RestMethod -Uri $HealthUrl -Method Get -TimeoutSec 5
            if ($response.status -eq 'ok') {
                return $true
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }

    return $false
}

function Test-EmbedTokenEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$TokenUrl
    )

    $response = Invoke-RestMethod -Uri $TokenUrl -Method Get -TimeoutSec 20
    if (-not $response.token) {
        throw "The embed token endpoint returned no token."
    }

    Write-Host "Embed token endpoint OK. Token expires at $($response.expiresAt)."
}

function Get-EdgeExecutablePath {
    $candidatePaths = @(
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
        "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe"
    )

    foreach ($candidate in $candidatePaths) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    return $null
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Test-PythonInstalled
Assert-LocalCredentialFile -RepoRoot $repoRoot
Stop-ServerOnPort -ListenPort $Port

$serverState = Start-DemoServerProcess -RepoRoot $repoRoot -PythonPath $pythonPath -HostName $HostName -Port $Port

$healthUrl = "http://${HostName}:${Port}/api/health"
$tokenUrl = "http://${HostName}:${Port}/api/embed-token"
$pageUrl = "http://${HostName}:${Port}/pbi-app-injection-demo.html"

if (-not (Wait-ForDemoServer -HealthUrl $healthUrl -TimeoutSeconds 15)) {
    Write-Host "Server did not become healthy within 15 seconds."
    if (Test-Path $serverState.StdErrLog) {
        Write-Host "--- Server stderr ---"
        Get-Content $serverState.StdErrLog
    }
    throw "Demo server failed to start."
}

Write-Host "Demo server is healthy at $healthUrl"

if (-not $SkipTokenWarmup) {
    Test-EmbedTokenEndpoint -TokenUrl $tokenUrl
}

Write-Host "Demo page: $pageUrl"
Write-Host "Server stdout log: $($serverState.StdOutLog)"
Write-Host "Server stderr log: $($serverState.StdErrLog)"

if (-not $NoBrowser) {
    $edgePath = if ($UseDefaultBrowser) { $null } else { Get-EdgeExecutablePath }
    if ($edgePath) {
        Write-Host "Opening demo in Microsoft Edge."
        Start-Process -FilePath $edgePath -ArgumentList @($pageUrl) | Out-Null
    } else {
        Write-Host "Microsoft Edge was not found. Opening the default browser instead."
        Start-Process $pageUrl | Out-Null
    }
}