# Devin Dynamic Wait & Live Streaming Poller
# Replaces slow, blind "sleep X" commands with fast, early-exit condition polling and real-time streaming heartbeats.

param(
    [Parameter(Position = 0)]
    [string]$Target,

    [string]$Proc,
    [switch]$Exit,
    [int]$Port,
    [string]$HostName = "127.0.0.1",
    [string]$File,
    [string]$Contains,
    [string]$Cmd,
    [string]$Tail,
    [double]$Timeout = 15.0,
    [int]$IntervalMs = 250
)

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$timeoutMs = [int]($Timeout * 1000)

# Numeric seconds wait fallback with live heartbeat
if ($Target -match '^\d+(\.\d+)?$' -and -not $Proc -and -not $Port -and -not $File -and -not $Cmd) {
    $sec = [int]$Target
    if ($sec -lt 60 -and -not (Test-Path $Target)) {
        for ($s = 1; $s -le $sec; $s++) {
            Start-Sleep -Seconds 1
            Write-Host "[devin-wait] Elapsed ${s}s / ${sec}s" -ForegroundColor Cyan
        }
        exit 0
    }
}

# Shorthand resolution
if ($Target -and -not $Proc -and -not $Port -and -not $File -and -not $Cmd) {
    if ($Target -match '^\d+$') {
        $Port = [int]$Target
    } elseif ($Target -match '\.(exe|dll|bin)$') {
        $Proc = $Target
    } elseif (Test-Path $Target) {
        $File = $Target
    } else {
        $File = $Target
    }
}

# Auto-detect nearby log file if --tail not specified
if (-not $Tail) {
    $candidates = @("sniff.out", "capture.out", "app.log", "output.log", "server.log")
    foreach ($cand in $candidates) {
        if (Test-Path $cand) {
            $Tail = $cand
            break
        }
    }
}

$desc = "condition"
if ($File) { $desc = "file '$File'" }
elseif ($Proc) { $desc = "process '$Proc'" }
elseif ($Port -gt 0) { $desc = "port '$Port'" }

Write-Host "[devin-wait] Watching for $desc (timeout: ${Timeout}s, polling every 250ms)..." -ForegroundColor Cyan

function Test-Condition {
    if ($Proc) {
        $procName = [System.IO.Path]::GetFileNameWithoutExtension($Proc)
        $running = @(Get-Process -Name $procName -ErrorAction SilentlyContinue).Count -gt 0
        if ($Exit) { return (-not $running) }
        else { return $running }
    }

    if ($Port -gt 0) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $async = $tcp.BeginConnect($HostName, $Port, $null, $null)
            $wait = $async.AsyncWaitHandle.WaitOne(200, $false)
            if ($wait -and $tcp.Connected) {
                $tcp.EndConnect($async)
                $tcp.Close()
                return $true
            }
            $tcp.Close()
        } catch {}
        return $false
    }

    if ($File) {
        if (-not (Test-Path $File)) { return $false }
        if ($Contains) {
            $content = Get-Content -Path $File -Tail 100 -ErrorAction SilentlyContinue
            if ($content -match [regex]::Escape($Contains)) { return $true }
            return $false
        }
        return $true
    }

    if ($Cmd) {
        try {
            $res = Invoke-Expression $Cmd
            if ($LASTEXITCODE -eq 0 -or $res) { return $true }
        } catch {}
        return $false
    }

    return $true
}

$lastHeartbeat = 0
$lastTailLine = ""

while ($sw.ElapsedMilliseconds -lt $timeoutMs) {
    if (Test-Condition) {
        $elapsedSec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        Write-Host "`n[devin-wait] SUCCESS: Condition met in ${elapsedSec}s!" -ForegroundColor Green
        if ($File -and (Test-Path $File)) {
            Write-Host "[devin-wait] Preview of $File (first 300 bytes):" -ForegroundColor DarkGray
            Get-Content -Path $File -TotalCount 5 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
        }
        exit 0
    }

    $elapsed = [int]($sw.ElapsedMilliseconds / 1000)
    if ($elapsed -ge ($lastHeartbeat + 2)) {
        $lastHeartbeat = $elapsed
        if ($Tail -and (Test-Path $Tail)) {
            $latest = Get-Content -Path $Tail -Tail 1 -ErrorAction SilentlyContinue
            if ($latest -and $latest -ne $lastTailLine) {
                $lastTailLine = $latest
                Write-Host "[devin-wait: ${elapsed}s] $Tail >> $latest" -ForegroundColor DarkCyan
            } else {
                Write-Host "[devin-wait: ${elapsed}s] still watching for $desc..." -ForegroundColor DarkGray
            }
        } else {
            Write-Host "[devin-wait: ${elapsed}s] still watching for $desc..." -ForegroundColor DarkGray
        }
    }

    Start-Sleep -Milliseconds $IntervalMs
}

$elapsedSec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
Write-Host "`n[devin-wait] TIMEOUT reached after ${elapsedSec}s. Condition not met." -ForegroundColor Yellow
if ($Tail -and (Test-Path $Tail)) {
    Write-Host "[devin-wait] Latest log from $Tail:" -ForegroundColor DarkYellow
    Get-Content -Path $Tail -Tail 5 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
}
exit 1
