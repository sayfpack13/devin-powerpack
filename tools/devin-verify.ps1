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

Write-Host "`n[2/5] Checking Custom Subagents in Devin Core..." -ForegroundColor Yellow
$doctorOutput = & 'C:\Users\sayfp\AppData\Local\devin\cli\_versions\3000.11.1-partner.1\bin\devin_custom.exe' doctor 2>&1
$doctorOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }

Write-Host "`n[3/5] Checking Active Rules in Devin..." -ForegroundColor Yellow
$rulesOutput = & 'C:\Users\sayfp\AppData\Local\devin\cli\_versions\3000.11.1-partner.1\bin\devin_custom.exe' rules list 2>&1
$rulesOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }

Write-Host "`n[4/5] Checking MCP Servers in Devin..." -ForegroundColor Yellow
$mcpOutput = & 'C:\Users\sayfp\AppData\Local\devin\cli\_versions\3000.11.1-partner.1\bin\devin_custom.exe' mcp list 2>&1
$mcpOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }

Write-Host "`n[5/5] Checking Configuration File Sync Status..." -ForegroundColor Yellow
$masterHash = (Get-FileHash 'C:\Users\sayfp\devin-powerpack\rules\mythos_v2.md').Hash
$targetFiles = @(
    'C:\Users\sayfp\AppData\Roaming\Devin\global_rules.md',
    'C:\Users\sayfp\AppData\Roaming\devin\global_rules.md',
    'C:\Users\sayfp\AppData\Local\devin\global_rules.md',
    'C:\Users\sayfp\.devin\global_rules.md'
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
$masterVaultHash = (Get-FileHash 'C:\Users\sayfp\devin-powerpack\knowledge\CROSS_PROJECT_KNOWLEDGE.md').Hash
$vaultTargets = @(
    'C:\Users\sayfp\AppData\Roaming\Devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md',
    'C:\Users\sayfp\AppData\Roaming\devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md',
    'C:\Users\sayfp\AppData\Local\devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md',
    'C:\Users\sayfp\.devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md'
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

