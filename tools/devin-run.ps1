# Devin Output Truncator & Context Protector
# Runs any command, logs full output to .mythos/last_output.log,
# and prints only the top 35 and bottom 45 lines if output exceeds 80 lines.

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs
)

if (-not $CommandArgs -or $CommandArgs.Length -eq 0) {
    Write-Host "Usage: devin-run <command> [args...]" -ForegroundColor Yellow
    exit 1
}

$cmdString = $CommandArgs -join " "

# Ensure .mythos folder exists
if (-not (Test-Path ".mythos")) {
    New-Item -ItemType Directory -Path ".mythos" -Force | Out-Null
}

$logPath = ".mythos/last_output.log"
$tempFile = [System.IO.Path]::GetTempFileName()

try {
    # Run command and capture both stdout and stderr
    $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $cmdString" -NoNewWindow -Wait -PassThru -RedirectStandardOutput $tempFile -RedirectStandardError "$tempFile.err"
    
    # Merge stderr into tempFile if exists
    if (Test-Path "$tempFile.err") {
        Get-Content "$tempFile.err" | Add-Content $tempFile
        Remove-Item "$tempFile.err" -Force -ErrorAction SilentlyContinue
    }

    # Save complete log
    Copy-Item $tempFile $logPath -Force

    $lines = Get-Content $tempFile
    $lineCount = $lines.Count

    if ($lineCount -le 80) {
        $lines | ForEach-Object { Write-Output $_ }
    } else {
        $topLines = $lines[0..34]
        $bottomLines = $lines[($lineCount - 45)..($lineCount - 1)]

        $topLines | ForEach-Object { Write-Output $_ }
        Write-Host ""
        Write-Host "[DEVIN-RUN: Truncated $($lineCount - 80) lines. Complete output saved to $logPath]" -ForegroundColor DarkYellow
        Write-Host ""
        $bottomLines | ForEach-Object { Write-Output $_ }
    }

    exit $process.ExitCode
} finally {
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
    }
}
