@echo off
REM Characterization: setup for a new PC (Windows batch fallback)
REM Use this script if setup.ps1 does not work
cd /d "%~dp0.."

echo === Characterization setup ===
echo.

REM 1. Check Python
echo 1. Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo    X Python not found. Please install Python 3.12+.
    pause
    exit /b 1
)
python --version
echo    OK
echo.

REM 2. Create .venv
echo 2. Creating virtual environment...
if exist .venv (
    echo    OK - .venv already exists
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo    X Error while creating .venv
        pause
        exit /b 1
    )
    echo    OK - .venv created
)
echo.

REM 3. Activate .venv and install dependencies
echo 3. Installing dependencies...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo    X Error while activating the virtual environment
    pause
    exit /b 1
)
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo    X Error during installation
    pause
    exit /b 1
)
echo    OK
echo.

REM 4. Create data folders
echo 4. Creating folders...
if not exist data mkdir data
if not exist backups mkdir backups
echo    OK
echo.

echo === Setup complete ===
echo Start with: python run.py
echo.
pause
