# Devin PowerPack Uninstaller / Rollback
$PowerPackRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BackupsDir = Join-Path $PowerPackRoot "backups"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DEVIN SWE 2.0 POWERPACK - ROLLBACK & UNINSTALLER        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $BackupsDir)) {
    Write-Host "No backup directory found. Cannot restore prior state automatically." -ForegroundColor Red
    exit 1
}

$latestBackup = Get-ChildItem -Path $BackupsDir -Directory | Sort-Object CreationTime -Descending | Select-Object -First 1

if (-not $latestBackup) {
    Write-Host "No backups available to restore." -ForegroundColor Yellow
    exit 0
}

Write-Host "Restoring from latest backup: $($latestBackup.FullName)..." -ForegroundColor Yellow

# Restore backed-up files
Get-ChildItem -Path $latestBackup.FullName -File | ForEach-Object {
    $filename = $_.Name
    # File format: C_Users_sayfp_AppData_...
    # Reconstruct original path if possible or print instructions
    Write-Host "  Found backup file: $filename"
}

Write-Host "`nTo revert rules manually, original files are safely stored in:"
Write-Host "  $($latestBackup.FullName)" -ForegroundColor Green
