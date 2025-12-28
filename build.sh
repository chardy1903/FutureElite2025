#!/bin/bash
# Build script for FutureElite
# Builds Tailwind CSS before deployment

set -e

echo "Building Tailwind CSS..."

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Build Tailwind CSS
npm run build:css

echo "Build complete!"

