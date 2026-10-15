# Creates a clean, shareable copy of the application.
# WITHOUT personal data (database, backups, images) and without anything
# that reveals the developer's setup (.git, .claude, Git files).
# Result: a folder + a dated ZIP on the desktop.
#
# The copy gets a version stamp (file VERSION, shown in the app header).
# Recipients install new versions via "Install update.bat" - their own
# data (data\, backups\) is preserved.

$ErrorActionPreference = "Stop"
$src = Split-Path -Parent $PSScriptRoot   # tools\ -> app folder

$desktop = [Environment]::GetFolderPath("Desktop")
$name = "Characterization-App"
$version = Get-Date -Format "yyyy-MM-dd"
# A copy that is passed on again keeps its original version: the code is
# unchanged, and a new date would make "Install update" treat it as newer
# than the originator's next real release.
$srcVersion = Join-Path $src "VERSION"
if (Test-Path $srcVersion) { $version = (Get-Content $srcVersion -TotalCount 1).Trim() }
$target = Join-Path $desktop $name
$zip = Join-Path $desktop "$name`_$version.zip"

Write-Host "=== Create distribution copy (version $version) ===" -ForegroundColor Green
Write-Host "Source: $src"
Write-Host "Target: $target"
Write-Host ""

# DO NOT distribute: personal data + PC-specific / temporary folders
$excludeDirs  = @(".venv", ".git", ".github", "data", "backups", "undo",
                  "__pycache__", ".pytest_cache", ".claude",
                  ".venv-build", "build", "dist")  # build_exe.ps1
# Safety net: never copy database/compiled files or developer files.
# Recipients do not need the developer setup scripts (start.bat sets
# everything up on its own).
# config.json is PC-specific (where the data folder lives) and must not travel.
$excludeFiles = @("*.db", "*.pyc", "*.pyo", ".gitignore", ".gitattributes",
                  "config.json", "in-use.lock",
                  "setup.bat", "setup.ps1")

# The "Distribute" feature itself is optional: with it, the recipient can
# pass the app on to others (always without their own data, too).
Write-Host "Include the 'Distribute' feature, so the recipient can pass the app on themselves?"
$withDistribute = (Read-Host "(y/n, default n)") -eq "y"
# test_server.py (app with a throw-away database) travels along: whoever
# receives the Distribute feature may also develop the app further.
if (-not $withDistribute) { $excludeFiles += @("Distribute.bat", "distribute.ps1", "test_server.py") }
Write-Host ""

if (Test-Path $target) {
    $ans = Read-Host "Target folder already exists. Replace it? (y/n)"
    if ($ans -ne "y") { Write-Host "Cancelled." -ForegroundColor Yellow; return }
    Remove-Item -Recurse -Force $target
}
if (Test-Path $zip) { Remove-Item -Force $zip }

# robocopy copies reliably with exclusions (bare names -> apply anywhere in the tree)
$roboArgs = @($src, $target, "/E", "/XD") + $excludeDirs + @("/XF") + $excludeFiles +
             @("/NFL", "/NDL", "/NJH", "/NP", "/R:1", "/W:1")
& robocopy @roboArgs | Out-Null
# robocopy: exit codes 0-7 = success, >=8 = error
if ($LASTEXITCODE -ge 8) {
    Write-Host "ERROR while copying (robocopy $LASTEXITCODE)" -ForegroundColor Red
    return
}

# Version stamp: shown in the app header and used by the update script
# for comparison (ISO date -> alphabetical = chronological)
Set-Content -Path (Join-Path $target "VERSION") -Value $version -Encoding ASCII

# --- Safety check: is the copy really free of personal data? ---
$leakDb   = Get-ChildItem -Recurse -File -Path $target -Filter *.db -ErrorAction SilentlyContinue
$leakData = Test-Path (Join-Path $target "data")
$leakBak  = Test-Path (Join-Path $target "backups")
$leakGit  = (Test-Path (Join-Path $target ".git")) -or (Test-Path (Join-Path $target ".claude"))
if ($leakDb -or $leakData -or $leakBak -or $leakGit) {
    Write-Host "ABORTED: personal data would have ended up in the copy!" -ForegroundColor Red
    if ($leakDb)   { Write-Host "  Database files found:"; $leakDb | ForEach-Object { Write-Host "   $($_.FullName)" } }
    if ($leakData) { Write-Host "  data folder present" }
    if ($leakBak)  { Write-Host "  backups folder present" }
    if ($leakGit)  { Write-Host "  .git or .claude folder present" }
    Remove-Item -Recurse -Force $target
    return
}

# ZIP for convenient sending (file name carries the version)
Compress-Archive -Path (Join-Path $target "*") -DestinationPath $zip -Force

Write-Host ""
Write-Host "Done - without your data." -ForegroundColor Green
if ($withDistribute) { Write-Host "  'Distribute' feature: included" }
else                 { Write-Host "  'Distribute' feature: not included" }
Write-Host "  Folder: $target"
Write-Host "  ZIP:    $zip"
Write-Host ""
Write-Host "FIRST-TIME handover: copy the folder (USB) or send the ZIP." -ForegroundColor Cyan
Write-Host "  The recipient needs Python 3.12, starts with start.bat and finds"
Write-Host "  everything else in 'Help and tools\GETTING-STARTED.txt'."
Write-Host "UPDATE for someone who already has the app: just send the ZIP." -ForegroundColor Cyan
Write-Host "  The recipient then double-clicks 'Help and tools\Install update.bat' -"
Write-Host "  their data is preserved."

# Show the result in Explorer
Start-Process explorer.exe "/select,`"$zip`""
