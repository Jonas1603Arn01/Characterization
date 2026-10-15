@echo off
title Characterization - create desktop shortcut
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\tools\shortcut.ps1"
echo.
pause
