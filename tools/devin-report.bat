@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0devin-report.ps1" %*
exit /b %ERRORLEVEL%
