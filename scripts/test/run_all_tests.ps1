<#
.SYNOPSIS
    Runs the complete test suite (unit tests, doctor check, and all backend integration harnesses).
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   HCS MovieForge - Full Test Suite     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Doctor verification
Write-Host "`n[1/8] Running movieforge doctor..." -ForegroundColor Yellow
python "$ProjectRoot\apps\cli\src\main.py" doctor
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Doctor check failed." -ForegroundColor Red
    exit 1
}

# 2. Pytest unit test suite
Write-Host "`n[2/8] Running pytest unit tests..." -ForegroundColor Yellow
python -m pytest "$ProjectRoot\tests\unit" -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Unit tests failed." -ForegroundColor Red
    exit 1
}

# 3. Headless Blender harness
Write-Host "`n[3/8] Running Blender integration harness..." -ForegroundColor Yellow
& "$ProjectRoot\scripts\test\test_blender.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Blender integration failed." -ForegroundColor Red
    exit 1
}

# 4. FFmpeg / FFprobe harness
Write-Host "`n[4/8] Running FFmpeg integration harness..." -ForegroundColor Yellow
& "$ProjectRoot\scripts\test\test_ffmpeg.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] FFmpeg integration failed." -ForegroundColor Red
    exit 1
}

# 5. Whisper STT harness
Write-Host "`n[5/8] Running Whisper STT integration harness..." -ForegroundColor Yellow
& "$ProjectRoot\scripts\test\test_whisper.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Whisper integration failed." -ForegroundColor Red
    exit 1
}

# 6. Piper Neural TTS harness
Write-Host "`n[6/8] Running Piper Neural TTS integration harness..." -ForegroundColor Yellow
& "$ProjectRoot\scripts\test\test_piper.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Piper TTS integration failed." -ForegroundColor Red
    exit 1
}

# 7. Bonsai FLUX.2 Klein Image harness
Write-Host "`n[7/8] Running Bonsai FLUX.2 Klein image harness..." -ForegroundColor Yellow
& "$ProjectRoot\scripts\test\test_bonsai.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Bonsai image integration failed." -ForegroundColor Red
    exit 1
}

# 8. Qwen3-VL 8B Multimodal Agent harness
Write-Host "`n[8/8] Running Qwen3-VL multimodal agent harness..." -ForegroundColor Yellow
& "$ProjectRoot\scripts\test\test_qwen3_vl.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Qwen3-VL integration failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  ALL TESTS & INTEGRATION HARNESSES PASSED  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
