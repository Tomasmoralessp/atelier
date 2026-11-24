#!/bin/bash

# Build desktop applications for Atelier Gallery
echo "Building desktop applications..."

cd frontend

# Check if Tauri is installed
if ! command -v tauri &> /dev/null; then
    echo "Tauri CLI not found. Installing..."
    npm install -g @tauri-apps/cli
fi

# Build the application for all platforms
echo "Building for all platforms..."
npm run tauri build

echo "Desktop applications built successfully!"
echo "Check frontend/src-tauri/target/release/bundle/ for the built files."