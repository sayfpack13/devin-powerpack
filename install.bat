@echo off
setlocal
cd /d "%~dp0"
echo Starting Devin SWE 2.0 PowerPack Installation...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Installation encountered an error.
    pause
    exit /b %ERRORLEVEL%
)
echo.
echo [DONE] Devin PowerPack is installed. Press any key to finish.
pause
exit /b 0
