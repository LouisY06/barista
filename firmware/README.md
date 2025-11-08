# Barista Robot Arm Firmware

Arduino C++ firmware for controlling the robot arm that makes drinks based on orders received from the backend server.

## Hardware Requirements

- Arduino board (Uno, Mega, or compatible)
- Robot arm components (servos, motors, sensors as needed)
- USB cable for serial communication

## Setup

1. Install [Arduino IDE](https://www.arduino.cc/en/software) or use [PlatformIO](https://platformio.org/)

2. Open `src/main.ino` in Arduino IDE

3. Install any required libraries (add as needed for your specific hardware)

4. Select your Arduino board and port in the IDE

5. Upload the sketch to your Arduino

## Communication Protocol

The firmware communicates with the backend via Serial USB at 9600 baud.

### Commands Received from Backend

- `ORDER:<drink_type>:<size>:<options>` - Execute a drink order
  - Example: `ORDER:ESPRESSO:MEDIUM:NONE`
  
- `STATUS` - Request current robot status
  - Response: `STATUS:<state>` where state is IDLE, PROCESSING_ORDER, MAKING_DRINK, COMPLETE, or ERROR

- `RESET` - Reset robot arm to idle state
  - Response: `RESET_COMPLETE`

### Messages Sent to Backend

- `READY` - Sent on startup when robot is ready
- `STATUS:<state>` - Current robot state
- `ORDER_COMPLETE` - Order has been completed
- `STATUS:IDLE` - Robot returned to idle state

## Customization

You'll need to implement the following functions based on your specific robot arm hardware:

- `initializeRobotArm()` - Initialize servos, motors, sensors
- `makeDrink()` - Implement the actual drink-making sequence
- `updateRobotArm()` - Continuous monitoring and control logic
- `resetRobotArm()` - Move robot to home position

## Building

### Using Arduino IDE

1. Open `src/main.ino`
2. Select Tools > Board > [Your Board]
3. Select Tools > Port > [Your Port]
4. Click Upload

### Using PlatformIO

```bash
cd firmware
pio run --target upload
```

## Testing

1. Connect Arduino via USB
2. Open Serial Monitor at 9600 baud
3. Send test commands:
   - `STATUS` - Should return current status
   - `ORDER:ESPRESSO:SMALL:NONE` - Should process order
   - `RESET` - Should reset robot

## Troubleshooting

- **No serial communication**: Check USB cable and port selection
- **Commands not recognized**: Ensure commands end with newline character
- **Robot not responding**: Verify hardware connections and power supply

