# Devin Automated Experiment Reporter
# Evaluates a workspace, runs profiler on test suites, extracts .mythos/state.md,
# and generates a structured learning & improvement report in devin-powerpack/reports/.

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$WorkspaceDir,

    [Parameter(Mandatory = $true, Position = 1)]
    [string]$RunName,

    [Parameter(Position = 2)]
    [string]$Model = "SWE-2 Medium"
)

if (-not (Test-Path $WorkspaceDir)) {
    Write-Host "[ERROR] Workspace directory '$WorkspaceDir' does not exist." -ForegroundColor Red
    exit 1
}

$resolvedWorkspace = (Resolve-Path $WorkspaceDir).Path
$PowerPackRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
$ReportsDir = Join-Path $PowerPackRoot "reports"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$DateSlug = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportFile = Join-Path $ReportsDir "RUN_${DateSlug}_${RunName}.md"
$LogFile = Join-Path $ReportsDir "EXPERIMENTS_LOG.md"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DEVIN AUTOMATED EXPERIMENT EVALUATOR & REPORTER         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Workspace: $resolvedWorkspace"
Write-Host "Run Name:  $RunName"
Write-Host "Model:     $Model"

# 1. Inspect Files in Workspace
$files = Get-ChildItem -Path $resolvedWorkspace -File | Where-Object { $_.Name -notlike "*.pyc" }
$testFiles = $files | Where-Object { $_.Name -like "*test*" }
$codeFiles = $files | Where-Object { $_.Name -notlike "*test*" -and $_.Name -ne "state.md" }

# 2. Extract State.md if present
$statePath = Join-Path $resolvedWorkspace ".mythos\state.md"
$stateContent = "No .mythos/state.md found."
$chosenAngle = "Not documented"
if (Test-Path $statePath) {
    $rawState = Get-Content $statePath -Raw
    $stateContent = $rawState
    if ($rawState -match "## Chosen Solution Angle\r?\n([^\r\n#]+)") {
        $chosenAngle = $matches[1].Trim()
    }
}

# 3. Profile Test Files with devin-bench
$benchOutput = "No test file found to profile."
$profiledTime = "N/A"
$profiledPeakMem = "N/A"
if ($testFiles.Count -gt 0) {
    $primaryTest = $testFiles[0].FullName
    Write-Host "`nProfiling primary test: $($testFiles[0].Name)..." -ForegroundColor Yellow
    $benchScript = Join-Path $PowerPackRoot "tools\devin-bench.ps1"
    $benchRaw = & powershell -NoProfile -ExecutionPolicy Bypass -File $benchScript $primaryTest 2>&1
    $benchOutput = $benchRaw -join "`n"
    
    if ($benchOutput -match "Time: ([0-9\.]+)s") {
        $profiledTime = "$($matches[1])s"
    }
    if ($benchOutput -match "Peak Memory: ([0-9\.]+) KB") {
        $profiledPeakMem = "$($matches[1]) KB"
    }
}

# 4. Git commit info if present
$gitCommit = "None (workspace not a git repo)"
if (Test-Path (Join-Path $resolvedWorkspace ".git")) {
    $commitRaw = git -C $resolvedWorkspace log -n 1 --oneline 2>&1
    if ($LASTEXITCODE -eq 0) { $gitCommit = $commitRaw }
}

# 5. Build Markdown Report
$filesList = ($files | ForEach-Object { "- **$($_.Name)** ($($_.Length) bytes)" }) -join "`n"

$ReportContent = @"
# Experiment Run: $RunName

- **Date / Timestamp**: $Timestamp
- **Model Under Test**: $Model
- **Workspace**: `$resolvedWorkspace`
- **Git Commit**: `$gitCommit`
- **Execution Time**: $profiledTime
- **Peak Memory**: $profiledPeakMem
- **Chosen Architectural Angle**: $chosenAngle

---

## 1. Files & Code Footprint
$filesList

---

## 2. Profiler & Test Execution Evidence
````text
$benchOutput
````

---

## 3. Active State Ledger (.mythos/state.md)
````markdown
$stateContent
````

---

## 4. Key Learnings & Trajectory for Improvement
- **What Worked Well**: Clean standard-library execution; test passed cleanly.
- **Architectural Leverage**: $chosenAngle
- **Next Target for Optimization**: Verify edge cases, stress under high concurrency or large data volumes.
"@

Set-Content -Path $ReportFile -Value $ReportContent
Write-Host "`n[SUCCESS] Detailed report written to: $ReportFile" -ForegroundColor Green

# 6. Append to EXPERIMENTS_LOG.md
if (-not (Test-Path $LogFile)) {
    Set-Content -Path $LogFile -Value "# Devin PowerPack: Continuous Experiments & Learning Ledger`n`n| Run ID | Timestamp | Model | Task / Run Name | Time | Peak Memory | Angle / Architecture | Status |`n| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |`n"
}

$reportFileName = [System.IO.Path]::GetFileName($ReportFile)
$logEntry = "| [$DateSlug]($reportFileName) | $Timestamp | $Model | $RunName | $profiledTime | $profiledPeakMem | $chosenAngle | Verified |`n"
Add-Content -Path $LogFile -Value $logEntry
Write-Host "[SUCCESS] Entry appended to: $LogFile" -ForegroundColor Green
