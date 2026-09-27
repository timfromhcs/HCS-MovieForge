<#
.SYNOPSIS
    Downloads and extracts verified upstream Vulkan release binaries for MovieForge backends.
.DESCRIPTION
    Pulls pinned release assets using GitHub CLI:
    - stable-diffusion.cpp (win-vulkan-x64) from leejet/stable-diffusion.cpp
    - trellis.cpp (vulkan-windows-x64) from pwilkin/trellis.cpp
    - llama.cpp (win-vulkan-x64) from ggml-org/llama.cpp
    - whisper.cpp (win-x64) from ggml-org/whisper.cpp
#>

param(
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName
$BinDir = Join-Path $ProjectRoot "bin"
$TmpDir = Join-Path $ProjectRoot "runtime\downloads"

New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
New-Item -ItemType Directory -Path $TmpDir -Force | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Fetching Upstream Vulkan Binaries     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. stable-diffusion.cpp
$SdDir = Join-Path $BinDir "stable-diffusion-cpp"
if ($Force -or -not (Test-Path (Join-Path $SdDir "sd.exe"))) {
    Write-Host "[1/4] Fetching stable-diffusion.cpp Vulkan (master-920-2f88688)..." -ForegroundColor Yellow
    $SdZip = Join-Path $TmpDir "sd-win-vulkan.zip"
    gh release download master-920-2f88688 --repo leejet/stable-diffusion.cpp --pattern "sd-*-bin-win-vulkan-x64.zip" --output $SdZip --clobber
    Expand-Archive -Path $SdZip -DestinationPath $SdDir -Force
    Remove-Item $SdZip -Force -ErrorAction SilentlyContinue
    Write-Host "  -> stable-diffusion.cpp installed to $SdDir" -ForegroundColor Green
} else {
    Write-Host "[1/4] stable-diffusion.cpp already installed." -ForegroundColor Green
}

# 2. trellis.cpp
$TrellisDir = Join-Path $BinDir "trellis-cpp"
if ($Force -or -not (Test-Path (Join-Path $TrellisDir "trellis.exe"))) {
    Write-Host "[2/4] Fetching trellis.cpp Vulkan (v0.8.1)..." -ForegroundColor Yellow
    $TrellisZip = Join-Path $TmpDir "trellis-win-vulkan.zip"
    gh release download v0.8.1 --repo pwilkin/trellis.cpp --pattern "trellis-vulkan-windows-x64.zip" --output $TrellisZip --clobber
    Expand-Archive -Path $TrellisZip -DestinationPath $TrellisDir -Force
    Remove-Item $TrellisZip -Force -ErrorAction SilentlyContinue
    Write-Host "  -> trellis.cpp installed to $TrellisDir" -ForegroundColor Green
} else {
    Write-Host "[2/4] trellis.cpp already installed." -ForegroundColor Green
}

# 3. llama.cpp
$LlamaDir = Join-Path $BinDir "llama-cpp"
if ($Force -or -not (Test-Path (Join-Path $LlamaDir "llama-cli.exe"))) {
    Write-Host "[3/4] Fetching llama.cpp Vulkan (b11205)..." -ForegroundColor Yellow
    $LlamaZip = Join-Path $TmpDir "llama-win-vulkan.zip"
    gh release download b11205 --repo ggml-org/llama.cpp --pattern "llama-*-bin-win-vulkan-x64.zip" --output $LlamaZip --clobber
    Expand-Archive -Path $LlamaZip -DestinationPath $LlamaDir -Force
    Remove-Item $LlamaZip -Force -ErrorAction SilentlyContinue
    Write-Host "  -> llama.cpp installed to $LlamaDir" -ForegroundColor Green
} else {
    Write-Host "[3/4] llama.cpp already installed." -ForegroundColor Green
}

# 4. whisper.cpp
$WhisperDir = Join-Path $BinDir "whisper-cpp"
if ($Force -or -not (Test-Path (Join-Path $WhisperDir "whisper-cli.exe"))) {
    Write-Host "[4/4] Fetching whisper.cpp (b5130)..." -ForegroundColor Yellow
    $WhisperZip = Join-Path $TmpDir "whisper-win.zip"
    gh release download b5130 --repo ggml-org/whisper.cpp --pattern "whisper-bin-x64.zip" --output $WhisperZip --clobber
    Expand-Archive -Path $WhisperZip -DestinationPath $WhisperDir -Force
    Remove-Item $WhisperZip -Force -ErrorAction SilentlyContinue
    Write-Host "  -> whisper.cpp installed to $WhisperDir" -ForegroundColor Green
} else {
    Write-Host "[4/4] whisper.cpp already installed." -ForegroundColor Green
}

Write-Host "`nAll upstream binaries are staged in $BinDir." -ForegroundColor Green
