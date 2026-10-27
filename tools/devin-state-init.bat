@echo off
setlocal

if not exist ".mythos" mkdir ".mythos"

if exist ".mythos\state.md" (
    echo [.mythos\state.md already exists. Kept intact.]
    exit /b 0
)

(
echo ## Goal ^& Success Criteria
echo - Goal: [Define the single core deliverable]
echo - Criteria 1: [Compiles / builds cleanly]
echo - Criteria 2: [Target test / behavior verified]
echo.
echo ## Current Slice
echo - Slice 1: [Exact first atomic step touching ^<= 3 files]
echo.
echo ## Modified Files Ledger
echo - [No files modified yet]
echo.
echo ## Completed Slices
echo - [None]
echo.
echo ## Pending Slices
echo - Slice 2: [Next logical vertical slice]
echo.
echo ## Do Not Repeat ^(Failed Approaches^)
echo - [None]
echo.
echo ## Resume Command
echo - git status -s
) > ".mythos\state.md"

echo [SUCCESS] Initialized fresh .mythos\state.md template.
exit /b 0
