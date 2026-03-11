import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [running, setRunning] = useState(false);
  const [fingerCount, setFingerCount] = useState(0);
  const [currentColor, setCurrentColor] = useState('green');
  const [currentMode, setCurrentMode] = useState('idle');
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);

  // Fetch hand tracking data from backend
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('http://localhost:5000/api/hand-data');
        const data = await response.json();
        
        setFingerCount(data.finger_count || 0);
        setCurrentColor(data.current_color || 'green');
        setCurrentMode(data.current_mode || 'idle');
        setIsConnected(true);
        setError(null);
      } catch (err) {
        console.error('Error fetching hand data:', err);
        setError('Failed to connect to hand tracking');
        setIsConnected(false);
      }
    }, 100); // Update every 100ms

    return () => clearInterval(interval);
  }, []);

  const startCamera = () => {
    setRunning(true);
  };

  const stopCamera = () => {
    setRunning(false);
  };

  const clearCanvas = async () => {
    try {
      await fetch('http://localhost:5000/clear', { method: 'POST' });
    } catch (err) {
      console.error('Error clearing canvas:', err);
    }
  };

  // Get mode color
  const getModeColor = () => {
    switch (currentMode) {
      case 'drawing':
        return '#4CAF50'; // Green
      case 'erasing':
        return '#F44336'; // Red
      case 'color-change':
        return '#2196F3'; // Blue
      default:
        return '#9E9E9E'; // Gray
    }
  };

  // Get actual color for display
  const getActualColor = () => {
    switch (currentColor) {
      case 'green':
        return '#4CAF50';
      case 'white':
        return '#FFFFFF';
      case 'light blue':
        return '#42A5F5'; // More vibrant blue
      case 'vibrant blue':
        return '#2196F3'; // True vibrant blue
      default:
        return '#9E9E9E';
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Hand Tracking Drawing</h1>
        <div className="status-indicators">
          <div className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="info-panel">
          <div className="info-card">
            <h2>Status</h2>
            <div className="status-item">
              <span className="label">Finger Count:</span>
              <span className="value">{fingerCount}</span>
            </div>
            <div className="status-item">
              <span className="label">Current Color:</span>
              <span className="value" style={{ color: getActualColor() }}>
                {currentColor}
              </span>
              <div 
                className="color-preview" 
                style={{ 
                  backgroundColor: getActualColor(),
                  width: '20px',
                  height: '20px',
                  borderRadius: '4px',
                  border: '1px solid #ddd',
                  marginLeft: '8px',
                  display: 'inline-block',
                  verticalAlign: 'middle'
                }}
              />
            </div>
            <div className="status-item">
              <span className="label">Current Mode:</span>
              <span className={`value mode-${currentMode}`} style={{ color: getModeColor() }}>
                {currentMode.replace('-', ' ').toUpperCase()}
              </span>
            </div>
          </div>

          <div className="info-card">
            <h2>Controls</h2>
            <div className="controls">
              <div className="control-item">
                <span>1 Finger</span>
                <span className="control-desc">Draw</span>
              </div>
              <div className="control-item">
                <span>2-4 Fingers</span>
                <span className="control-desc">Change Color</span>
              </div>
              <div className="control-item">
                <span>5 Fingers</span>
                <span className="control-desc">Erase</span>
              </div>
            </div>
          </div>
        </div>

        <div className="canvas-container">
          <div className="canvas-wrapper">
            <div className="camera-controls">
              <button onClick={startCamera} disabled={running}>
                Start Camera
              </button>
              <button onClick={stopCamera} disabled={!running}>
                Stop Camera
              </button>
              <button onClick={clearCanvas}>
                Clear Canvas
              </button>
            </div>
            {running ? (
              <img
                src="http://localhost:5000/video_feed"
                alt="camera"
                className="video"
              />
            ) : (
              <div className="placeholder">Camera Stopped</div>
            )}
          </div>
        </div>
      </main>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

export default App;
