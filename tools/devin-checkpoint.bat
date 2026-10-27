@echo off
setlocal
set MSG=%*
if "%MSG%"=="" set MSG=wip: atomic slice checkpoint

git status >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Not a git repository. Run 'git init' first.
    exit /b 1
)

git add -A
git commit -m "%MSG%"
echo [CHECKPOINT] Progress committed: "%MSG%"
exit /b 0
