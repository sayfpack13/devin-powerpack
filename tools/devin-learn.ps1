# Devin Reflexion & Compounding Memory Engine
# Records a verified technical lesson, bug trap, or high-performance pattern permanently
# into the cross-project knowledge vault and all active Devin profiles.

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Category,

    [Parameter(Mandatory = $true, Position = 1)]
    [string]$Title,

    [Parameter(Mandatory = $true, Position = 2)]
    [string]$RootCause,

    [Parameter(Mandatory = $true, Position = 3)]
    [string]$ProvenSolution
)

$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$SafeCategory = if ($Category) { ($Category.Trim() -replace '[^a-zA-Z0-9_-]', '_').ToLower() } else { 'general' }
# 1. Resolve PowerPack Root dynamically on any machine
$PowerPackRoot = $null
if ($env:DEVIN_POWERPACK_ROOT -and (Test-Path $env:DEVIN_POWERPACK_ROOT)) {
    $PowerPackRoot = $env:DEVIN_POWERPACK_ROOT
} elseif (Test-Path "$env:USERPROFILE\.devin\powerpack_root.txt") {
    $stored = (Get-Content "$env:USERPROFILE\.devin\powerpack_root.txt" -Raw).Trim()
    if (Test-Path $stored) { $PowerPackRoot = $stored }
}

if (-not $PowerPackRoot) {
    $scriptParent = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
    if (Test-Path (Join-Path $scriptParent "knowledge\CROSS_PROJECT_KNOWLEDGE.md")) {
        $PowerPackRoot = $scriptParent
    }
}

$MasterVault = if ($PowerPackRoot) { Join-Path $PowerPackRoot "knowledge\CROSS_PROJECT_KNOWLEDGE.md" } else { "$env:APPDATA\devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md" }


$LessonMarkdown = @"

### [$Timestamp] $Title
- **Category**: $Category
- **Root Cause / Trap**: $RootCause
- **Proven Solution**: $ProvenSolution

"@

# 1. Append to Central Master Knowledge Base
if (Test-Path $MasterVault) {
    Add-Content -Path $MasterVault -Value "`n$LessonMarkdown"
}

# 2. Append to Category File in knowledge/
$KnowledgeDir = Join-Path $PowerPackRoot "knowledge"
if (-not (Test-Path $KnowledgeDir)) {
    New-Item -ItemType Directory -Path $KnowledgeDir -Force | Out-Null
}
$CategoryFile = Join-Path $KnowledgeDir "$SafeCategory.md"
if (-not (Test-Path $CategoryFile)) {
    Set-Content -Path $CategoryFile -Value "# Cross-Project Lessons: $Category`n"
}
Add-Content -Path $CategoryFile -Value $LessonMarkdown

# 3. Propagate to all Devin global config directories
$SyncDirs = @(
    "$env:APPDATA\Devin\knowledge",
    "$env:APPDATA\devin\knowledge",
    "$env:USERPROFILE\.devin\knowledge",
    "$env:APPDATA\Devin\lessons",
    "$env:APPDATA\devin\lessons",
    ".mythos\lessons"
)

foreach ($dir in $SyncDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $targetFile = Join-Path $dir "$SafeCategory.md"
    if (-not (Test-Path $targetFile)) {
        Set-Content -Path $targetFile -Value "# Lessons: $Category`n"
    }
    Add-Content -Path $targetFile -Value $LessonMarkdown
}

# Mirror Master Vault to APPDATA
Copy-Item -Path $MasterVault -Destination "$env:APPDATA\devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md" -Force -ErrorAction SilentlyContinue
Copy-Item -Path $MasterVault -Destination "$env:APPDATA\Devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md" -Force -ErrorAction SilentlyContinue

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DEVIN KNOWLEDGE ENGINE - LESSON INDEXED CROSS-PROJECT   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Category: $Category"
Write-Host "Title:    $Title"
Write-Host "Vault:    $MasterVault"
Write-Host "Lesson permanently available to all current and future Devin chat sessions."
