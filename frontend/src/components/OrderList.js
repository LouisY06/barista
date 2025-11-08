import React, { useEffect, useState } from 'react';
import { getOrderStatus } from '../services/api';
import './OrderList.css';

function OrderList({ orders, onStatusUpdate }) {
  const [statuses, setStatuses] = useState({});

  useEffect(() => {
    // Poll for order status updates
    const interval = setInterval(async () => {
      for (const order of orders) {
        try {
          const status = await getOrderStatus(order.id);
          setStatuses((prev) => ({
            ...prev,
            [order.id]: status.status,
          }));
        } catch (error) {
          console.error(`Error getting status for order ${order.id}:`, error);
        }
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [orders]);

  if (orders.length === 0) {
    return (
      <div className="order-list">
        <h2>Recent Orders</h2>
        <p className="no-orders">No orders yet</p>
      </div>
    );
  }

  return (
    <div className="order-list">
      <h2>Recent Orders</h2>
      <div className="orders-container">
        {orders.map((order) => (
          <div key={order.id} className="order-item">
            <div className="order-header">
              <span className="order-id">Order #{order.id}</span>
              <span className={`order-status ${statuses[order.id]?.toLowerCase() || order.status}`}>
                {statuses[order.id] || order.status}
              </span>
            </div>
            <div className="order-details">
              <div className="order-detail">
                <strong>Drink:</strong> {order.drink_type}
              </div>
              <div className="order-detail">
                <strong>Size:</strong> {order.size}
              </div>
              {order.options && order.options !== 'NONE' && (
                <div className="order-detail">
                  <strong>Options:</strong> {order.options}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default OrderList;

