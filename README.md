# Barista Robot

A complete system for an automated barista robot arm that makes drinks based on customer orders from a POS system.

## Project Overview

This repository contains three main components:

- **Firmware** - Arduino C++ code for robot arm control
- **Frontend** - React application for the Point of Sale (POS) system
- **Backend** - Python server handling orders and serial communication

## Architecture

```
┌─────────────┐         HTTP/REST         ┌─────────────┐
│   Frontend  │ ────────────────────────> │   Backend   │
│   (React)   │ <──────────────────────── │  (Python)   │
└─────────────┘                           └─────────────┘
                                                    │
                                                    │ Serial USB
                                                    ▼
                                           ┌─────────────┐
                                           │  Firmware   │
                                           │  (Arduino)  │
                                           └─────────────┘
```

### Communication Flow

1. Customer places order via Frontend (React POS)
2. Frontend sends order to Backend via REST API
3. Backend processes order and sends commands to Firmware via Serial USB
4. Firmware controls robot arm to make the drink
5. Status updates flow back: Firmware → Backend → Frontend

## Quick Start

### Prerequisites

- Node.js 14+ (for frontend)
- Python 3.8+ (for backend)
- Arduino IDE or PlatformIO (for firmware)
- Arduino board with USB connection

### Setup

1. **Firmware Setup**

```bash
cd firmware
# Open src/main.ino in Arduino IDE
# Upload to your Arduino board
```

See [firmware/README.md](firmware/README.md) for detailed instructions.

2. **Backend Setup**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

See [backend/README.md](backend/README.md) for detailed instructions.

3. **Frontend Setup**

```bash
cd frontend
npm install
npm start
```

See [frontend/README.md](frontend/README.md) for detailed instructions.

## Repository Structure

```
barista/
├── firmware/          # Arduino C++ firmware
│   ├── src/
│   │   └── main.ino   # Main Arduino sketch
│   └── README.md
├── backend/           # Python backend server
│   ├── app/
│   │   ├── main.py    # Flask application
│   │   └── serial_handler.py
│   ├── requirements.txt
│   └── README.md
├── frontend/          # React POS application
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.js
│   └── README.md
└── README.md          # This file
```

## Features

- **POS Interface**: User-friendly React interface for placing drink orders
- **Order Management**: Real-time order tracking and status updates
- **Robot Control**: Serial communication between backend and Arduino
- **Status Monitoring**: Live robot arm status and connection monitoring
- **RESTful API**: Clean API for order processing and robot control

## Development

Each component has its own README with specific setup and development instructions:

- [Firmware Documentation](firmware/README.md)
- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)

## API Endpoints

The backend provides the following REST API endpoints:

- `GET /api/health` - Health check
- `POST /api/orders` - Create new order
- `GET /api/orders/<id>/status` - Get order status
- `GET /api/robot/status` - Get robot status
- `POST /api/robot/reset` - Reset robot arm
- `POST /api/robot/connect` - Connect to robot arm

## Serial Communication Protocol

The firmware and backend communicate via Serial USB at 9600 baud:

**Commands (Backend → Firmware):**
- `ORDER:<drink_type>:<size>:<options>`
- `STATUS`
- `RESET`

**Responses (Firmware → Backend):**
- `READY`
- `STATUS:<state>`
- `ORDER_COMPLETE`
- `RESET_COMPLETE`

## Contributing

1. Create a feature branch
2. Make your changes
3. Test all three components
4. Submit a pull request

## License

[Add your license here]

## Troubleshooting

### Backend can't find Arduino
- Check USB connection
- Verify Arduino is powered on
- Try manually specifying port via `/api/robot/connect` endpoint
- On Linux, ensure user is in `dialout` group

### Frontend can't connect to backend
- Ensure backend is running on port 5000
- Check CORS settings in backend
- Verify `REACT_APP_API_URL` environment variable

### Firmware not responding
- Check serial monitor for error messages
- Verify baud rate matches (9600)
- Ensure commands end with newline character
- Check hardware connections
