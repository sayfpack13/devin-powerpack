@echo off
setlocal
set MSG=%*
if "%MSG%"=="" set MSG=wip: atomic slice checkpoint

git status >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Not a git repository. Run 'git init' first.
    exit /b 1
)
git status -s | findstr /R "." >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [CHECKPOINT] Clean working tree, nothing to commit.
    exit /b 0
)

git add -A
git commit -m "%MSG%"
echo [CHECKPOINT] Progress committed: "%MSG%"
exit /b 0

