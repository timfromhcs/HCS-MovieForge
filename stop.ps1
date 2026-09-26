<#
.SYNOPSIS
    Gracefully stops HCS MovieForge Supervisor and its child processes.
.DESCRIPTION
    Reads runtime/supervisor.pid and runtime/service-state.json.
    Sends graceful shutdown request, waits for children, then terminates only
    tracked MovieForge processes if needed. Never kills unrelated system processes.
#>

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $ScriptDir "runtime"
$PidFile = Join-Path $RuntimeDir "supervisor.pid"
$StateFile = Join-Path $RuntimeDir "service-state.json"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HCS MovieForge - Stopping Services    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$TrackedPids = @()

if (Test-Path $StateFile) {
    try {
        $State = Get-Content $StateFile -Raw | ConvertFrom-Json
        if ($State.pids) {
            foreach ($p in $State.pids) {
                $TrackedPids += [int]$p
            }
        }
    } catch {
        Write-Host "[MovieForge] Warning: Could not parse service-state.json" -ForegroundColor Yellow
    }
}

if (Test-Path $PidFile) {
    $SupPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($SupPid) {
        $TrackedPids += [int]$SupPid
    }
}

$TrackedPids = $TrackedPids | Select-Object -Unique

if ($TrackedPids.Count -eq 0) {
    Write-Host "[MovieForge] No running supervisor or worker instances found." -ForegroundColor Green
    exit 0
}

Write-Host "[MovieForge] Tracked processes to stop: $($TrackedPids -join ', ')" -ForegroundColor Yellow

# Attempt graceful termination first
foreach ($p in $TrackedPids) {
    $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "[MovieForge] Requesting graceful stop for PID $p ($($proc.ProcessName))..." -ForegroundColor Gray
        $proc.CloseMainWindow() | Out-Null
    }
}

# Wait up to 5 seconds
$TimeoutSeconds = 5
$StartTime = Get-Date

foreach ($p in $TrackedPids) {
    $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
    if ($proc) {
        $Elapsed = (Get-Date) - $StartTime
        $Remaining = $TimeoutSeconds - [int]$Elapsed.TotalSeconds
        if ($Remaining -gt 0) {
            $proc.WaitForExit($Remaining * 1000) | Out-Null
        }
    }
}

# Force kill any still running tracked processes
foreach ($p in $TrackedPids) {
    $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
    if ($proc -and -not $proc.HasExited) {
        Write-Host "[MovieForge] Force terminating remaining tracked PID $p..." -ForegroundColor Red
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
    }
}

# Cleanup runtime PID and state files
if (Test-Path $PidFile) {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}
if (Test-Path $StateFile) {
    Remove-Item $StateFile -Force -ErrorAction SilentlyContinue
}

Write-Host "[MovieForge] All MovieForge processes stopped cleanly." -ForegroundColor Green
