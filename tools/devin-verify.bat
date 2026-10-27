@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0devin-verify.ps1"
pause
