# Installs a new version of the app WITHOUT touching user data.
# Preserved: data\ (database, images), backups\ and the virtual
# environment (.venv). Only program files are replaced.

$ErrorActionPreference = "Stop"
$app = Split-Path -Parent $PSScriptRoot   # tools\ -> app folder

Write-Host "=== Characterization: install update ===" -ForegroundColor Green
Write-Host ""

# 1) Is the app still running? Ask the user to close it first.
$client = New-Object Net.Sockets.TcpClient
try {
    $client.Connect("127.0.0.1", 8710)
    $client.Close()
    Write-Host "The app is still running. Please close the server window first," -ForegroundColor Yellow
    Write-Host "then run this update again."
    return
} catch {
    # Port closed -> app is off, carry on
} finally {
    $client.Dispose()
}

# 2) Find the newest update ZIP (Downloads, Desktop).
# Also matches the old German ZIP name for updates from earlier versions.
$searchDirs = @(
    (Join-Path $env:USERPROFILE "Downloads"),
    [Environment]::GetFolderPath("Desktop")
) | Where-Object { Test-Path $_ }

$zips = $searchDirs | ForEach-Object {
    $dir = $_
    @("Characterization-App*.zip", "Charakterisierung-App*.zip") | ForEach-Object {
        Get-ChildItem -Path $dir -Filter $_ -File -ErrorAction SilentlyContinue
    }
} | Sort-Object LastWriteTime -Descending

if ($zips) {
    $zipFile = $zips | Select-Object -First 1
} else {
    Write-Host "No 'Characterization-App...zip' found in Downloads or on the Desktop." -ForegroundColor Yellow
    $manual = Read-Host "Enter the full path to the ZIP (or press Enter to cancel)"
    if (-not $manual) { Write-Host "Cancelled." -ForegroundColor Yellow; return }
    $manual = $manual.Trim('"')
    if (-not (Test-Path $manual)) { Write-Host "File not found: $manual" -ForegroundColor Red; return }
    $zipFile = Get-Item $manual
}

Write-Host "Update found: $($zipFile.Name)"
Write-Host "  Location: $($zipFile.DirectoryName)"
Write-Host "  Dated:    $($zipFile.LastWriteTime)"
$ans = Read-Host "Install this update? (y/n)"
if ($ans -ne "y") { Write-Host "Cancelled." -ForegroundColor Yellow; return }

# 3) Extract the ZIP into a temp folder and verify it
$tmp = Join-Path $env:TEMP ("characterization-update-" + [Guid]::NewGuid().ToString("N"))
Write-Host ""
Write-Host "Extracting..."
Expand-Archive -Path $zipFile.FullName -DestinationPath $tmp -Force

# If the ZIP contains a subfolder: look for the app root inside it
$root = $tmp
if (-not (Test-Path (Join-Path $root "run.py"))) {
    $sub = Get-ChildItem -Directory $tmp |
        Where-Object { Test-Path (Join-Path $_.FullName "run.py") } |
        Select-Object -First 1
    if ($sub) { $root = $sub.FullName }
}
if (-not ((Test-Path (Join-Path $root "run.py")) -and (Test-Path (Join-Path $root "app\main.py")))) {
    Write-Host "ABORTED: the ZIP does not contain the Characterization app." -ForegroundColor Red
    Remove-Item -Recurse -Force $tmp
    return
}
if (Test-Path (Join-Path $root "data")) {
    Write-Host "ABORTED: the ZIP contains a data folder - that would be someone else's user data." -ForegroundColor Red
    Remove-Item -Recurse -Force $tmp
    return
}

