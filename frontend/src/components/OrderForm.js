import React, { useState } from 'react';
import { createOrder } from '../services/api';
import './OrderForm.css';

const DRINK_TYPES = [
  'ESPRESSO',
  'CAPPUCCINO',
  'LATTE',
  'AMERICANO',
  'MOCHA',
  'MACCHIATO',
];

const SIZES = ['SMALL', 'MEDIUM', 'LARGE'];

function OrderForm({ onOrderCreated }) {
  const [drinkType, setDrinkType] = useState('ESPRESSO');
  const [size, setSize] = useState('MEDIUM');
  const [options, setOptions] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const order = {
        drink_type: drinkType,
        size: size,
        options: options || 'NONE',
      };

      const result = await createOrder(order);
      onOrderCreated(result);
      
      // Reset form
      setOptions('');
    } catch (err) {
      setError(err.message || 'Failed to create order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="order-form">
      <h2>New Order</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="drink-type">Drink Type:</label>
          <select
            id="drink-type"
            value={drinkType}
            onChange={(e) => setDrinkType(e.target.value)}
            required
          >
            {DRINK_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="size">Size:</label>
          <select
            id="size"
            value={size}
            onChange={(e) => setSize(e.target.value)}
            required
          >
            {SIZES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="options">Options (optional):</label>
          <input
            id="options"
            type="text"
            value={options}
            onChange={(e) => setOptions(e.target.value)}
            placeholder="e.g., extra shot, decaf, etc."
          />
        </div>

        {error && <div className="error-message">{error}</div>}

        <button type="submit" disabled={loading} className="submit-button">
          {loading ? 'Processing...' : 'Place Order'}
        </button>
      </form>
    </div>
  );
}

export default OrderForm;

