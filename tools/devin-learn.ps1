# Devin Reflexion & Compounding Memory Engine
# Records a verified technical lesson, bug trap, or high-performance pattern across sessions.

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
$SafeCategory = $Category.ToLower().Replace(" ", "_")

$LessonContent = @"

### [$Timestamp] $Title
- **Category**: $Category
- **Root Cause / Trap**: $RootCause
- **Proven Solution**: $ProvenSolution

"@

$LessonDirs = @(
    "$env:APPDATA\Devin\lessons",
    "$env:APPDATA\devin\lessons",
    "$env:USERPROFILE\.devin\lessons",
    ".mythos\lessons"
)

foreach ($dir in $LessonDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $targetFile = Join-Path $dir "$SafeCategory.md"
    if (-not (Test-Path $targetFile)) {
        Set-Content -Path $targetFile -Value "# Lessons & Proven Patterns: $Category`n"
    }
    Add-Content -Path $targetFile -Value $LessonContent
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DEVIN REFLEXION ENGINE - LESSON INDEXED PERMANENTLY     " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Category: $Category"
Write-Host "Title:    $Title"
Write-Host "Saved to global lessons vault for compounding intelligence across sessions."
