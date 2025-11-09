#include "AccelStepper.h"

// Define stepper motor connections and motor interface type. 
// Motor interface type must be set to 1 when using a driver:
#define dirPin 3
#define stepPin 2
#define motorInterfaceType 1

// Create a new instance of the AccelStepper class:
AccelStepper stepper = AccelStepper(motorInterfaceType, stepPin, dirPin);

// Serial communication
const int BAUD_RATE = 9600;
String inputString = "";
boolean stringComplete = false;

void setup() {
  // Initialize Serial communication with Python backend
  Serial.begin(BAUD_RATE);
  inputString.reserve(200);
  
  // Set the maximum speed and acceleration:
  stepper.setMaxSpeed(500);
  stepper.setAcceleration(500);
  
  // Send ready signal to Python backend
  delay(1000); // Wait for serial connection to establish
  Serial.println("READY");
}

void loop() {
  // Must call run() to keep motor moving if it has a target
  stepper.run();
  
  // Check for serial commands from Python
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
}

// Serial event handler - called when data is available
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    
    if (inChar == '\n' || inChar == '\r') {
      stringComplete = true;
    }
  }
}

void processCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();
  
  // Test motor forward
  if (cmd == "MOVE+") {
    stepper.moveTo(80);
    Serial.println("STATUS:MOVING_FORWARD");
  }
  // Test motor backward
  else if (cmd == "MOVE-") {
    stepper.moveTo(0);
    Serial.println("STATUS:MOVING_BACKWARD");
  }
  // Stop motor
  else if (cmd == "STOP") {
    stepper.stop();
    stepper.setCurrentPosition(0);
    Serial.println("STATUS:STOPPED");
  }
  // Status request
  else if (cmd == "STATUS") {
    if (stepper.isRunning()) {
      Serial.println("STATUS:RUNNING");
    } else {
      Serial.println("STATUS:IDLE");
    }
  }
  // Continuous test mode (original behavior)
  else if (cmd == "TEST") {
    // Set the target position:
    stepper.moveTo(80);
    // Run to target position with set speed and acceleration/deceleration:
    stepper.runToPosition();
    
    delay(1000);
    
    // Move back to zero:
    stepper.moveTo(0);
    stepper.runToPosition();
    
    delay(1000);
    Serial.println("STATUS:TEST_COMPLETE");
  }
  // Unknown command
  else {
    Serial.print("ERROR:Unknown command: ");
    Serial.println(cmd);
  }
}
