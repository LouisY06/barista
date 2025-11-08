import React, { useState } from 'react';
import OrderForm from './components/OrderForm';
import OrderList from './components/OrderList';
import RobotStatus from './components/RobotStatus';
import './App.css';

function App() {
  const [orders, setOrders] = useState([]);

  const handleOrderCreated = (newOrder) => {
    setOrders((prevOrders) => [newOrder, ...prevOrders]);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Barista Robot POS System</h1>
      </header>
      <main className="App-main">
        <div className="content-grid">
          <div className="left-column">
            <OrderForm onOrderCreated={handleOrderCreated} />
            <RobotStatus />
          </div>
          <div className="right-column">
            <OrderList orders={orders} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
