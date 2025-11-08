"""
Barista Robot Backend Server

Handles order processing and communication with the robot arm via Serial USB.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Serial connection to Arduino
serial_connection: Optional[serial.Serial] = None
serial_lock = threading.Lock()

# Configuration
SERIAL_BAUD_RATE = 9600
SERIAL_TIMEOUT = 1


def find_arduino_port() -> Optional[str]:
    """Find the Arduino port automatically."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Common Arduino identifiers
        if 'arduino' in port.description.lower() or 'usb' in port.description.lower():
            return port.device
    return None


def connect_to_arduino(port: Optional[str] = None) -> bool:
    """Connect to Arduino via Serial USB."""
    global serial_connection
    
    if port is None:
        port = find_arduino_port()
    
    if port is None:
        print("Error: Could not find Arduino port")
        return False
    
    try:
        with serial_lock:
            if serial_connection and serial_connection.is_open:
                serial_connection.close()
            
            serial_connection = serial.Serial(
                port=port,
                baudrate=SERIAL_BAUD_RATE,
                timeout=SERIAL_TIMEOUT
            )
            print(f"Connected to Arduino on {port}")
            
            # Wait for Arduino to initialize
            time.sleep(2)
            
            # Read initial "READY" message
            if serial_connection.in_waiting:
                response = serial_connection.readline().decode('utf-8').strip()
                print(f"Arduino: {response}")
            
            return True
    except Exception as e:
        print(f"Error connecting to Arduino: {e}")
        return False


def send_to_arduino(command: str) -> bool:
    """Send command to Arduino via Serial."""
    global serial_connection
    
    if not serial_connection or not serial_connection.is_open:
        return False
    
    try:
        with serial_lock:
            serial_connection.write(f"{command}\n".encode('utf-8'))
            return True
    except Exception as e:
        print(f"Error sending to Arduino: {e}")
        return False


def read_from_arduino() -> Optional[str]:
    """Read response from Arduino."""
    global serial_connection
    
    if not serial_connection or not serial_connection.is_open:
        return None
    
    try:
        with serial_lock:
            if serial_connection.in_waiting:
                response = serial_connection.readline().decode('utf-8').strip()
                return response
    except Exception as e:
        print(f"Error reading from Arduino: {e}")
    
    return None


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'arduino_connected': serial_connection is not None and serial_connection.is_open
    })


@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new drink order."""
    try:
        data = request.json
        
        # Validate order data
        required_fields = ['drink_type', 'size']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        drink_type = data['drink_type']
        size = data['size']
        options = data.get('options', 'NONE')
        
        # Format order command for Arduino
        order_command = f"ORDER:{drink_type}:{size}:{options}"
        
        # Send order to Arduino
        if not send_to_arduino(order_command):
            return jsonify({'error': 'Failed to send order to robot arm'}), 500
        
        # Wait for acknowledgment (simplified - could be enhanced with async handling)
        time.sleep(0.5)
        response = read_from_arduino()
        
        # Create order response
        order_response = {
            'id': int(time.time()),  # Simple ID generation
            'drink_type': drink_type,
            'size': size,
            'options': options,
            'status': 'processing',
            'arduino_response': response
        }
        
        return jsonify(order_response), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders/<int:order_id>/status', methods=['GET'])
def get_order_status(order_id):
    """Get status of an order."""
    # Request status from Arduino
    send_to_arduino("STATUS")
    time.sleep(0.2)
    response = read_from_arduino()
    
    return jsonify({
        'order_id': order_id,
        'status': response or 'unknown',
        'arduino_connected': serial_connection is not None and serial_connection.is_open
    })


@app.route('/api/robot/status', methods=['GET'])
def get_robot_status():
    """Get current robot arm status."""
    send_to_arduino("STATUS")
    time.sleep(0.2)
    response = read_from_arduino()
    
    return jsonify({
        'status': response or 'unknown',
        'connected': serial_connection is not None and serial_connection.is_open
    })


@app.route('/api/robot/reset', methods=['POST'])
def reset_robot():
    """Reset robot arm to idle state."""
    if send_to_arduino("RESET"):
        time.sleep(0.5)
        response = read_from_arduino()
        return jsonify({
            'message': 'Reset command sent',
            'response': response
        })
    else:
        return jsonify({'error': 'Failed to send reset command'}), 500


@app.route('/api/robot/connect', methods=['POST'])
def connect_robot():
    """Manually connect to robot arm."""
    data = request.json
    port = data.get('port') if data else None
    
    if connect_to_arduino(port):
        return jsonify({'message': 'Connected to robot arm'})
    else:
        return jsonify({'error': 'Failed to connect to robot arm'}), 500


if __name__ == '__main__':
    # Try to connect to Arduino on startup
    print("Attempting to connect to Arduino...")
    connect_to_arduino()
    
    # Start Flask server
    app.run(debug=True, host='0.0.0.0', port=5000)

