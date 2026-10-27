@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0devin-learn.ps1" %*
exit /b %ERRORLEVEL%
