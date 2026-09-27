<#
.SYNOPSIS
    Integration test harness for Qwen3-VL 8B Instruct multimodal agent via llama.cpp.
.DESCRIPTION
    Runs llama-mtmd-cli with the Qwen3-VL 8B Q4_K_M GGUF model and F16 multimodal projector,
    inspects a test image, and validates that structured text is generated.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName

$LlamaCli = Join-Path $ProjectRoot "bin\llama-cpp\llama-mtmd-cli.exe"
$ModelFile = Join-Path $ProjectRoot "models\agent_qwen3-vl_8b_q4km\Qwen3VL-8B-Instruct-Q4_K_M.gguf"
$MmprojFile = Join-Path $ProjectRoot "models\agent_qwen3-vl_8b_q4km\mmproj-Qwen3VL-8B-Instruct-F16.gguf"
$TestImage = Join-Path $ProjectRoot "runtime\test_bonsai_robot.png"

if (-not (Test-Path $LlamaCli)) {
    Write-Host "[FAIL] llama-mtmd-cli binary not found at $LlamaCli" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ModelFile)) {
    Write-Host "[FAIL] Qwen3-VL model file not found: $ModelFile" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $MmprojFile)) {
    Write-Host "[FAIL] Qwen3-VL mmproj file not found: $MmprojFile" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $TestImage)) {
    Write-Host "[FAIL] Test image not found: $TestImage" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Testing Qwen3-VL 8B Multimodal Agent " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ArgsList = @(
    "-m", $ModelFile,
    "--mmproj", $MmprojFile,
    "--image", $TestImage,
    "--jinja",
    "-sys", "You are a concise visual inspector. Answer with exactly one descriptive sentence, no greetings.",
    "-p", "Describe this image in one concise sentence.",
    "-c", "2048",
    "-n", "64",
    "--no-warmup",
    "-ngl", "33"
)

$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$RawOutput = & $LlamaCli @ArgsList 2>&1
$ExitCode = $LASTEXITCODE
$Stopwatch.Stop()

$OutLines = @($RawOutput | ForEach-Object { "$($_)" })
$ContentLines = @($OutLines | Where-Object { $_ -notmatch '^\d+\.\d+\.\d+' -and $_.Trim() -ne "" })
$CutIndex = -1
for ($i = 0; $i -lt $ContentLines.Count; $i++) {
    if ($ContentLines[$i] -match 'im_end' -or ($ContentLines[$i] -match 'assistant' -and $ContentLines[$i] -match '<\|')) { $CutIndex = $i }
}
if ($CutIndex -ge 0 -and ($CutIndex + 1) -lt $ContentLines.Count) { $ContentLines = $ContentLines[($CutIndex + 1)..($ContentLines.Count - 1)] }
$ResultSentence = (($ContentLines | ForEach-Object { $_ -replace '<\|[^|]*\|>', '' }) | Out-String).Trim()

if ($ExitCode -eq 0 -and $ResultSentence.Length -gt 5) {
    Write-Host "[PASS] Qwen3-VL multimodal inspection succeeded in $($Stopwatch.Elapsed.TotalSeconds.ToString('F2'))s" -ForegroundColor Green
    Write-Host "VLM Analysis: $ResultSentence" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "[FAIL] Qwen3-VL multimodal inspection failed (ExitCode: $ExitCode)" -ForegroundColor Red
    Write-Host ($OutLines -join "`n")
    exit 1
}
