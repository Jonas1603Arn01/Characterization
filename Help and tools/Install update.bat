@echo off
title Characterization - install update
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\tools\update.ps1"
echo.
pause
