# Arduino Firmware Upload

## Quick Start

### Option 1: Using the Upload Script (Recommended)

From Cursor terminal, run:

```bash
cd firmware
./upload.sh
```

The script will:
- Install `arduino-cli` if needed (via Homebrew)
- Detect your Arduino board
- Install required libraries (AccelStepper)
- Compile and upload the code

### Option 2: Manual Upload

1. **Install arduino-cli:**
   ```bash
   brew install arduino-cli
   ```

2. **Initialize and update:**
   ```bash
   arduino-cli config init
   arduino-cli core update-index
   ```

3. **List available boards:**
   ```bash
   arduino-cli board list
   ```

4. **Install board core (e.g., for Uno):**
   ```bash
   arduino-cli core install arduino:avr
   ```

5. **Install AccelStepper library:**
   ```bash
   arduino-cli lib install AccelStepper
   ```

6. **Compile:**
   ```bash
   arduino-cli compile --fqbn arduino:avr:uno src/
   ```

7. **Upload:**
   ```bash
   arduino-cli upload -p /dev/cu.usbmodem* --fqbn arduino:avr:uno src/
   ```
   (Replace `/dev/cu.usbmodem*` with your actual port from `arduino-cli board list`)

## Current Code

The current `main.ino` tests a single stepper motor:
- STEP pin: 2
- DIR pin: 3
- Moves 80 steps forward, then back to 0, continuously

## Troubleshooting

- **Board not detected:** Make sure Arduino is connected via USB and drivers are installed
- **Permission denied:** On macOS, you may need to allow the USB device in System Preferences
- **Library not found:** Run `arduino-cli lib install AccelStepper`
- **Wrong board:** Update the FQBN in the script or use manual commands with your board type
