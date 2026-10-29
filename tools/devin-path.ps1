# Devin Autonomous Path & Target Resolver
# Resolves any binary, directory, config, or target path instantly without asking the user.

param(
    [Parameter(Position = 0, Mandatory = $true)]
    [string]$TargetName,

    [switch]$Dir,
    [switch]$All
)

$targetClean = $TargetName.Trim().Trim('"').Trim("'")
$results = [System.Collections.Generic.List[string]]::new()

# 1. Check if it's already an existing valid path
if (Test-Path $targetClean) {
    $results.Add((Resolve-Path $targetClean).Path)
}

# 2. Check targets.json in current directory or parents
$curr = (Get-Location).Path
while ($curr) {
    $tj = Join-Path $curr "targets.json"
    if (Test-Path $tj) {
        try {
            $json = Get-Content $tj -Raw | ConvertFrom-Json
            if ($json.PSObject.Properties[$targetClean]) {
                $p = $json.$targetClean
                if (Test-Path $p) { $results.Add((Resolve-Path $p).Path) }
            }
        } catch {}
    }
    $parent = Split-Path $curr -Parent
    if ($parent -eq $curr) { break }
    $curr = $parent
}

# 3. Fast Workspace Search (Depth 4)
$wsMatches = @(Get-ChildItem -Path . -Filter "*$targetClean*" -Depth 4 -ErrorAction SilentlyContinue)
foreach ($m in $wsMatches) {
    if ($Dir -and -not $m.PSIsContainer) { continue }
    $results.Add($m.FullName)
}

# 4. Standard App & Target Roots if not found yet
if ($results.Count -eq 0) {
    $searchRoots = @(
        "E:\the-binary\manual\targets",
        "E:\the-binary\packteam-hub\targets",
        "E:\SteamLibrary\steamapps\common",
        "C:\Program Files (x86)\Steam\steamapps\common",
        "C:\Program Files (x86)",
        "C:\Program Files",
        "E:\apps",
        "$env:LOCALAPPDATA\Programs",
        "$env:APPDATA"
    )

    foreach ($root in $searchRoots) {
        if (Test-Path $root) {
            $found = @(Get-ChildItem -Path $root -Filter "*$targetClean*" -Depth 2 -ErrorAction SilentlyContinue)
            foreach ($f in $found) {
                if ($Dir -and -not $f.PSIsContainer) { continue }
                $results.Add($f.FullName)
            }
            if ($results.Count -gt 0 -and -not $All) { break }
        }
    }
}

if ($results.Count -gt 0) {
    if ($All) {
        $results | Select-Object -Unique
    } else {
        # Pick the best/most relevant: prefer files with exact base name, or most recently modified
        $sorted = $results | Select-Object -Unique | Sort-Object { 
            if ([System.IO.Path]::GetFileNameWithoutExtension($_) -ieq $targetClean) { 0 }
            elseif ([System.IO.Path]::GetFileName($_) -ieq $targetClean) { 1 }
            else { 2 }
        }
        $best = $sorted | Select-Object -First 1
        Write-Output $best
    }
    exit 0
} else {
    Write-Error "Could not resolve path for target '$targetClean'"
    exit 1
}
