"""
Barista Robot Backend Server

Handles order processing and communication with the robot arm via Serial USB.
"""

from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional, Tuple
import uuid
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import os
import base64
import binascii
import logging
from logging.handlers import RotatingFileHandler
from .object_detection import get_detector, detect_from_array, detect_from_file

from .vision.calibration_service import bp_calib
from .vision.sift_service import bp_sift
from .vision.aruco_service import bp_aruco
from .storage import (
    init_db,
    save_order,
    save_receipt,
    get_orders,
    get_order,
    get_receipts,
    update_order,
)

app = Flask(__name__)
app.register_blueprint(bp_calib)
app.register_blueprint(bp_sift)
app.register_blueprint(bp_aruco)
CORS(app)  # Enable CORS for frontend communication

# Ensure persistence layer is ready
init_db()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('backend.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Serial connection to Arduino
serial_connection: Optional[serial.Serial] = None
serial_lock = threading.Lock()

# Configuration
SERIAL_BAUD_RATE = 9600
SERIAL_TIMEOUT = 1

# Object detection configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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
        logger.error("Could not find Arduino port")
        return False
    
    try:
        with serial_lock:
            if serial_connection and serial_connection.is_open:
                logger.info("Closing existing serial connection")
                serial_connection.close()
            
            serial_connection = serial.Serial(
                port=port,
                baudrate=SERIAL_BAUD_RATE,
                timeout=SERIAL_TIMEOUT
            )
            logger.info(f"Connected to Arduino on {port}")
            
            # Wait for Arduino to initialize
            time.sleep(2)
            
            # Read initial "READY" message
            if serial_connection.in_waiting:
                response = serial_connection.readline().decode('utf-8').strip()
                logger.info(f"Arduino: {response}")
            
            return True
    except Exception as e:
        logger.error(f"Error connecting to Arduino: {e}", exc_info=True)
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
        logger.error(f"Error sending to Arduino: {e}", exc_info=True)
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
        logger.error(f"Error reading from Arduino: {e}", exc_info=True)
    
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
    """
    Create a new drink order.
    
    The robot will use its camera to detect objects (like cups) before executing the order.
    """
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
        # The robot will use CV to find objects when it receives this command
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
            'arduino_response': response,
            'note': 'Robot will use CV to detect objects before executing order'
        }

        # Persist a minimal record so we track hardware-triggered orders too
        try:
            save_order({
                'order_id': str(order_response['id']),
                'customer_id': data.get('customer_id'),
                'customer_name': data.get('customer_name'),
                'customer_email': data.get('customer_email'),
                'status': 'processing',
                'total': data.get('total'),
                'items': [data],
                'metadata': {'source': 'hardware-order'},
            })
        except Exception as db_error:
            logger.warning(f"Failed to persist order {order_response['id']}: {db_error}")
        
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


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_image_from_request(request) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Parse image from request (either multipart form or JSON base64).
    
    Returns:
        Tuple of (image_array, error_message)
        If successful: (image, None)
        If error: (None, error_message)
    """
    image = None
    error = None
    
    # Check if image is uploaded as file
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_IMAGE_SIZE:
                return None, f'Image file too large. Maximum size: {MAX_IMAGE_SIZE / (1024*1024):.1f}MB'
            
            if file_size == 0:
                return None, 'Empty image file'
            
            try:
                file_bytes = file.read()
                if len(file_bytes) > MAX_IMAGE_SIZE:
                    return None, f'Image file too large. Maximum size: {MAX_IMAGE_SIZE / (1024*1024):.1f}MB'
                
                nparr = np.frombuffer(file_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    return None, 'Could not decode image file. Invalid image format.'
            except Exception as e:
                return None, f'Error reading image file: {str(e)}'
    
    # Check if image is sent as base64
    elif request.is_json and 'image' in request.json:
        try:
            image_data = request.json['image']
            if not image_data:
                return None, 'Empty image data'
            
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Check base64 size (rough estimate: base64 is ~33% larger than binary)
            if len(image_data) > (MAX_IMAGE_SIZE * 4 / 3):
                return None, f'Image data too large. Maximum size: {MAX_IMAGE_SIZE / (1024*1024):.1f}MB'
            
            image_bytes = base64.b64decode(image_data)
            if len(image_bytes) > MAX_IMAGE_SIZE:
                return None, f'Image data too large. Maximum size: {MAX_IMAGE_SIZE / (1024*1024):.1f}MB'
            
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return None, 'Could not decode base64 image. Invalid image format.'
        except binascii.Error:
            return None, 'Invalid base64 image data'
        except Exception as e:
            return None, f'Error decoding base64 image: {str(e)}'
    
    if image is None:
        return None, 'No valid image provided. Send as multipart file or JSON base64.'
    
    return image, None


def validate_confidence(confidence: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Validate and clamp confidence value."""
    try:
        conf = float(confidence)
        return max(min_val, min(max_val, conf))
    except (ValueError, TypeError):
        return 0.5  # Default value


