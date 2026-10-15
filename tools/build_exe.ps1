# Builds the packaged program: dist\Characterization\Characterization.exe
# plus dist\Characterization-<version>-windows.zip for a GitHub release.
#
#   powershell -ExecutionPolicy Bypass -File tools\build_exe.ps1 [-Version 1.2.0] [-Test]
#
# Uses its own environment (.venv-build) so the everyday .venv stays as it is.
# The build contains only program files: static\, app\ and the Python
# packages. data\, backups\, config.json and the Git history never go in;
# a check at the end aborts if any of them turns up anyway.
param(
    [string]$Version = "",
    [switch]$Test
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not $Version) { $Version = "dev-" + (Get-Date -Format "yyyy-MM-dd") }
$Version = $Version.TrimStart("v")

$py = ".venv-build\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Creating build environment (.venv-build) ..."
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) { & py -3.12 -m venv .venv-build } else { & python -m venv .venv-build }
    if ($LASTEXITCODE) { throw "Could not create .venv-build" }
}
$env:PIP_CONFIG_FILE = (Resolve-Path "pip.ini").Path
& $py -m pip install --disable-pip-version-check -q -r requirements.txt -r requirements-build.txt
if ($LASTEXITCODE) { throw "pip install failed" }

if ($Test) {
    & $py -m pytest tests -q
    if ($LASTEXITCODE) { throw "Tests failed - no build" }
}

New-Item -ItemType Directory -Force build | Out-Null
[IO.File]::WriteAllText("$PWD\build\VERSION", "$Version`n")

& $py -m PyInstaller --noconfirm --clean Characterization.spec
if ($LASTEXITCODE) { throw "PyInstaller failed" }

# Safety check: no dataset, settings or developer files in the build
$out = "dist\Characterization"
$leaks = @(Get-ChildItem $out -Recurse -Force | Where-Object {
    $_.Name -in @("app.db", "config.json", "in-use.lock", ".git", ".claude", ".venv") -or
    $_.Extension -in @(".db", ".cdx")
}) + @(Get-ChildItem $out, "$out\_internal" -Force | Where-Object {
    $_.Name -in @("data", "backups", "undo", "images")
})
$leaks = $leaks | Where-Object { $_ }
if ($leaks) {
    $leaks | ForEach-Object { Write-Host "  $($_.FullName)" }
    throw "Build contains data or developer files - aborted"
}

$zip = "dist\Characterization-$Version-windows.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path $out -DestinationPath $zip
Write-Host ""
Write-Host "Done: $out\Characterization.exe"
Write-Host "      $zip"
