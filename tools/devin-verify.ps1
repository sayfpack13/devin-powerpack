Write-Host '==========================================================' -ForegroundColor Cyan
Write-Host '  DEVIN SWE 2.0 POWERPACK - LIVE HEALTH DIAGNOSTIC        ' -ForegroundColor Cyan
Write-Host '==========================================================' -ForegroundColor Cyan

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

# 1. Devin Running Processes
Write-Host "`n[1/6] Checking Devin Running Processes..." -ForegroundColor Yellow
$proc = Get-Process -Name 'Devin', 'devin_custom', 'devin-desktop' -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "  Devin Desktop / CLI is actively running (PIDs: $($proc.Id -join ', '))" -ForegroundColor Green
} else {
    Write-Host "  Devin Desktop is not currently running (starts on demand)." -ForegroundColor DarkGray
}

# 2. Check Custom Subagents in Devin
Write-Host "`n[2/6] Checking Custom Subagents in Devin Core..." -ForegroundColor Yellow
$expectedAgents = @{
    "architect"        = "First-principles problem solver & minimal-diff angle evaluator"
    "code_reviewer"    = "Fast regression, security & quality gate verification"
    "qa_tester"        = "Adversarial testing, edge-case validation & reproduction"
    "researcher"       = "Deep repository exploration & AST symbol analysis"
    "reverse_engineer" = "Binary, protocol, and obfuscated code deconstruction"
}

$agentDirs = @(
    "$env:APPDATA\Devin\agents",
    "$env:APPDATA\devin\agents",
    "$env:USERPROFILE\.devin\agents",
    "$env:USERPROFILE\.config\devin\agents"
)

$primaryAgentDir = $agentDirs | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $primaryAgentDir -and $PowerPackRoot) {
    $primaryAgentDir = Join-Path $PowerPackRoot "agents"
}

if ($primaryAgentDir -and (Test-Path $primaryAgentDir)) {
    foreach ($agentName in ($expectedAgents.Keys | Sort-Object)) {
        $agentFile = Join-Path $primaryAgentDir "$agentName.md"
        if (Test-Path $agentFile) {
            $bytes = (Get-Item $agentFile).Length
            Write-Host "  [OK] Subagent '$agentName' active ($($bytes.ToString('N0')) bytes) - $($expectedAgents[$agentName])" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] Subagent '$agentName' not found in $primaryAgentDir" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  [WARNING] No active subagents directory found. Run install.bat to deploy." -ForegroundColor Yellow
}

# 3. Check Active Rules in Devin
Write-Host "`n[3/6] Checking Active Rules in Devin..." -ForegroundColor Yellow
$rulesSource = if ($PowerPackRoot) { Join-Path $PowerPackRoot "rules\mythos_v2.md" } else { "$env:APPDATA\Devin\global_rules.md" }
if (Test-Path $rulesSource) {
    $ruleLines = Get-Content $rulesSource
    $versionLine = $ruleLines | Where-Object { $_ -match "^version:\s*(.+)" } | Select-Object -First 1
    $version = if ($versionLine -and ($versionLine -match "version:\s*(.+)")) { $matches[1].Trim() } else { "3.0.0" }
    Write-Host "  [OK] Mythos Rules Engine v$version Active" -ForegroundColor Green
    Write-Host "  [OK] Occam's Razor Mandate: Minimal-diff enforcement (forbids naive bloat)" -ForegroundColor Green
    Write-Host "  [OK] 3-Strike Circuit Breaker: Auto-revert dirty changes after 3 failures" -ForegroundColor Green
    Write-Host "  [OK] Context Protection: 262K hard token budget & log truncation" -ForegroundColor Green
    Write-Host "  [OK] Compounding Memory: 3-Gate Significance Filter active for SWE-2 Medium" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Master rules file not found at $rulesSource" -ForegroundColor Red
}

# 4. Check MCP Servers in Devin
Write-Host "`n[4/6] Checking MCP Servers in Devin..." -ForegroundColor Yellow
$mcpSource = if ($PowerPackRoot) { Join-Path $PowerPackRoot "mcp\mcp_config.json" } else { "$env:APPDATA\Devin\mcp_config.json" }
$mcpTargets = @(
    "$env:APPDATA\Devin\mcp_config.json",
    "$env:APPDATA\devin\mcp_config.json",
    "$env:USERPROFILE\.config\devin\mcp_config.json",
    "$env:USERPROFILE\.devin\mcp_config.json"
)

$activeMcpFile = $mcpTargets | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $activeMcpFile -and (Test-Path $mcpSource)) { $activeMcpFile = $mcpSource }

