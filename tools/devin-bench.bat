@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0devin-bench.ps1" %*
exit /b %ERRORLEVEL%
