Write-Host '==========================================================' -ForegroundColor Cyan
Write-Host '  DEVIN SWE 2.0 POWERPACK - LIVE HEALTH DIAGNOSTIC        ' -ForegroundColor Cyan
Write-Host '==========================================================' -ForegroundColor Cyan

Write-Host "`n[1/5] Checking Devin Running Processes..." -ForegroundColor Yellow
$proc = Get-Process -Name 'Devin', 'devin_custom' -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "  Devin Desktop / CLI is actively running (PIDs: $($proc.Id -join ', '))" -ForegroundColor Green
} else {
    Write-Host "  Devin Desktop is not currently running." -ForegroundColor DarkGray
}

# 0. Resolve PowerPack Root across any PC
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

# Find devin_custom.exe dynamically
$devinBin = Get-ChildItem -Path "$env:LOCALAPPDATA\devin\cli\_versions" -Filter "devin_custom.exe" -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
$devinExe = if ($devinBin) { $devinBin.FullName } else { "devin" }

Write-Host "`n[2/5] Checking Custom Subagents in Devin Core..." -ForegroundColor Yellow
$doctorOutput = & $devinExe doctor 2>&1
$doctorOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }

Write-Host "`n[3/5] Checking Active Rules in Devin..." -ForegroundColor Yellow
$rulesOutput = & $devinExe rules list 2>&1
$rulesOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }

Write-Host "`n[4/5] Checking MCP Servers in Devin..." -ForegroundColor Yellow
$mcpOutput = & $devinExe mcp list 2>&1
$mcpOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }

Write-Host "`n[5/5] Checking Configuration File Sync Status..." -ForegroundColor Yellow
$masterRulesFile = Join-Path $PowerPackRoot "rules\mythos_v2.md"
$masterHash = if (Test-Path $masterRulesFile) { (Get-FileHash $masterRulesFile).Hash } else { "" }
$targetFiles = @(
    "$env:APPDATA\Devin\global_rules.md",
    "$env:APPDATA\devin\global_rules.md",
    "$env:LOCALAPPDATA\devin\global_rules.md",
    "$env:USERPROFILE\.devin\global_rules.md"
)
$allSynced = $true
foreach ($f in $targetFiles) {
    if (Test-Path $f) {
        $h = (Get-FileHash $f).Hash
        $match = ($h -eq $masterHash)
        if ($match) {
            Write-Host "  [OK] $f" -ForegroundColor Green
        } else {
            Write-Host "  [OUT OF SYNC] $f" -ForegroundColor Red
            $allSynced = $false
        }
    } else {
        Write-Host "  [MISSING] $f" -ForegroundColor Red
        $allSynced = $false
    }
}

Write-Host "`n[6/6] Checking Cross-Project Knowledge Vault Sync..." -ForegroundColor Yellow
$masterVaultFile = Join-Path $PowerPackRoot "knowledge\CROSS_PROJECT_KNOWLEDGE.md"
$masterVaultHash = if (Test-Path $masterVaultFile) { (Get-FileHash $masterVaultFile).Hash } else { "" }
$vaultTargets = @(
    "$env:APPDATA\Devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md",
    "$env:APPDATA\devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md",
    "$env:LOCALAPPDATA\devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md",
    "$env:USERPROFILE\.devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md"
)
foreach ($vf in $vaultTargets) {
    if (Test-Path $vf) {
        $vh = (Get-FileHash $vf).Hash

        if ($vh -eq $masterVaultHash) {
            Write-Host "  [OK] $vf" -ForegroundColor Green
        } else {
            Write-Host "  [OUT OF SYNC] $vf" -ForegroundColor Red
            $allSynced = $false
        }
    } else {
        Write-Host "  [MISSING] $vf" -ForegroundColor Red
        $allSynced = $false
    }
}

if ($allSynced) {
    Write-Host "`nALL SYSTEMS OPERATIONAL: Devin Desktop & Knowledge Vault are 100% synced." -ForegroundColor Cyan
} else {
    Write-Host "`nSome files are out of sync. Run install.bat to re-sync." -ForegroundColor Yellow
}

