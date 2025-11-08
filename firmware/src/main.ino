/*
 * Barista Robot Arm Firmware
 * 
 * This firmware controls the robot arm to make drinks based on orders
 * received via Serial USB communication from the backend server.
 */

// Serial communication
const int BAUD_RATE = 9600;
String inputString = "";
boolean stringComplete = false;

// Robot arm state
enum ArmState {
  IDLE,
  PROCESSING_ORDER,
  MAKING_DRINK,
  COMPLETE,
  ERROR
};

ArmState currentState = IDLE;

void setup() {
  // Initialize serial communication
  Serial.begin(BAUD_RATE);
  inputString.reserve(200);
  
  // Initialize robot arm components
  initializeRobotArm();
  
  // Send ready signal to backend
  Serial.println("READY");
  
  currentState = IDLE;
}

void loop() {
  // Check for incoming serial data
  if (stringComplete) {
    processOrder(inputString);
    inputString = "";
    stringComplete = false;
  }
  
  // Update robot arm state machine
  updateRobotArm();
}

/*
 * Serial event handler - called when data is available
 */
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}

/*
 * Process order received from backend
 * Expected format: "ORDER:<drink_type>:<size>:<options>"
 * Example: "ORDER:ESPRESSO:SMALL:NONE"
 */
void processOrder(String order) {
  order.trim();
  
  if (order.startsWith("ORDER:")) {
    currentState = PROCESSING_ORDER;
    
    // Parse order string
    String orderData = order.substring(6); // Remove "ORDER:" prefix
    String drinkType = "";
    String size = "";
    String options = "";
    
    // Simple parsing (can be enhanced)
    int firstColon = orderData.indexOf(':');
    int secondColon = orderData.indexOf(':', firstColon + 1);
    
    if (firstColon > 0) {
      drinkType = orderData.substring(0, firstColon);
      if (secondColon > 0) {
        size = orderData.substring(firstColon + 1, secondColon);
        options = orderData.substring(secondColon + 1);
      } else {
        size = orderData.substring(firstColon + 1);
      }
    } else {
      drinkType = orderData;
    }
    
    // Execute drink making sequence
    makeDrink(drinkType, size, options);
  } else if (order == "STATUS") {
    // Respond with current status
    sendStatus();
  } else if (order == "RESET") {
    // Reset robot arm to idle state
    resetRobotArm();
  }
}

/*
 * Initialize robot arm components
 * Add your hardware initialization code here
 */
void initializeRobotArm() {
  // TODO: Initialize servos, motors, sensors, etc.
  // Example:
  // servo1.attach(SERVO1_PIN);
  // pinMode(SENSOR_PIN, INPUT);
}

/*
 * Make drink based on order parameters
 */
void makeDrink(String drinkType, String size, String options) {
  currentState = MAKING_DRINK;
  Serial.println("STATUS:MAKING_DRINK");
  
  // TODO: Implement drink-making sequence
  // This will depend on your specific robot arm configuration
  // Example sequence:
  // 1. Move to cup position
  // 2. Dispense ingredients based on drink type
  // 3. Mix/stir if needed
  // 4. Return to home position
  
  // Simulate drink making (replace with actual robot control)
  delay(2000); // Simulate work time
  
  currentState = COMPLETE;
  Serial.println("STATUS:COMPLETE");
  Serial.println("ORDER_COMPLETE");
  
  // Return to idle after completion
  delay(500);
  currentState = IDLE;
  Serial.println("STATUS:IDLE");
}

/*
 * Update robot arm state machine
 */
void updateRobotArm() {
  // TODO: Add continuous monitoring and control logic
  // This could include:
  // - Checking sensor readings
  // - Updating servo positions
  // - Monitoring for errors
}

/*
 * Send current status to backend
 */
void sendStatus() {
  String status;
  switch (currentState) {
    case IDLE:
      status = "IDLE";
      break;
    case PROCESSING_ORDER:
      status = "PROCESSING_ORDER";
      break;
    case MAKING_DRINK:
      status = "MAKING_DRINK";
      break;
    case COMPLETE:
      status = "COMPLETE";
      break;
    case ERROR:
      status = "ERROR";
      break;
  }
  Serial.println("STATUS:" + status);
}

/*
 * Reset robot arm to idle state
 */
void resetRobotArm() {
  currentState = IDLE;
  // TODO: Move robot arm to home position
  Serial.println("STATUS:IDLE");
  Serial.println("RESET_COMPLETE");
}

