@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0devin-wait.ps1" %*
exit /b %ERRORLEVEL%
