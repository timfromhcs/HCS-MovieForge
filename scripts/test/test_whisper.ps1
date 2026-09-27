<#
.SYNOPSIS
    Integration test harness for Whisper.cpp speech-to-text.
.DESCRIPTION
    Generates a 16kHz WAV file using FFmpeg, feeds it to whisper-cli with
    the verified ggml-base model, and validates transcription execution.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName

$WhisperBin = Join-Path $ProjectRoot "bin\whisper-cpp\whisper-cli.exe"
$ModelFile = Join-Path $ProjectRoot "models\stt_whisper_base\ggml-base.bin"
$FFmpeg = (Get-Command ffmpeg.exe -ErrorAction SilentlyContinue).Source

if (-not (Test-Path $WhisperBin)) {
    Write-Host "[FAIL] Whisper binary not found: $WhisperBin" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ModelFile)) {
    Write-Host "[FAIL] Whisper base model not found: $ModelFile" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Testing Whisper.cpp STT Execution    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$TestWav = Join-Path $ProjectRoot "runtime\test_whisper_input.wav"

# Generate 2 seconds of 16kHz mono audio (required format for Whisper)
& $FFmpeg -y -f lavfi -i "sine=frequency=440:duration=2" -ar 16000 -ac 1 -c:a pcm_s16le $TestWav | Out-Null

$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$Proc = Start-Process -FilePath $WhisperBin -ArgumentList @("-m", $ModelFile, "-f", $TestWav, "-nt") -PassThru -NoNewWindow -Wait
$Stopwatch.Stop()

Remove-Item $TestWav -Force -ErrorAction SilentlyContinue

if ($Proc.ExitCode -eq 0) {
    Write-Host "[PASS] Whisper STT executed cleanly in $($Stopwatch.Elapsed.TotalSeconds.ToString('F2'))s" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[FAIL] Whisper STT execution failed (ExitCode: $($Proc.ExitCode))" -ForegroundColor Red
    exit 1
}
