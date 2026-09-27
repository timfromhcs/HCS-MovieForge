<#
.SYNOPSIS
    Integration test harness for Bonsai FLUX.2 Klein image generation via stable-diffusion.cpp.
.DESCRIPTION
    Runs sd-cli with the Bonsai Q2_K diffusion model, FLUX.2 VAE, and Qwen3 text encoder,
    generates a test image, and validates the output with the image validator.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName

$SdCli = Join-Path $ProjectRoot "bin\stable-diffusion-cpp\sd-cli.exe"
$DiffModel = Join-Path $ProjectRoot "models\image_bonsai_flux2-klein_q2k\bonsai-flux2-klein-ternary-q2_k.gguf"
$VaeModel = Join-Path $ProjectRoot "models\vae_flux2_dev\split_files\vae\flux2-vae.safetensors"
$TeModel = Join-Path $ProjectRoot "models\te_qwen3_4b_q2k\Qwen3-4B-Q2_K.gguf"
$OutImage = Join-Path $ProjectRoot "runtime\test_bonsai_robot.png"

if (-not (Test-Path $SdCli)) {
    Write-Host "[FAIL] sd-cli binary not found at $SdCli" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $DiffModel)) {
    Write-Host "[FAIL] Bonsai diffusion model not found: $DiffModel" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $VaeModel)) {
    Write-Host "[FAIL] FLUX.2 VAE not found: $VaeModel" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $TeModel)) {
    Write-Host "[FAIL] Qwen3 text encoder not found: $TeModel" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Testing Bonsai FLUX.2 Klein Worker   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-Path $OutImage) {
    Remove-Item $OutImage -Force
}

$ArgsList = @(
    "--diffusion-model", $DiffModel,
    "--vae", $VaeModel,
    "--llm", $TeModel,
    "-p", "a maintenance robot on a train platform in the rain, cinematic lighting, 8k",
    "-o", $OutImage,
    "-W", "256",
    "-H", "256",
    "--cfg-scale", "1.0",
    "--steps", "4",
    "-v",
    "--offload-to-cpu",
    "--diffusion-fa",
    "--vae-tiling"
)

$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
& $SdCli @ArgsList
$ExitCode = $LASTEXITCODE
$Stopwatch.Stop()

if ($ExitCode -ne 0 -or -not (Test-Path $OutImage)) {
    Write-Host "[FAIL] Bonsai generation failed (ExitCode: $ExitCode)" -ForegroundColor Red
    exit 1
}

# Run image validator
$ValOutput = python -c "from packages.validators.src.image_validator import validate_image; res = validate_image(r'$OutImage', expected_width=256, expected_height=256); print(res.is_valid)"
if ($ValOutput.Trim() -eq "True") {
    Write-Host "[PASS] Bonsai FLUX.2 Klein generation & validation succeeded in $($Stopwatch.Elapsed.TotalSeconds.ToString('F2'))s" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[FAIL] Generated image failed validation." -ForegroundColor Red
    exit 1
}
