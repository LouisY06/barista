/**
 * API client for communicating with the backend server
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

/**
 * Create a new drink order
 * @param {Object} order - Order object with drink_type, size, and optional options
 * @returns {Promise<Object>} Created order response
 */
export const createOrder = async (order) => {
  try {
    const response = await fetch(`${API_BASE_URL}/orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(order),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create order');
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating order:', error);
    throw error;
  }
};

/**
 * Get status of an order
 * @param {number} orderId - Order ID
 * @returns {Promise<Object>} Order status
 */
export const getOrderStatus = async (orderId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/orders/${orderId}/status`);
    
    if (!response.ok) {
      throw new Error('Failed to get order status');
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting order status:', error);
    throw error;
  }
};

/**
 * Get robot arm status
 * @returns {Promise<Object>} Robot status
 */
export const getRobotStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/robot/status`);
    
    if (!response.ok) {
      throw new Error('Failed to get robot status');
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting robot status:', error);
    throw error;
  }
};

/**
 * Reset robot arm
 * @returns {Promise<Object>} Reset response
 */
export const resetRobot = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/robot/reset`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error('Failed to reset robot');
    }

    return await response.json();
  } catch (error) {
    console.error('Error resetting robot:', error);
    throw error;
  }
};

/**
 * Check backend health
 * @returns {Promise<Object>} Health status
 */
export const checkHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return await response.json();
  } catch (error) {
    console.error('Error checking health:', error);
    throw error;
  }
};

