# FutureElite - Windows Build Script
# This script builds a single-file executable for Windows

Write-Host "Building FutureElite for Windows..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ and try again" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Clean previous builds
if (Test-Path "dist") {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "dist"
}

if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}

# Build executable
Write-Host "Building executable..." -ForegroundColor Yellow
pyinstaller --noconfirm --onefile --name "FutureElite" --add-data "app;app" --add-data "app/templates;templates" --add-data "app/static;static" --add-data "app/data;data" app/main.py

# Check if build was successful
if (Test-Path "dist\FutureElite.exe") {
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Executable created: dist\FutureElite.exe" -ForegroundColor Green
    Write-Host ""
    Write-Host "To create a desktop shortcut:" -ForegroundColor Yellow
    Write-Host "1. Right-click on your desktop" -ForegroundColor Yellow
    Write-Host "2. Select 'New' > 'Shortcut'" -ForegroundColor Yellow
    Write-Host "3. Browse to: $((Get-Location).Path)\dist\FutureElite.exe" -ForegroundColor Yellow
    Write-Host "4. Click 'Next' and name it 'FutureElite'" -ForegroundColor Yellow
    Write-Host "5. Click 'Finish'" -ForegroundColor Yellow
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build complete! You can now run FutureElite.exe" -ForegroundColor Green









