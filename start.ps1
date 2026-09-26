<#
.SYNOPSIS
    Starts HCS MovieForge Supervisor and Control Plane services.
.DESCRIPTION
    Launches the supervisor process, writes PID to runtime/supervisor.pid,
    and initializes service-state.json.
#>

param(
    [switch]$Headless = $false,
    [switch]$Daemon = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$RuntimeDir = Join-Path $ScriptDir "runtime"
if (-not (Test-Path $RuntimeDir)) {
    New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
}

$PidFile = Join-Path $RuntimeDir "supervisor.pid"
if (Test-Path $PidFile) {
    $ExistingPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($ExistingPid) {
        $Process = Get-Process -Id $ExistingPid -ErrorAction SilentlyContinue
        if ($Process) {
            Write-Host "[MovieForge] Supervisor already running with PID $ExistingPid" -ForegroundColor Yellow
            exit 0
        }
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HCS MovieForge - Starting Supervisor  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Set Python path to include root
$env:PYTHONPATH = "$ScriptDir;$env:PYTHONPATH"

# Launch supervisor
$ArgsList = @("-m", "engine.supervisor.main")
if ($Headless) {
    $ArgsList += "--headless"
}

if ($Daemon) {
    $Proc = Start-Process -FilePath "python" -ArgumentList $ArgsList -PassThru -NoNewWindow
    Set-Content -Path $PidFile -Value $Proc.Id
    Write-Host "[MovieForge] Supervisor started in background (PID $($Proc.Id))." -ForegroundColor Green
} else {
    # Run in foreground and save current PID
    Set-Content -Path $PidFile -Value $PID
    try {
        & python -m engine.supervisor.main @ArgsList
    } finally {
        if (Test-Path $PidFile) {
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        }
    }
}
