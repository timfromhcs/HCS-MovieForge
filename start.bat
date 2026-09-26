@echo off
REM HCS MovieForge - Windows Start Script
setlocal EnableDelayedExpansion

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [MovieForge] Launching HCS MovieForge...
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start.ps1" %*
exit /b %ERRORLEVEL%
