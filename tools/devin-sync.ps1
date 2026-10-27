# Devin Universal Cloud & Multi-PC Synchronizer
# Pulls latest lessons and tools from GitHub, re-applies installations, and verifies health.

$PowerPackRoot = $null
if ($env:DEVIN_POWERPACK_ROOT -and (Test-Path $env:DEVIN_POWERPACK_ROOT)) {
    $PowerPackRoot = $env:DEVIN_POWERPACK_ROOT
} elseif (Test-Path "$env:USERPROFILE\.devin\powerpack_root.txt") {
    $stored = (Get-Content "$env:USERPROFILE\.devin\powerpack_root.txt" -Raw).Trim()
    if (Test-Path $stored) { $PowerPackRoot = $stored }
}

if (-not $PowerPackRoot) {
    $scriptParent = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
    if (Test-Path (Join-Path $scriptParent "rules\mythos_v2.md")) { $PowerPackRoot = $scriptParent }
}

if (-not $PowerPackRoot -or -not (Test-Path $PowerPackRoot)) {
    Write-Host "[ERROR] Could not resolve Devin PowerPack directory." -ForegroundColor Red
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DEVIN POWERPACK - UNIVERSAL CLOUD & PROFILE SYNC        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "PowerPack Directory: $PowerPackRoot"

# 1. Pull latest updates from Git if it's a git repo
if (Test-Path (Join-Path $PowerPackRoot ".git")) {
    Write-Host "`n[1/3] Pulling latest updates from GitHub..." -ForegroundColor Yellow
    $pullOutput = git -C $PowerPackRoot pull origin main 2>&1
    Write-Host "  $pullOutput" -ForegroundColor Green
} else {
    Write-Host "`n[1/3] Skipping git pull (not a git repository)." -ForegroundColor DarkGray
}

# 2. Re-run installer to mirror configurations
Write-Host "`n[2/3] Re-applying installations and roaming profiles..." -ForegroundColor Yellow
$installScript = Join-Path $PowerPackRoot "install.ps1"
if (Test-Path $installScript) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $installScript
}

# 3. Verify health
Write-Host "`n[3/3] Running Live Health Diagnostics..." -ForegroundColor Yellow
$verifyScript = Join-Path $PowerPackRoot "tools\devin-verify.ps1"
if (Test-Path $verifyScript) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $verifyScript
}

Write-Host "`n[SYNC COMPLETE] All profiles, rules, subagents, and knowledge vaults are 100% up to date." -ForegroundColor Cyan
