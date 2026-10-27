# Devin PowerPack Production-Grade Installer
# Idempotent, safe, updates surviving

$ErrorActionPreference = "Stop"

$PowerPackRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $PowerPackRoot "backups\backup_$Timestamp"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DEVIN SWE 2.0 POWERPACK - PRODUCTION INSTALLER          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Source Directory: $PowerPackRoot"
Write-Host "Backup Directory: $BackupDir"

# 1. Target Directories
$TargetDirs = @(
    "$env:APPDATA\Devin",
    "$env:APPDATA\devin",
    "$env:LOCALAPPDATA\devin",
    "$env:USERPROFILE\.devin",
    "$env:USERPROFILE\.config\devin"
)

# Ensure directories exist
foreach ($dir in $TargetDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# 1b. Register Persistent PowerPack Clone Location on this PC
[Environment]::SetEnvironmentVariable("DEVIN_POWERPACK_ROOT", $PowerPackRoot, "User")
$env:DEVIN_POWERPACK_ROOT = $PowerPackRoot
Set-Content -Path "$env:USERPROFILE\.devin\powerpack_root.txt" -Value $PowerPackRoot -Force
Write-Host "  Registered PowerPack Root: $PowerPackRoot" -ForegroundColor Green


# 2. Perform Backups of Existing Configs
Write-Host "`n[1/5] Backing up existing configurations..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$FilesToBackup = @(
    "$env:APPDATA\Devin\global_rules.md",
    "$env:APPDATA\Devin\AGENTS.md",
    "$env:APPDATA\Devin\mcp_config.json",
    "$env:APPDATA\devin\global_rules.md",
    "$env:APPDATA\devin\AGENTS.md",
    "$env:APPDATA\devin\mcp_config.json",
    "$env:LOCALAPPDATA\devin\global_rules.md",
    "$env:USERPROFILE\.devin\global_rules.md",
    "$env:USERPROFILE\.config\devin\AGENTS.md",
    "$env:USERPROFILE\.config\devin\mcp_config.json"
)

foreach ($filePath in $FilesToBackup) {
    if (Test-Path $filePath) {
        $relPath = $filePath.Replace(":", "").Replace("\", "_")
        Copy-Item -Path $filePath -Destination (Join-Path $BackupDir $relPath) -Force
        Write-Host "  Backed up: $filePath" -ForegroundColor DarkGray
    }
}

# 3. Deploy Master Rules
Write-Host "`n[2/5] Deploying Mythos v2.5 Hardened Rules..." -ForegroundColor Yellow
$MythosSource = Join-Path $PowerPackRoot "rules\mythos_v2.md"
$AgentsSource = Join-Path $PowerPackRoot "rules\AGENTS.md"

$RuleTargets = @(
    "$env:APPDATA\Devin\global_rules.md",
    "$env:APPDATA\devin\global_rules.md",
    "$env:LOCALAPPDATA\devin\global_rules.md",
    "$env:USERPROFILE\.devin\global_rules.md"
)

foreach ($target in $RuleTargets) {
    Copy-Item -Path $MythosSource -Destination $target -Force
    Write-Host "  Installed Mythos v2.5 -> $target" -ForegroundColor Green
}

$AgentsTargets = @(
    "$env:APPDATA\Devin\AGENTS.md",
    "$env:APPDATA\devin\AGENTS.md",
    "$env:USERPROFILE\.config\devin\AGENTS.md"
)

foreach ($target in $AgentsTargets) {
    Copy-Item -Path $AgentsSource -Destination $target -Force
    Write-Host "  Installed AGENTS.md -> $target" -ForegroundColor Green
}

# 4. Deploy Subagent Profiles
Write-Host "`n[3/5] Deploying Custom Subagents (Researcher, Reverse Engineer, Code Reviewer)..." -ForegroundColor Yellow
$AgentsSourceDir = Join-Path $PowerPackRoot "agents"
$AgentTargetDirs = @(
    "$env:APPDATA\Devin\agents",
    "$env:APPDATA\devin\agents",
    "$env:USERPROFILE\.devin\agents",
    "$env:USERPROFILE\.config\devin\agents"
)

foreach ($targetDir in $AgentTargetDirs) {
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    Get-ChildItem -Path $AgentsSourceDir -Filter "*.md" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $targetDir -Force
    }
    Write-Host "  Subagents deployed to -> $targetDir" -ForegroundColor Green
}

