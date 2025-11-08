# Barista Robot Backend

Python backend server that handles order processing and communicates with the robot arm via Serial USB.

## Requirements

- Python 3.8 or higher
- pip (Python package manager)
- USB connection to Arduino

## Setup

1. Create a virtual environment (recommended):

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure serial port (optional):

The backend will attempt to auto-detect the Arduino port. If you need to specify a port manually, you can:

- Set environment variable: `ARDUINO_PORT=/dev/ttyUSB0` (Linux) or `ARDUINO_PORT=COM3` (Windows)
- Or use the `/api/robot/connect` endpoint with a POST request containing `{"port": "/dev/ttyUSB0"}`

## Running the Server

```bash
python -m app.main
```

The server will start on `http://localhost:5001` (port 5000 is often used by macOS AirPlay Receiver)

## Testing Object Detection with Your Laptop Camera

You can test the object detection system using your laptop camera:

```bash
# Make sure backend is running first, then:
python test_camera_detection.py
```

This script will:
- Open your laptop camera
- Send frames to the backend for YOLOv11 detection
- Display results in real-time with bounding boxes
- Press 'q' to quit, 'c' for cup detection, 'a' for all objects, '+/-' to adjust confidence

## API Endpoints

### Health Check

- `GET /api/health` - Check server and Arduino connection status

### Orders

- `POST /api/orders` - Create a new drink order
  - Request body:
    ```json
    {
      "drink_type": "ESPRESSO",
      "size": "MEDIUM",
      "options": "NONE"
    }
    ```
  - Response: Order object with ID and status

- `GET /api/orders/<order_id>/status` - Get status of an order

### Robot Control

- `GET /api/robot/status` - Get current robot arm status
- `POST /api/robot/reset` - Reset robot arm to idle state
- `POST /api/robot/connect` - Manually connect to robot arm
  - Request body (optional):
    ```json
    {
      "port": "/dev/ttyUSB0"
    }
    ```

### Vision/Object Detection (YOLOv11)

**Robot CV Endpoints** (for robot-to-backend communication):

- `POST /api/robot/find-cup` - **Simplified endpoint for robots to find a cup**
  - Accepts: Image file or base64 encoded image
  - Query parameters:
    - `confidence` (float, default: 0.5) - Confidence threshold
  - Response:
    ```json
    {
      "found": true,
      "center": {"x": 320, "y": 240},
      "confidence": 0.95,
      "bbox": {"x1": 100, "y1": 50, "x2": 200, "y2": 150}
    }
    ```
  - Returns 404 if no cup found

- `POST /api/robot/detect-objects` - **General object detection for robots**
  - Accepts: Image file or base64 encoded image
  - Query parameters:
    - `object_type` (string, default: 'cup') - Type of object ('cup', 'all')
    - `confidence` (float, default: 0.5) - Confidence threshold
    - `return_coordinates` (bool, default: true) - Include pixel coordinates
  - Response:
    ```json
    {
      "detections_found": true,
      "count": 1,
      "objects": [
        {
          "class_name": "cup",
          "confidence": 0.95,
          "center": {"x": 320, "y": 240},
          "bbox": {"x1": 100, "y1": 50, "x2": 200, "y2": 150}
        }
      ]
    }
    ```

**General Vision Endpoints**:

- `POST /api/vision/detect` - Detect objects in an image
  - Accepts: Multipart form data with 'image' file OR JSON with base64 encoded image
  - Query parameters:
    - `confidence` (float, 0.0-1.0, default: 0.5) - Confidence threshold
    - `annotate` (bool, default: false) - Return annotated image with bounding boxes
  - Response:
    ```json
    {
      "detections": [
        {
          "class_id": 41,
          "class_name": "cup",
          "confidence": 0.95,
          "bbox": [x1, y1, x2, y2],
          "center": [x, y]
        }
      ],
      "count": 1,
      "annotated_image": "data:image/jpeg;base64,..." // if annotate=true
    }
    ```

