# Barista Robot POS Frontend

React application for the Point of Sale (POS) system that allows customers to place drink orders.

## Requirements

- Node.js 14 or higher
- npm or yarn

## Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Configure API endpoint (optional):

Create a `.env` file in the `frontend/` directory:

```
REACT_APP_API_URL=http://localhost:5000/api
```

If not set, defaults to `http://localhost:5000/api`

## Running the Application

Start the development server:

```bash
npm start
```

The application will open at `http://localhost:3000`

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Project Structure

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── OrderForm.js      # Order creation form
│   │   ├── OrderForm.css
│   │   ├── OrderList.js      # List of recent orders
│   │   ├── OrderList.css
│   │   ├── RobotStatus.js    # Robot arm status display
│   │   └── RobotStatus.css
│   ├── services/
│   │   └── api.js            # API client for backend communication
│   ├── App.js                # Main application component
│   ├── App.css
│   └── index.js
├── package.json
└── README.md
```

## Features

- **Order Form**: Create new drink orders with type, size, and options
- **Order List**: View recent orders with real-time status updates
- **Robot Status**: Monitor robot arm connection and status
- **Real-time Updates**: Automatic polling for order and robot status

## Available Drink Types

- ESPRESSO
- CAPPUCCINO
- LATTE
- AMERICANO
- MOCHA
- MACCHIATO

## Available Sizes

- SMALL
- MEDIUM
- LARGE

## API Integration

The frontend communicates with the backend via REST API. See `src/services/api.js` for available API functions:

- `createOrder(order)` - Create a new order
- `getOrderStatus(orderId)` - Get order status
- `getRobotStatus()` - Get robot arm status
- `resetRobot()` - Reset robot arm
- `checkHealth()` - Check backend health

## Development

### Adding New Components

Components are located in `src/components/`. Each component has its own CSS file.

### Modifying API Calls

Update `src/services/api.js` to add or modify API endpoints.

### Styling

- Component-specific styles in `src/components/*.css`
- Global styles in `src/App.css`

## Testing

Run tests:

```bash
npm test
```

## Troubleshooting

- **API connection errors**: Ensure backend server is running on port 5000
- **CORS errors**: Check that backend has CORS enabled
- **Build errors**: Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
