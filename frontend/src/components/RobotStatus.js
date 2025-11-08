import React, { useState, useEffect } from 'react';
import { getRobotStatus, resetRobot } from '../services/api';
import './RobotStatus.css';

function RobotStatus() {
  const [status, setStatus] = useState('unknown');
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      const data = await getRobotStatus();
      setStatus(data.status || 'unknown');
      setConnected(data.connected || false);
      setError(null);
    } catch (err) {
      setError('Failed to get robot status');
      setConnected(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000); // Update every 3 seconds
    return () => clearInterval(interval);
  }, []);

  const handleReset = async () => {
    setLoading(true);
    setError(null);
    try {
      await resetRobot();
      await fetchStatus();
    } catch (err) {
      setError('Failed to reset robot');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = () => {
    switch (status.toLowerCase()) {
      case 'idle':
        return '#4caf50';
      case 'making_drink':
      case 'processing_order':
        return '#ff9800';
      case 'error':
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  return (
    <div className="robot-status">
      <h2>Robot Arm Status</h2>
      <div className="status-container">
        <div className="status-indicator">
          <div
            className="status-dot"
            style={{ backgroundColor: getStatusColor() }}
          />
          <span className="status-text">{status.toUpperCase()}</span>
        </div>
        <div className="connection-status">
          <span className={connected ? 'connected' : 'disconnected'}>
            {connected ? '● Connected' : '○ Disconnected'}
          </span>
        </div>
      </div>
      {error && <div className="error-message">{error}</div>}
      <button
        onClick={handleReset}
        disabled={loading || !connected}
        className="reset-button"
      >
        {loading ? 'Resetting...' : 'Reset Robot'}
      </button>
    </div>
  );
}

export default RobotStatus;