# 4) Compare versions (ISO date -> text comparison = time comparison)
$oldV = ""
$newV = ""
if (Test-Path (Join-Path $app "VERSION"))  { $oldV = (Get-Content (Join-Path $app "VERSION") -TotalCount 1).Trim() }
if (Test-Path (Join-Path $root "VERSION")) { $newV = (Get-Content (Join-Path $root "VERSION") -TotalCount 1).Trim() }
if ($oldV -or $newV) {
    Write-Host "Installed version: $oldV  ->  update: $newV"
}
if ($oldV -and $newV -and ($newV -le $oldV)) {
    $ans = Read-Host "The update is NOT newer than the installed version. Install anyway? (y/n)"
    if ($ans -ne "y") { Remove-Item -Recurse -Force $tmp; Write-Host "Cancelled." -ForegroundColor Yellow; return }
}

# 5) Safety copy of the database (in addition to the regular backups)
$db = Join-Path $app "data\app.db"
if (Test-Path $db) {
    $bakDir = Join-Path $app "backups"
    New-Item -ItemType Directory -Force $bakDir | Out-Null
    $bak = Join-Path $bakDir ("pre-update-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".db")
    Copy-Item $db $bak
    Write-Host "Safety copy of the database: backups\$(Split-Path -Leaf $bak)"
}

# 6) Replace program files.
# Empty app\ and static\ first so renamed/deleted files do not linger.
# data\, backups\ and .venv are NEVER touched.
Write-Host "Replacing program files..."
foreach ($d in @("app", "static", "tests")) {
    $p = Join-Path $app $d
    if (Test-Path $p) { Remove-Item -Recurse -Force $p }
}
$roboArgs = @($root, $app, "/E",
              "/XD", "data", "backups", ".venv", "__pycache__",
              "/XF", "config.json",
              "/NFL", "/NDL", "/NJH", "/NP", "/R:1", "/W:1")
& robocopy @roboArgs | Out-Null
if ($LASTEXITCODE -ge 8) {
    Write-Host "ERROR while copying (robocopy $LASTEXITCODE)" -ForegroundColor Red
    Remove-Item -Recurse -Force $tmp
    return
}
# The "Distribute" feature is optional per handover: the update decides.
# If it is not included, remove it (otherwise an outdated copy would linger).
$pkgHasDistribute = Test-Path (Join-Path $root "tools\distribute.ps1")
Remove-Item -Recurse -Force $tmp
if (-not $pkgHasDistribute) {
    foreach ($f in @("Distribute.bat", "tools\distribute.ps1", "tools\test_server.py")) {
        $p = Join-Path $app $f
        if (Test-Path $p) { Remove-Item -Force $p }
    }
}

# 6b) Remove left-over files from older versions (German file names, and
# helper files that used to live in the root folder before "Help and tools")
foreach ($legacy in @("ANLEITUNG.txt", "Update einspielen.bat",
                      "Desktop-Verknuepfung erstellen.bat", "Weitergeben.bat",
                      "verteilen.ps1", "tools\verknuepfung.ps1",
                      "GETTING-STARTED.txt", "Install update.bat",
                      "Create desktop shortcut.bat", "setup.bat", "setup.ps1")) {
    $p = Join-Path $app $legacy
    if (Test-Path $p) { Remove-Item -Force $p }
}

# 7) Install new/changed Python packages (if the environment exists)
$venvPy = Join-Path $app ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    Write-Host "Updating Python packages (this can take a moment)..."
    $env:PIP_CONFIG_FILE = Join-Path $app "pip.ini"
    & $venvPy -m pip install -r (Join-Path $app "requirements.txt") --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Note: package installation failed." -ForegroundColor Yellow
        Write-Host "If the app does not start afterwards: delete the .venv folder and"
        Write-Host "run start.bat - the environment will then be rebuilt from scratch."
    }
}

Write-Host ""
if ($newV) {
    Write-Host "Update to version $newV complete." -ForegroundColor Green
} else {
    Write-Host "Update complete." -ForegroundColor Green
}
Write-Host "You can now start the app again via the desktop shortcut or start.bat."
Write-Host "All your data (projects, images, notes, backups) is unchanged."