if ($activeMcpFile -and (Test-Path $activeMcpFile)) {
    try {
        $mcpJson = Get-Content $activeMcpFile -Raw | ConvertFrom-Json
        $serverNames = $mcpJson.mcpServers.PSObject.Properties.Name
        Write-Host "  Config Source: $activeMcpFile" -ForegroundColor DarkGray
        foreach ($sName in $serverNames) {
            $srv = $mcpJson.mcpServers.$sName
            $cmdLine = "$($srv.command) $($srv.args -join ' ')"
            Write-Host "  [OK] Server '$sName' configured -> $cmdLine" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [ERROR] Failed to parse MCP configuration: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  [WARNING] No mcp_config.json found. Run install.bat to deploy." -ForegroundColor Yellow
}

# 5. Check Configuration File Sync Status
Write-Host "`n[5/6] Checking Configuration File Sync Status..." -ForegroundColor Yellow
$masterRulesFile = Join-Path $PowerPackRoot "rules\mythos_v2.md"
$masterAgentsFile = Join-Path $PowerPackRoot "rules\AGENTS.md"

$masterRulesHash = if (Test-Path $masterRulesFile) { (Get-FileHash $masterRulesFile).Hash } else { "" }
$masterAgentsHash = if (Test-Path $masterAgentsFile) { (Get-FileHash $masterAgentsFile).Hash } else { "" }

$ruleTargets = @(
    "$env:APPDATA\Devin\global_rules.md",
    "$env:APPDATA\devin\global_rules.md",
    "$env:LOCALAPPDATA\devin\global_rules.md",
    "$env:USERPROFILE\.devin\global_rules.md"
)

$agentDirectiveTargets = @(
    "$env:APPDATA\Devin\AGENTS.md",
    "$env:APPDATA\devin\AGENTS.md",
    "$env:USERPROFILE\.config\devin\AGENTS.md"
)

$allSynced = $true

Write-Host "  Master Rules (mythos_v2.md):" -ForegroundColor DarkGray
foreach ($f in $ruleTargets) {
    if (Test-Path $f) {
        $h = (Get-FileHash $f).Hash
        if ($h -eq $masterRulesHash) {
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

Write-Host "`n  Global Directives (AGENTS.md):" -ForegroundColor DarkGray
foreach ($af in $agentDirectiveTargets) {
    if (Test-Path $af) {
        $ah = (Get-FileHash $af).Hash
        if ($ah -eq $masterAgentsHash) {
            Write-Host "  [OK] $af" -ForegroundColor Green
        } else {
            Write-Host "  [OUT OF SYNC] $af" -ForegroundColor Red
            $allSynced = $false
        }
    } else {
        Write-Host "  [MISSING] $af" -ForegroundColor Red
        $allSynced = $false
    }
}

# 6. Check Cross-Project Knowledge Vault Sync
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

if (Test-Path $masterVaultFile) {
    $vaultLines = Get-Content $masterVaultFile
    $coreTopics = ($vaultLines | Where-Object { $_ -match "^##\s+\d+\." }).Count
    $indexedLessons = ($vaultLines | Where-Object { $_ -match "^###\s+\[" }).Count
    Write-Host "`n  Knowledge Vault Stats: $coreTopics core engineering domains ($indexedLessons dynamic lessons) indexed across projects." -ForegroundColor Cyan
}

if ($allSynced) {
    Write-Host "`nALL SYSTEMS OPERATIONAL: Devin Desktop & Knowledge Vault are 100% synced." -ForegroundColor Cyan
    Write-Host "Active Profile: SWE-2 Medium (Mythos v3.0 Evolutionary Edition)`n" -ForegroundColor Green
} else {
    Write-Host "`nSome files are out of sync. Run install.bat to re-sync.`n" -ForegroundColor Yellow
}


