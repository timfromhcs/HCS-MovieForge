@echo off
REM HCS MovieForge - Windows Stop Script
setlocal EnableDelayedExpansion

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [MovieForge] Stopping HCS MovieForge services...
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%stop.ps1" %*
exit /b %ERRORLEVEL%
