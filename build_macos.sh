#!/bin/bash

# FutureElite - macOS Build Script
# This script builds a macOS app bundle

echo "Building FutureElite for macOS..." | grep --color=always "Building FutureElite for macOS..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH" | grep --color=always "Error:"
    echo "Please install Python 3.11+ and try again" | grep --color=always "Please install Python 3.11+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "Found Python: $PYTHON_VERSION" | grep --color=always "Found Python:"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..." | grep --color=always "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..." | grep --color=always "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..." | grep --color=always "Installing requirements..."
pip install -r requirements.txt

# Clean previous builds
if [ -d "dist" ]; then
    echo "Cleaning previous builds..." | grep --color=always "Cleaning previous builds..."
    rm -rf dist
fi

if [ -d "build" ]; then
    rm -rf build
fi

# Build app bundle
echo "Building app bundle..." | grep --color=always "Building app bundle..."
pyinstaller --noconfirm --windowed --name "FutureElite" --add-data "app:app" --add-data "app/templates:templates" --add-data "app/static:static" --add-data "app/data:data" app/main.py

# Check if build was successful
if [ -d "dist/FutureElite.app" ]; then
    echo "Build successful!" | grep --color=always "Build successful!"
    echo "App bundle created: dist/FutureElite.app" | grep --color=always "App bundle created:"
    echo ""
    echo "To install the app:" | grep --color=always "To install the app:"
    echo "1. Drag FutureElite.app to your Applications folder" | grep --color=always "1. Drag FutureElite.app to your Applications folder"
    echo "2. Double-click the app in Applications to run it" | grep --color=always "2. Double-click the app in Applications to run it"
    echo ""
    echo "Note: You may need to right-click and select 'Open' the first time due to macOS security" | grep --color=always "Note:"
else
    echo "Build failed!" | grep --color=always "Build failed!"
    exit 1
fi

echo ""
echo "Build complete! You can now run FutureElite.app" | grep --color=always "Build complete! You can now run FutureElite.app"









