@echo off
title Characterization - create distribution copy
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\distribute.ps1"
echo.
pause
