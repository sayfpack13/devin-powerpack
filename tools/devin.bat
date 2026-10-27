@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0devin.ps1" %*
exit /b %ERRORLEVEL%
