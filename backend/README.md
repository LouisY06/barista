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

The server will start on `http://localhost:5000`

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
│   ├── main.py          # Main Flask application
│   └── serial_handler.py # Advanced serial communication handler
├── requirements.txt
└── README.md
```

### Testing

Test the API using curl or a tool like Postman:

```bash
# Health check
curl http://localhost:5000/api/health

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

## Dependencies

- `flask` - Web framework
- `flask-cors` - CORS support for frontend
- `pyserial` - Serial communication with Arduino
- `python-dotenv` - Environment variable management

