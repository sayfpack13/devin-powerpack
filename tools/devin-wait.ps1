# Devin Dynamic Wait & Polling Tool
# Replaces slow, blind "sleep X" commands with fast, early-exit condition polling.
# Exits immediately the millisecond the condition is met!

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
    [double]$Timeout = 15.0,
    [int]$IntervalMs = 250
)

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$timeoutMs = [int]($Timeout * 1000)

# 1. Simple numeric sleep fallback if invoked as "devin-wait 2"
if ($Target -match '^\d+(\.\d+)?$' -and -not $Proc -and -not $Port -and -not $File -and -not $Cmd) {
    Start-Sleep -Seconds ([double]$Target)
    exit 0
}

# If target is provided as a shorthand
if ($Target -and -not $Proc -and -not $Port -and -not $File -and -not $Cmd) {
    if ($Target -match '^\d+$') {
        $Port = [int]$Target
    } elseif ($Target -match '\.(exe|dll)$') {
        $Proc = $Target
    } elseif (Test-Path $Target -PathType Leaf) {
        $File = $Target
    } else {
        $Cmd = $Target
    }
}

function Test-Condition {
    # Check 1: Process presence or exit
    if ($Proc) {
        $procName = [System.IO.Path]::GetFileNameWithoutExtension($Proc)
        $running = @(Get-Process -Name $procName -ErrorAction SilentlyContinue).Count -gt 0
        if ($Exit) {
            return (-not $running)
        } else {
            return $running
        }
    }

    # Check 2: TCP Port open
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

    # Check 3: File existence or log pattern
    if ($File) {
        if (-not (Test-Path $File)) {
            return $false
        }
        if ($Contains) {
            $content = Get-Content -Path $File -Tail 100 -ErrorAction SilentlyContinue
            if ($content -match [regex]::Escape($Contains)) {
                return $true
            }
            return $false
        }
        return $true
    }

    # Check 4: Arbitrary check command
    if ($Cmd) {
        try {
            $res = Invoke-Expression $Cmd
            if ($LASTEXITCODE -eq 0 -or $res) {
                return $true
            }
        } catch {}
        return $false
    }

    return $true
}

# Polling Loop with Fast Early Exit
while ($sw.ElapsedMilliseconds -lt $timeoutMs) {
    if (Test-Condition) {
        $elapsedSec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        Write-Host "[devin-wait] Condition met early in ${elapsedSec}s!" -ForegroundColor Green
        exit 0
    }
    Start-Sleep -Milliseconds $IntervalMs
}

$elapsedSec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
Write-Host "[devin-wait] Timeout after ${elapsedSec}s (condition not met)." -ForegroundColor Yellow
exit 1
