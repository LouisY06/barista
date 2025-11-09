#!/bin/bash
# Arduino Upload Script for Cursor
# Uploads firmware to Arduino board

set -e

FIRMWARE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKETCH_DIR="$FIRMWARE_DIR/src"
SKETCH_NAME="main.ino"

echo "=========================================="
echo "Arduino Firmware Upload Script"
echo "=========================================="

# Check if arduino-cli is installed
if ! command -v arduino-cli &> /dev/null; then
    echo "❌ arduino-cli not found!"
    echo ""
    echo "Installing arduino-cli via Homebrew..."
    
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    brew install arduino-cli
    echo "✓ arduino-cli installed"
fi

# Initialize arduino-cli config
echo ""
echo "📦 Setting up arduino-cli..."
arduino-cli config init --overwrite 2>/dev/null || true

# Update core index
echo "📥 Updating board index..."
arduino-cli core update-index

# Detect Arduino board (try common boards)
BOARD=""
if arduino-cli board list | grep -q "arduino:avr:uno"; then
    BOARD="arduino:avr:uno"
    echo "✓ Detected: Arduino Uno"
elif arduino-cli board list | grep -q "arduino:avr:nano"; then
    BOARD="arduino:avr:nano"
    echo "✓ Detected: Arduino Nano"
elif arduino-cli board list | grep -q "arduino:avr:mega"; then
    BOARD="arduino:avr:mega"
    echo "✓ Detected: Arduino Mega"
else
    echo ""
    echo "⚠️  Could not auto-detect board. Available boards:"
    arduino-cli board list
    echo ""
    read -p "Enter board FQBN (e.g., arduino:avr:uno): " BOARD
fi

# Install board core if needed
if [ -n "$BOARD" ]; then
    CORE=$(echo "$BOARD" | cut -d: -f1,2)
    echo "📦 Installing board core: $CORE"
    arduino-cli core install "$CORE"
fi

# Install AccelStepper library
echo ""
echo "📚 Installing AccelStepper library..."
arduino-cli lib install "AccelStepper"

# Compile
echo ""
echo "🔨 Compiling sketch..."
arduino-cli compile --fqbn "$BOARD" "$SKETCH_DIR"

if [ $? -ne 0 ]; then
    echo "❌ Compilation failed!"
    exit 1
fi

echo "✓ Compilation successful!"

# Upload
echo ""
echo "📤 Uploading to board..."
arduino-cli upload -p $(arduino-cli board list | grep "$BOARD" | head -1 | awk '{print $1}') --fqbn "$BOARD" "$SKETCH_DIR"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Upload successful!"
    echo ""
    echo "The motor should now be running the test sequence."
else
    echo "❌ Upload failed!"
    exit 1
fi

