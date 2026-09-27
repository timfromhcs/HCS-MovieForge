<#
.SYNOPSIS
    Integration test harness for Piper neural text-to-speech.
.DESCRIPTION
    Synthesizes speech from a test dialogue line using the verified Piper Lessac voice,
    and validates the generated WAV file with validate_audio.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName

$VoiceModel = Join-Path $ProjectRoot "models\voice_piper_en_lessac_medium\en\en_US\lessac\medium\en_US-lessac-medium.onnx"
$VoiceConfig = Join-Path $ProjectRoot "models\voice_piper_en_lessac_medium\en\en_US\lessac\medium\en_US-lessac-medium.onnx.json"
$OutWav = Join-Path $ProjectRoot "runtime\test_piper_dialogue.wav"

if (-not (Test-Path $VoiceModel)) {
    Write-Host "[FAIL] Piper voice model not found: $VoiceModel" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "     Testing Piper Neural TTS Worker    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-Path $OutWav) {
    Remove-Item $OutWav -Force
}

$TestLine = "Welcome to HCS MovieForge. All AI production pipelines are fully operational."

$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$TestLine | python -m piper -m $VoiceModel -c $VoiceConfig -f $OutWav
$ExitCode = $LASTEXITCODE
$Stopwatch.Stop()

if ($ExitCode -ne 0 -or -not (Test-Path $OutWav)) {
    Write-Host "[FAIL] Piper TTS synthesis failed (ExitCode: $ExitCode)" -ForegroundColor Red
    exit 1
}

# Run audio validator
$ValOutput = python -c "from packages.validators.src.audio_validator import validate_audio; res = validate_audio(r'$OutWav'); print(f'{res.is_valid}|{res.duration_sec}|{res.sample_rate}|{res.channels}')"
$Parts = $ValOutput.Trim().Split('|')
if ($Parts[0] -eq "True") {
    Write-Host "[PASS] Piper TTS generated & validated in $($Stopwatch.Elapsed.TotalSeconds.ToString('F2'))s (Duration: $($Parts[1])s, Sample Rate: $($Parts[2])Hz, Channels: $($Parts[3]))" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[FAIL] Generated WAV failed validation: $ValOutput" -ForegroundColor Red
    exit 1
}
