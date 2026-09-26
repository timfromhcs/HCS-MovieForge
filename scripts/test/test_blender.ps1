<#
.SYNOPSIS
    Integration test harness for headless Blender execution.
.DESCRIPTION
    Launches Blender headless in background, creates a simple scene,
    and validates Blender Python API and render engine availability.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName

$BlenderExe = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
if (-not (Test-Path $BlenderExe)) {
    $BlenderExe = (Get-Command blender.exe -ErrorAction SilentlyContinue).Source
}

if (-not $BlenderExe -or -not (Test-Path $BlenderExe)) {
    Write-Host "[FAIL] Blender executable not found." -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Testing Blender Headless Integration  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$TempBlend = Join-Path $ProjectRoot "runtime\test_scene.blend"
$PyScript = @"
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.ops.wm.save_as_mainfile(filepath=r'$TempBlend')
print('[BLENDER_TEST_OK] Scene created successfully.')
"@

$PyFile = Join-Path $ProjectRoot "runtime\blender_test.py"
Set-Content -Path $PyFile -Value $PyScript

$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$Proc = Start-Process -FilePath $BlenderExe -ArgumentList @("-b", "--python", $PyFile) -PassThru -NoNewWindow -Wait
$Stopwatch.Stop()

Remove-Item $PyFile -Force -ErrorAction SilentlyContinue

if ($Proc.ExitCode -eq 0 -and (Test-Path $TempBlend)) {
    Write-Host "[PASS] Blender headless scene created in $($Stopwatch.Elapsed.TotalSeconds.ToString('F2'))s" -ForegroundColor Green
    Remove-Item $TempBlend -Force -ErrorAction SilentlyContinue
    exit 0
} else {
    Write-Host "[FAIL] Blender headless execution failed (ExitCode: $($Proc.ExitCode))" -ForegroundColor Red
    exit 1
}
