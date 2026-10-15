#!/usr/bin/env powershell
# Characterization: setup for a new PC
# Creates .venv, installs dependencies, sets up the data folders

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)   # tools\ -> app folder

Write-Host "=== Characterization setup ===" -ForegroundColor Green
Write-Host ""

# 1. Check Python
Write-Host "1. Checking Python..."
try {
    $pyVersion = python --version 2>&1 | Select-String "\d+\.\d+"
    if ($pyVersion -match "3\.1[2-9]") {
        Write-Host "   ✓ Python $($pyVersion -replace 'Python ') found" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ Python $($pyVersion) — Python 3.12+ is required" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ✗ Python not found. Please install Python 3.12+." -ForegroundColor Red
    exit 1
}

# 2. Create or reuse .venv
Write-Host ""
Write-Host "2. Virtual environment..."
if (Test-Path ".venv") {
    Write-Host "   ✓ .venv already exists" -ForegroundColor Green
} else {
    Write-Host "   Creating .venv..."
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ .venv created" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Error while creating .venv" -ForegroundColor Red
        exit 1
    }
}

# 3. Activate
Write-Host "   Activating .venv..."
$activateScript = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Host "   ✗ Activate.ps1 not found" -ForegroundColor Red
    exit 1
}

# 4. Install dependencies
Write-Host ""
Write-Host "3. Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ✗ Error during installation" -ForegroundColor Red
    exit 1
}

# 5. Create data folders
Write-Host ""
Write-Host "4. Creating folders..."
@("data", "backups") | ForEach-Object {
    if (!(Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ | Out-Null
        Write-Host "   ✓ Folder '$_' created" -ForegroundColor Green
    } else {
        Write-Host "   ✓ Folder '$_' present" -ForegroundColor Green
    }
}

# 6. Run tests (optional)
Write-Host ""
Write-Host "5. Run tests (optional)..."
$runTests = Read-Host "Run the tests? (y/n)"
if ($runTests -eq "y") {
    pytest tests -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ All tests passed" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ Some tests failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "   (skipped)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host "Start with: python run.py" -ForegroundColor Cyan
