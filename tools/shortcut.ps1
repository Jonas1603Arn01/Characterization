# Creates a "Characterization" shortcut on the desktop that starts
# the app via start.bat (with the app icon).

$ErrorActionPreference = "Stop"
$app = Split-Path -Parent $PSScriptRoot   # tools\ -> app folder
$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop "Characterization.lnk"

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut($lnkPath)
$lnk.TargetPath = Join-Path $app "start.bat"
$lnk.WorkingDirectory = $app
$lnk.IconLocation = (Join-Path $app "static\icon.ico") + ",0"
$lnk.Description = "Start Characterization"
$lnk.Save()

Write-Host "The 'Characterization' shortcut is now on your desktop." -ForegroundColor Green
