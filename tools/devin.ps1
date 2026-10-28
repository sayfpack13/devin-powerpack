# Devin Unified Command-Line Interface (PowerPack & Desktop Integration)
# Provides instant CLI dispatch for diagnostics, rules, MCP, memory, bench, and desktop agent.

param(
    [Parameter(Position = 0)]
    [string]$Command = "help",

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

switch ($Command.ToLower()) {
    { $_ -in @("doctor", "verify", "health", "diag") } {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ToolsDir "devin-verify.ps1") @RemainingArgs
        break
    }
    { $_ -in @("remember", "query", "knowledge") } {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ToolsDir "devin-remember.ps1") @RemainingArgs
        break
    }
    { $_ -in @("bench", "profile") } {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ToolsDir "devin-bench.ps1") @RemainingArgs
        break
    }
    { $_ -in @("learn", "record") } {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ToolsDir "devin-learn.ps1") @RemainingArgs
        break
    }
    { $_ -in @("sync", "update") } {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ToolsDir "devin-sync.ps1") @RemainingArgs
        break
    }
    { $_ -in @("checkpoint", "commit") } {
        & cmd.exe /c (Join-Path $ToolsDir "devin-checkpoint.bat") @RemainingArgs
        break
    }
    { $_ -in @("state-init", "init") } {
        & cmd.exe /c (Join-Path $ToolsDir "devin-state-init.bat") @RemainingArgs
        break
    }
    { $_ -in @("run", "protect") } {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ToolsDir "devin-run.ps1") @RemainingArgs
        break
    }
    { $_ -in @("wait", "poll") } {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ToolsDir "devin-wait.ps1") @RemainingArgs
        break
    }
    { $_ -in @("rules", "directives") } {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ToolsDir "devin-verify.ps1")
        break
    }
    { $_ -in @("mcp", "servers") } {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ToolsDir "devin-verify.ps1")
        break
    }
    default {
        $desktopCli = "$env:LOCALAPPDATA\Programs\Devin\bin\devin-desktop.cmd"
        if (Test-Path $desktopCli) {
            & $desktopCli $Command @RemainingArgs
        } else {
            Write-Host "==========================================================" -ForegroundColor Cyan
            Write-Host "  DEVIN SWE 2.0 POWERPACK CLI                             " -ForegroundColor Cyan
            Write-Host "==========================================================" -ForegroundColor Cyan
            Write-Host "Usage: devin <command> [args...]`n"
            Write-Host "Available Commands:" -ForegroundColor Yellow
            Write-Host "  devin doctor / verify    Run live health & synchronization diagnostic"
            Write-Host "  devin remember <topic>   Query global cross-project knowledge vault"
            Write-Host "  devin bench <file>       Profile CPU time and peak RAM in KB"
            Write-Host "  devin learn <args...>    Index technical lessons passing 3-gate filter"
            Write-Host "  devin sync               Synchronize configs, rules & subagents"
            Write-Host "  devin checkpoint [msg]   Stage & commit atomic milestone progress"
            Write-Host "  devin state-init         Initialize fresh .mythos/state.md template"
            Write-Host "  devin run <cmd>          Protect context window from noisy CLI logs"
            Write-Host ""
        }
    }
}
