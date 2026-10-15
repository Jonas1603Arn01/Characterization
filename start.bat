@echo off
title Characterization - server (keep this window open)
cd /d "%~dp0"

REM Networks that intercept SSL (company/university) need trusted-host for pip
set "PIP_CONFIG_FILE=%~dp0pip.ini"
set "VENV_PY=.venv\Scripts\python.exe"

REM --- Check whether the venv exists AND works on this PC ---
if not exist "%VENV_PY%" goto rebuild
"%VENV_PY%" -c "import sys" >nul 2>&1
if errorlevel 1 goto rebuild
goto run

:rebuild
echo ============================================================
echo   The virtual environment is missing or was created on a
echo   different PC. It will be rebuilt now - this takes a few
echo   minutes on first run. Please wait.
echo ============================================================
if exist ".venv" rmdir /s /q ".venv"

REM --- Find a suitable Python (3.12 preferred) ---
set "PYLAUNCH="
py -3.12 --version >nul 2>&1 && set "PYLAUNCH=py -3.12"
if not defined PYLAUNCH py -3 --version >nul 2>&1 && set "PYLAUNCH=py -3"
if not defined PYLAUNCH python --version >nul 2>&1 && set "PYLAUNCH=python"
if not defined PYLAUNCH goto nopython

echo Creating environment with %PYLAUNCH% ...
%PYLAUNCH% -m venv .venv
if errorlevel 1 goto venvfail

echo Updating pip ...
"%VENV_PY%" -m pip install --upgrade pip
echo Installing packages - rdkit, FastAPI and others ...
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto pipfail

echo Setup complete. Starting the application.

:run
"%VENV_PY%" run.py
goto end

:nopython
echo.
echo ERROR: No Python found.
echo Please install Python 3.12: https://www.python.org/downloads/
echo During setup, tick "Add python.exe to PATH".
echo.
pause
goto end

:venvfail
echo ERROR while creating the virtual environment.
pause
goto end

:pipfail
echo ERROR during package installation.
pause
goto end

:end
