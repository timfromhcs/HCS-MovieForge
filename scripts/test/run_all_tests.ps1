<#
.SYNOPSIS
    Runs the complete test suite (unit tests, doctor check, and available backend integration harnesses).
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   HCS MovieForge - Full Test Suite     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Doctor verification
Write-Host "`n[1/3] Running movieforge doctor..." -ForegroundColor Yellow
python "$ProjectRoot\apps\cli\src\main.py" doctor
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Doctor check failed." -ForegroundColor Red
    exit 1
}

# 2. Pytest unit test suite
Write-Host "`n[2/3] Running pytest unit tests..." -ForegroundColor Yellow
python -m pytest "$ProjectRoot\tests\unit" -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Unit tests failed." -ForegroundColor Red
    exit 1
}

# 3. Headless integration harnesses
Write-Host "`n[3/3] Running headless integration harnesses..." -ForegroundColor Yellow
& "$ProjectRoot\scripts\test\test_blender.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Blender integration failed." -ForegroundColor Red
    exit 1
}

& "$ProjectRoot\scripts\test\test_ffmpeg.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] FFmpeg integration failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  ALL TESTS & INTEGRATION CHECKS PASSED  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