# 5. Deploy MCP Configuration
Write-Host "`n[4/6] Deploying MCP Configurations (Context7, Memory, Playwright)..." -ForegroundColor Yellow
$McpSource = Join-Path $PowerPackRoot "mcp\mcp_config.json"
$McpTargets = @(
    "$env:APPDATA\Devin\mcp_config.json",
    "$env:APPDATA\devin\mcp_config.json",
    "$env:USERPROFILE\.config\devin\mcp_config.json",
    "$env:USERPROFILE\.devin\mcp_config.json"
)

foreach ($target in $McpTargets) {
    Copy-Item -Path $McpSource -Destination $target -Force
    Write-Host "  MCP Config deployed -> $target" -ForegroundColor Green
}

# 6. Deploy Cross-Project Knowledge Vault
Write-Host "`n[5/6] Deploying Cross-Project Knowledge Vault..." -ForegroundColor Yellow
$KnowledgeSource = Join-Path $PowerPackRoot "knowledge"
$KnowledgeTargets = @(
    "$env:APPDATA\Devin\knowledge",
    "$env:APPDATA\devin\knowledge",
    "$env:LOCALAPPDATA\devin\knowledge",
    "$env:USERPROFILE\.devin\knowledge"
)

foreach ($targetDir in $KnowledgeTargets) {
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    Get-ChildItem -Path $KnowledgeSource -Filter "*.md" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $targetDir -Force
    }
    Write-Host "  Knowledge Vault mirrored -> $targetDir" -ForegroundColor Green
}

# 7. Configure Tools in PATH and Native Devin Binaries
Write-Host "`n[6/6] Configuring Tools in User PATH & Native Devin Binaries..." -ForegroundColor Yellow
$ToolsDir = Join-Path $PowerPackRoot "tools"
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CurrentPath -notlike "*$ToolsDir*") {
    $NewPath = "$ToolsDir;$CurrentPath"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    $env:Path = "$ToolsDir;$env:Path"
    Write-Host "  Added $ToolsDir to User PATH." -ForegroundColor Green
} else {
    Write-Host "  Tools directory already in PATH." -ForegroundColor DarkGray
}

# Copy directly to Devin Desktop native bin directories for instant discovery without restart
$DevinBinDirs = @(
    "$env:LOCALAPPDATA\Programs\Devin\bin",
    "$env:LOCALAPPDATA\devin\bin"
)
$cliVersions = Get-ChildItem -Path "$env:LOCALAPPDATA\devin\cli\_versions" -Directory -ErrorAction SilentlyContinue
if ($cliVersions) {
    foreach ($ver in $cliVersions) {
        $binDir = Join-Path $ver.FullName "bin"
        if (Test-Path $binDir) { $DevinBinDirs += $binDir }
    }
}

foreach ($bin in $DevinBinDirs) {
    if (Test-Path $bin) {
        Get-ChildItem -Path $ToolsDir -File | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $bin -Force
        }
        Write-Host "  Mirrored CLI tools to native bin -> $bin" -ForegroundColor Green
    }
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  SUCCESS! DEVIN SWE 2.0 POWERPACK SUCCESSFULLY INSTALLED " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Summary of enhancements activated:"
Write-Host " - Mythos v3.0 Active (Evolutionary Performance, Cross-Project Knowledge, Bounded Slices)"
Write-Host " - Cross-Project Knowledge Vault deployed ('CROSS_PROJECT_KNOWLEDGE.md')"
Write-Host " - Fast Knowledge Query Tool active via 'devin-remember <topic>'"
Write-Host " - Custom Subagents installed: 'architect', 'researcher', 'reverse_engineer', 'code_reviewer', 'qa_tester'"
Write-Host " - Production MCP Servers configured: Context7 (live docs), Memory, Playwright"
Write-Host " - Physical context protector enabled via 'devin-run <cmd>'"
Write-Host " - Micro-benchmarker & Memory profiler enabled via 'devin-bench <file>'"
Write-Host " - Compounding Reflexion memory enabled via 'devin-learn <category> <title> <cause> <fix>'"
Write-Host " - 1-command checkpointing enabled via 'devin-checkpoint'"
Write-Host "`nTo revert changes at any time, run uninstall.bat."

