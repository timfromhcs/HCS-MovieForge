<#
.SYNOPSIS
    Integration test harness for TRELLIS.2 3D mesh generation via trellis-cli.
.DESCRIPTION
    Runs trellis-cli with TRELLIS.2 Q4 weights, generates a real 3D mesh GLB,
    and validates the output with validate_glb.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName

$TrellisCli = Join-Path $ProjectRoot "bin\trellis-cpp\trellis-cli.exe"
$ModelsDir = Join-Path $ProjectRoot "models\3d_trellis2_q4\q4"
$InputImage = Join-Path $ProjectRoot "runtime\test_shape_rgba.png"
$OutGlb = Join-Path $ProjectRoot "runtime\test_trellis_output.glb"

if (-not (Test-Path $TrellisCli)) {
    Write-Host "[FAIL] trellis-cli binary not found at $TrellisCli" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ModelsDir)) {
    Write-Host "[FAIL] Trellis models directory not found: $ModelsDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $InputImage)) {
    # Generate test RGBA shape if not present
    python -c "
from PIL import Image, ImageDraw
img = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.ellipse([100, 100, 412, 412], fill=(220, 60, 40, 255), outline=(255, 200, 50, 255), width=8)
draw.rectangle([200, 200, 312, 312], fill=(40, 120, 220, 255))
img.save(r'$InputImage')
"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Testing TRELLIS.2 3D Mesh Worker     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-Path $OutGlb) {
    Remove-Item $OutGlb -Force
}

$ArgsList = @(
    "--image", $InputImage,
    "--output", $OutGlb,
    "-m", $ModelsDir,
    "--steps", "1",
    "--res", "512",
    "--backend", "CPU",
    "--no-texture",
    "--box-uv"
)

$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
& $TrellisCli @ArgsList
$ExitCode = $LASTEXITCODE
$Stopwatch.Stop()

if ($ExitCode -ne 0 -or -not (Test-Path $OutGlb)) {
    Write-Host "[FAIL] Trellis generation failed (ExitCode: $ExitCode)" -ForegroundColor Red
    exit 1
}

# Run GLB validator
$ValOutput = python -c "from packages.validators.src.mesh_validator import validate_glb; res = validate_glb(r'$OutGlb'); print(f'{res.is_valid}|{res.vertex_count}|{res.face_count}')"
$Parts = $ValOutput.Trim().Split('|')
if ($Parts[0] -eq "True") {
    Write-Host "[PASS] TRELLIS.2 3D mesh generated & validated cleanly in $($Stopwatch.Elapsed.TotalSeconds.ToString('F2'))s (Vertices: $($Parts[1]), Faces: $($Parts[2]))" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[FAIL] Generated GLB failed validation: $ValOutput" -ForegroundColor Red
    exit 1
}