- `POST /api/vision/detect-cups` - Detect cups/containers specifically
  - Same parameters as `/api/vision/detect` but filters for cup-related objects
  - Response:
    ```json
    {
      "cups": [...],
      "count": 1,
      "annotated_image": "..." // if annotate=true
    }
    ```

- `GET /api/vision/model-info` - Get information about loaded YOLOv11 model
  - Response:
    ```json
    {
      "model_loaded": true,
      "confidence_threshold": 0.5,
      "model_name": "YOLOv11"
    }
    ```

## Configuration

### Serial Communication

- Baud rate: 9600 (configurable in `app/main.py`)
- Timeout: 1 second

### Environment Variables

Create a `.env` file in the `backend/` directory:

```
ARDUINO_PORT=/dev/ttyUSB0  # Optional: specify Arduino port
FLASK_ENV=development       # Optional: Flask environment
```

## Development

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main Flask application
│   ├── serial_handler.py    # Advanced serial communication handler
│   └── object_detection.py  # YOLOv11 object detection module
├── uploads/                 # Temporary image uploads (created automatically)
├── requirements.txt
└── README.md
```

### Testing

Test the API using curl or a tool like Postman:

```bash
# Health check
curl http://localhost:5001/api/health

# Create order
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"drink_type": "ESPRESSO", "size": "MEDIUM", "options": "NONE"}'

# Get robot status
curl http://localhost:5000/api/robot/status
```

## Troubleshooting

- **Arduino not found**: Check USB connection and try manually specifying the port
- **Serial communication errors**: Ensure Arduino is powered and firmware is uploaded
- **Port permission errors (Linux)**: Add user to dialout group: `sudo usermod -a -G dialout $USER`

## Object Detection with YOLOv11

The backend includes YOLOv11 (the latest and most powerful YOLO model) for object detection. This can be used for:

- **Cup/Container Detection**: Locate cups on the workspace before placing drinks
- **Ingredient Detection**: Identify ingredients and containers
- **Quality Control**: Verify drink placement and appearance
- **Workspace Monitoring**: Monitor the robot's working area

### Model Options

By default, the system uses YOLOv11n (nano) for fast inference. For better accuracy on a powerful machine, you can modify `app/object_detection.py` to use:

- `yolo11n.pt` - Nano (fastest, smallest)
- `yolo11s.pt` - Small
- `yolo11m.pt` - Medium
- `yolo11l.pt` - Large
- `yolo11x.pt` - Extra Large (most accurate, slowest)

### Custom Models

You can train a custom YOLOv11 model for your specific use case (e.g., detecting specific cup types, ingredients) and load it by setting the `model_path` parameter when initializing the detector.

### Usage Examples

**Robot finding a cup (most common use case):**
```bash
# Robot sends image from camera
curl -X POST http://localhost:5000/api/robot/find-cup?confidence=0.6 \
  -F "image=@camera_capture.jpg"

# Response: {"found": true, "center": {"x": 320, "y": 240}, ...}
# Robot uses center coordinates to move arm to cup position
```

**Robot detecting multiple objects:**
```bash
curl -X POST http://localhost:5000/api/robot/detect-objects?object_type=all \
  -F "image=@workspace_image.jpg"
```

**General object detection:**
```bash
curl -X POST http://localhost:5000/api/vision/detect?confidence=0.6&annotate=true \
  -F "image=@path/to/image.jpg"
```

**Using Python helper (for robots with Python):**
```python
from app.robot_cv_helper import RobotCVClient

client = RobotCVClient(backend_url="http://localhost:5000")
result = client.find_cup(image_path="camera_image.jpg")
if result['found']:
    x, y = result['center']['x'], result['center']['y']
    move_robot_arm(x, y)
```

## Dependencies

- `flask` - Web framework
- `flask-cors` - CORS support for frontend
- `pyserial` - Serial communication with Arduino
- `python-dotenv` - Environment variable management
- `ultralytics` - YOLOv11 object detection
- `opencv-python` - Image processing
- `numpy` - Numerical operations
- `pillow` - Image handling

