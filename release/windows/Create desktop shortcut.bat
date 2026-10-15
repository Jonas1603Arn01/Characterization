@echo off
title Characterization - create desktop shortcut
REM Puts a "Characterization" shortcut on the desktop that starts
REM Characterization.exe from this folder (with the program's icon).
REM Run it again after moving the folder somewhere else.
set "APP_EXE=%~dp0Characterization.exe"
if not exist "%APP_EXE%" (
    echo Characterization.exe was not found next to this file.
    echo.
    echo You probably downloaded the source code. On the GitHub Releases page,
    echo download Characterization-VERSION-windows.zip instead ^(not
    echo "Source code"^), extract it and run this file from that folder.
    echo.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$exe = $env:APP_EXE;" ^
  "$lnk = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Characterization.lnk'));" ^
  "$lnk.TargetPath = $exe;" ^
  "$lnk.WorkingDirectory = Split-Path -Parent $exe;" ^
  "$lnk.IconLocation = $exe + ',0';" ^
  "$lnk.Description = 'Start Characterization';" ^
  "$lnk.Save();" ^
  "Write-Host 'The Characterization shortcut is now on your desktop.' -ForegroundColor Green"
echo.
pause
