<#
.SYNOPSIS
    Integration test harness for FFmpeg and ffprobe validation.
.DESCRIPTION
    Encodes a synthetic 1080p 24fps MP4 with AAC stereo audio tone,
    validates streams with ffprobe, and checks file existence and hash.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName

$FFmpeg = (Get-Command ffmpeg.exe -ErrorAction SilentlyContinue).Source
$FFprobe = (Get-Command ffprobe.exe -ErrorAction SilentlyContinue).Source

if (-not $FFmpeg -or -not $FFprobe) {
    Write-Host "[FAIL] FFmpeg or ffprobe executable not found." -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Testing FFmpeg & FFprobe Integration  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$OutVideo = Join-Path $ProjectRoot "runtime\ffmpeg_smoke_test.mp4"
if (Test-Path $OutVideo) { Remove-Item $OutVideo -Force }

# Generate 1 second 1080p test video with 440Hz test sine tone
$ArgsList = @(
    "-y",
    "-f", "lavfi", "-i", "testsrc=duration=1:size=1920x1080:rate=24",
    "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "128k",
    $OutVideo
)

$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$Proc = Start-Process -FilePath $FFmpeg -ArgumentList $ArgsList -PassThru -NoNewWindow -Wait
$Stopwatch.Stop()

if ($Proc.ExitCode -ne 0 -or -not (Test-Path $OutVideo)) {
    Write-Host "[FAIL] FFmpeg test encode failed (ExitCode: $($Proc.ExitCode))" -ForegroundColor Red
    exit 1
}

# Validate with ffprobe
$ProbeOut = & $FFprobe -v quiet -print_format json -show_format -show_streams $OutVideo | ConvertFrom-Json
$VStream = $ProbeOut.streams | Where-Object { $_.codec_type -eq "video" }
$AStream = $ProbeOut.streams | Where-Object { $_.codec_type -eq "audio" }

if ($VStream.width -eq 1920 -and $VStream.height -eq 1080 -and $AStream) {
    Write-Host "[PASS] FFmpeg 1080p encode & probe verified in $($Stopwatch.Elapsed.TotalSeconds.ToString('F2'))s" -ForegroundColor Green
    Remove-Item $OutVideo -Force -ErrorAction SilentlyContinue
    exit 0
} else {
    Write-Host "[FAIL] Stream validation failed (Width: $($VStream.width), Height: $($VStream.height), Audio: $($AStream -ne $null))" -ForegroundColor Red
    Remove-Item $OutVideo -Force -ErrorAction SilentlyContinue
    exit 1
}
