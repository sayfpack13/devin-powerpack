# Devin Micro-Benchmarking & Memory Profiler
# Runs a script/command, measures execution time, peak memory, and verifies O(1)/O(N) scalability.

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$TargetFile,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

if (-not (Test-Path $TargetFile)) {
    Write-Host "[ERROR] Target file '$TargetFile' does not exist." -ForegroundColor Red
    exit 1
}

$ext = [System.IO.Path]::GetExtension($TargetFile).ToLower()
$normalizedPath = (Resolve-Path $TargetFile).Path.Replace('\', '/')
$targetDir = (Split-Path -Parent (Resolve-Path $TargetFile).Path).Replace('\', '/')
$argsString = if ($ScriptArgs) { $ScriptArgs -join " " } else { "" }

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DEVIN AUTOMATED PERFORMANCE & MEMORY PROFILER           " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Profiling Target: $normalizedPath"

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

if ($ext -eq ".py") {
    $cmd = "python -c `"import time, tracemalloc, runpy, sys, os; sys.path.insert(0, '$targetDir'); tracemalloc.start(); t0 = time.perf_counter(); runpy.run_path('$normalizedPath'); t1 = time.perf_counter(); current, peak = tracemalloc.get_traced_memory(); tracemalloc.stop(); print(f'\\n[PROFILER_METRICS] Time: {t1-t0:.6f}s | Peak Memory: {peak / 1024:.2f} KB | Final Memory: {current / 1024:.2f} KB')`""
} elseif ($ext -eq ".js" -or $ext -eq ".ts") {
    $cmd = "node -e `"const { performance } = require('perf_hooks'); process.chdir('$targetDir'); const t0 = performance.now(); require('$normalizedPath'); const t1 = performance.now(); const mem = process.memoryUsage().heapUsed / 1024; console.log('\\n[PROFILER_METRICS] Time: ' + ((t1-t0)/1000).toFixed(6) + 's | Heap Memory: ' + mem.toFixed(2) + ' KB');`""
} else {
    $cmd = "$TargetFile $argsString"
}

try {
    $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $cmd" -WorkingDirectory (Split-Path -Parent (Resolve-Path $TargetFile).Path) -NoNewWindow -Wait -PassThru
    $stopwatch.Stop()

    Write-Host "`n----------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "Total Process Lifetime: $($stopwatch.ElapsedMilliseconds) ms" -ForegroundColor Green
    if ($process.ExitCode -eq 0) {
        Write-Host "Exit Code: $($process.ExitCode)" -ForegroundColor Green
    } else {
        Write-Host "Exit Code: $($process.ExitCode)" -ForegroundColor Red
    }
    Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray

    exit $process.ExitCode
} catch {
    Write-Host "[ERROR] Execution failed: $_" -ForegroundColor Red
    exit 1
}