@app.route('/api/vision/detect', methods=['POST'])
def detect_objects():
    """
    Detect objects in an uploaded image.
    
    Accepts:
    - Multipart form data with 'image' file
    - JSON with 'image' as base64 encoded string
    
    Optional query parameters:
    - confidence: Confidence threshold (0.0-1.0, default: 0.5)
    - annotate: Return annotated image (true/false, default: false)
    """
    try:
        confidence = validate_confidence(request.args.get('confidence', 0.5))
        annotate = request.args.get('annotate', 'false').lower() == 'true'
        
        # Parse image from request
        image, error = parse_image_from_request(request)
        if error:
            return jsonify({'error': error}), 400
        
        # Initialize detector with custom confidence
        detector = get_detector(confidence=confidence)
        
        # Detect objects
        detections = detector.detect_objects(image)
        
        response = {
            'detections': detections,
            'count': len(detections)
        }
        
        # Add annotated image if requested
        if annotate:
            annotated = detector.annotate_image(image, detections)
            # Encode as base64
            _, buffer = cv2.imencode('.jpg', annotated)
            annotated_base64 = base64.b64encode(buffer).decode('utf-8')
            response['annotated_image'] = f'data:image/jpeg;base64,{annotated_base64}'
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in detect_objects: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/vision/detect-cups', methods=['POST'])
def detect_cups():
    """
    Detect cups/containers in an uploaded image.
    
    Same parameters as /api/vision/detect but filters for cup-related objects.
    """
    try:
        confidence = validate_confidence(request.args.get('confidence', 0.5))
        annotate = request.args.get('annotate', 'false').lower() == 'true'
        
        # Parse image from request
        image, error = parse_image_from_request(request)
        if error:
            return jsonify({'error': error}), 400
        
        detector = get_detector(confidence=confidence)
        
        # Detect cups specifically
        cup_detections = detector.detect_cups(image)
        
        response = {
            'cups': cup_detections,
            'count': len(cup_detections)
        }
        
        if annotate:
            annotated = detector.annotate_image(image, cup_detections)
            _, buffer = cv2.imencode('.jpg', annotated)
            annotated_base64 = base64.b64encode(buffer).decode('utf-8')
            response['annotated_image'] = f'data:image/jpeg;base64,{annotated_base64}'
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in detect_cups: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/vision/model-info', methods=['GET'])
def get_model_info():
    """Get information about the loaded YOLOv11 model."""
    try:
        detector = get_detector()
        return jsonify({
            'model_loaded': detector.is_loaded,
            'confidence_threshold': detector.confidence_threshold,
            'model_name': 'YOLOv11' if detector.is_loaded else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/robot/detect-objects', methods=['POST'])
def robot_detect_objects():
    """
    Endpoint for robot to send camera images and get object detection results.
    
    This is called by the robot when it needs to find objects (like cups) to perform actions.
    The robot sends an image from its camera, and the backend processes it with YOLOv11.
    
    Accepts:
    - Multipart form data with 'image' file
    - JSON with 'image' as base64 encoded string
    
    Query parameters:
    - object_type: Type of object to detect ('cup', 'all', etc., default: 'cup')
    - confidence: Confidence threshold (0.0-1.0, default: 0.5)
    - return_coordinates: Return pixel coordinates (true/false, default: true)
    """
    try:
        object_type = request.args.get('object_type', 'cup').lower()
        confidence = validate_confidence(request.args.get('confidence', 0.5))
        return_coords = request.args.get('return_coordinates', 'true').lower() == 'true'
        
        # Parse image from request
        image, error = parse_image_from_request(request)
        if error:
            return jsonify({'error': error}), 400
        
        detector = get_detector(confidence=confidence)
        
        # Detect objects based on requested type
        if object_type == 'cup':
            detections = detector.detect_cups(image)
        else:
            detections = detector.detect_objects(image)
        
        # Format response for robot
        response = {
            'detections_found': len(detections) > 0,
            'count': len(detections),
            'objects': []
        }
        
        for det in detections:
            obj_data = {
                'class_name': det['class_name'],
                'confidence': det['confidence']
            }
            
            if return_coords:
                obj_data['center'] = {
                    'x': int(det['center'][0]),
                    'y': int(det['center'][1])
                }
                obj_data['bbox'] = {
                    'x1': int(det['bbox'][0]),
                    'y1': int(det['bbox'][1]),
                    'x2': int(det['bbox'][2]),
                    'y2': int(det['bbox'][3])
                }
            
            response['objects'].append(obj_data)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in robot_detect_objects: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/robot/find-cup', methods=['POST'])
def robot_find_cup():
    """
    Simplified endpoint for robot to find a cup.
    
    Returns the center coordinates of the first cup found, or error if none found.
    This is optimized for robot control - returns simple coordinates the robot can use.
    """
    try:
        confidence = validate_confidence(request.args.get('confidence', 0.5))
        
        # Parse image from request
        image, error = parse_image_from_request(request)
        if error:
            return jsonify({'error': error}), 400
        
        detector = get_detector(confidence=confidence)
        
        # Find cups
        cup_detections = detector.detect_cups(image)
        
        if len(cup_detections) == 0:
            return jsonify({
                'found': False,
                'error': 'No cup detected in image'
            }), 404
        
        # Return the first (or most confident) cup
        best_cup = max(cup_detections, key=lambda x: x['confidence'])
        
        return jsonify({
            'found': True,
            'center': {
                'x': int(best_cup['center'][0]),
                'y': int(best_cup['center'][1])
            },
            'confidence': best_cup['confidence'],
            'bbox': {
                'x1': int(best_cup['bbox'][0]),
                'y1': int(best_cup['bbox'][1]),
                'x2': int(best_cup['bbox'][2]),
                'y2': int(best_cup['bbox'][3])
            }
        })
        
    except Exception as e:
        logger.error(f"Error in robot_find_cup: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders/archive', methods=['POST'])
def archive_order():
    """
    Persist a detailed order from the frontend experience.
    This endpoint is meant for the kiosk/web app to send structured order data
    that future backend developers can build automations on top of.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Missing JSON payload'}), 400

        required = ['order_id', 'items']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        save_order(data)
        return jsonify({'status': 'stored'}), 201
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Error archiving order: {e}", exc_info=True)
        return jsonify({'error': 'Failed to archive order'}), 500


@app.route('/api/orders/archive', methods=['GET'])
def list_archived_orders():
    """
    Return archived orders. Supports query params:
        - limit: number of records to return
    """
    try:
        limit = request.args.get('limit', type=int)
        orders = list(get_orders(limit=limit))
        return jsonify({'orders': orders})
    except Exception as e:
        logger.error(f"Error fetching archived orders: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch orders'}), 500


@app.route('/api/orders/archive/<order_id>', methods=['GET'])
def get_archived_order(order_id):
    try:
        order = get_order(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        return jsonify(order)
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch order'}), 500


@app.route('/api/receipts', methods=['POST'])
def store_receipt():
    """
    Persist a Knot receipt or any payment receipt payload.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Missing JSON payload'}), 400
        if 'receipt_id' not in data:
            return jsonify({'error': 'Missing required field: receipt_id'}), 400

        save_receipt(data)
        return jsonify({'status': 'stored'}), 201
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Error storing receipt: {e}", exc_info=True)
        return jsonify({'error': 'Failed to store receipt'}), 500


@app.route('/api/receipts', methods=['GET'])
def list_receipts():
    """
    Return stored receipts. Supports query params:
        - limit: number of records to return
        - order_id: filter receipts for a specific order
    """
    try:
        limit = request.args.get('limit', type=int)
        order_id = request.args.get('order_id')
        receipts = list(get_receipts(limit=limit, order_id=order_id))
        return jsonify({'receipts': receipts})
    except Exception as e:
        logger.error(f"Error fetching receipts: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch receipts'}), 500


@app.route('/api/pay/knot', methods=['POST'])
def pay_with_knot():
    """
    Simulate a Knot TransactionLink payment for an archived order.
    """
    try:
        data = request.json or {}
        order_id = data.get('orderId')
        amount_cents = data.get('amountCents')
        method = data.get('method')

        if method != 'knot':
            return jsonify({'error': 'Unsupported payment method'}), 400

        if not order_id or amount_cents is None:
            return jsonify({'error': 'orderId and amountCents are required'}), 400

        order = get_order(order_id)
        if order is None:
            # Create a placeholder order so downstream systems have a record
            save_order({
                'order_id': order_id,
                'status': 'pending-payment',
                'total': amount_cents / 100.0,
                'currency': 'USD',
                'items': data.get('items', []),
                'metadata': {'source': 'knot-pay-endpoint'},
            })
            order = get_order(order_id)

        tx_id = f"txn_{uuid.uuid4().hex[:16]}"

        # Simulate that the payment was initiated but awaiting settlement
        payment_status = 'PENDING'
        loyalty_delta = 0

        update_order(
            order_id,
            status='pending',
            total=amount_cents / 100.0,
            currency='USD',
            knot_tx_id=tx_id,
            payment_status=payment_status,
            loyalty_delta=loyalty_delta,
            paid=False,
            metadata_updates={
                'knot_payment': {
                    'tx_id': tx_id,
                    'amount_cents': amount_cents,
                    'captured_at': time.time(),
                }
            },
        )

        response = {
            'ok': True,
            'status': payment_status,
            'txId': tx_id,
            'loyaltyDelta': loyalty_delta,
            'orderId': order_id,
        }
        return jsonify(response), 200
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 404
    except Exception as e:
        logger.error(f"Error processing Knot payment: {e}", exc_info=True)
        return jsonify({'error': 'Failed to process payment'}), 500


if __name__ == '__main__':
    # Initialize object detection model
    logger.info("Initializing YOLOv11 object detection model...")
    try:
        detector = get_detector()
        logger.info("YOLOv11 model loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load YOLOv11 model: {e}")
        logger.warning("Object detection endpoints will not be available")
    
    # Try to connect to Arduino on startup
    logger.info("Attempting to connect to Arduino...")
    connect_to_arduino()
    
    # Start Flask server
    # Using port 5001 because 5000 is often used by macOS AirPlay Receiver
    logger.info("Starting Flask server on port 5001...")
    app.run(debug=True, host='0.0.0.0', port=5001)

