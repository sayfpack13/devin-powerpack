@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0devin-run.ps1" %*
exit /b %ERRORLEVEL%
