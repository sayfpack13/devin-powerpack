# Devin Cross-Project Knowledge Query Engine
# Instantly queries and prints battle-tested patterns and traps from the global knowledge vault.

param(
    [Parameter(Position = 0)]
    [string]$Topic = ""
)

$PowerPackRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
$MasterKnowledgeFile = Join-Path $PowerPackRoot "knowledge\CROSS_PROJECT_KNOWLEDGE.md"

if (-not (Test-Path $MasterKnowledgeFile)) {
    # Fallback to APPDATA location
    $MasterKnowledgeFile = "$env:APPDATA\devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md"
}

if (-not (Test-Path $MasterKnowledgeFile)) {
    Write-Host "[ERROR] Master knowledge vault not found." -ForegroundColor Red
    exit 1
}

$content = Get-Content -Path $MasterKnowledgeFile -Raw

if ([string]::IsNullOrWhiteSpace($Topic)) {
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "  DEVIN CROSS-PROJECT KNOWLEDGE VAULT INDEX               " -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "Usage: devin-remember <topic_or_keyword>`n"
    Write-Host "Available Core Topics:" -ForegroundColor Yellow
    Write-Host "  - transactions  : Layered delta stack, O(1) rollback, zero deepcopy"
    Write-Host "  - protocols     : Sentinel trailers (0xAA55), 3-strike circuit breaker"
    Write-Host "  - concurrency   : collections.deque left-purge, bounded sliding windows"
    Write-Host "  - caching       : OrderedDict, O(1) LRU eviction, monotonic time"
    Write-Host "  - subagents     : Researcher vs QA vs Single-agent velocity guidelines"
    Write-Host "  - windows       : PowerShell escaping, Electron terminal path resolution"
    Write-Host "`nTo view full topic, run: devin-remember <topic>"
    exit 0
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  SEARCHING GLOBAL KNOWLEDGE VAULT: '$Topic'             " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Find sections matching the topic keyword
$lines = Get-Content -Path $MasterKnowledgeFile
$matching = $false
$foundCount = 0
$buffer = @()

foreach ($line in $lines) {
    if ($line -match "^##\s+[0-9]+\.\s+.*") {
        if ($matching) {
            # End of previous match
            $buffer | ForEach-Object { Write-Host $_ }
            Write-Host "`n----------------------------------------------------------`n" -ForegroundColor DarkGray
            $buffer = @()
            $matching = $false
        }
        if ($line -match "(?i)$Topic") {
            $matching = $true
            $foundCount++
        }
    }

    if ($matching) {
        $buffer += $line
    }
}

if ($matching -and $buffer.Count -gt 0) {
    $buffer | ForEach-Object { Write-Host $_ }
}

if ($foundCount -eq 0) {
    Write-Host "`nNo specific section found for '$Topic'. Searching body text for matches...`n" -ForegroundColor Yellow
    $matches = Select-String -Path $MasterKnowledgeFile -Pattern $Topic -Context 2, 4
    if ($matches) {
        foreach ($m in $matches) {
            Write-Host "Found in Line $($m.LineNumber):" -ForegroundColor Green
            $m.Context.PreContext | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
            Write-Host " > $($m.Line)" -ForegroundColor Yellow
            $m.Context.PostContext | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            Write-Host ""
        }
    } else {
        Write-Host "No matches found. Run 'devin-remember' without arguments to see available topics." -ForegroundColor Red
    }
}
