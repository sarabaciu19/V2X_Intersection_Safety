import React, { useState, useEffect } from 'react';
import IntersectionCanvas from './components/IntersectionCanvas';
import Dashboard from './components/Dashboard';
import ControlPanel from './components/ControlPanel';
import EventLog from './components/EventLog';
import useSimulation from './hooks/useSimulation';
import './App.css';

/**
 * App.jsx - Layout principal al aplicației V2X Intersection Safety
 * Integrează toate componentele și gestionează starea globală
 * Conectează frontend cu backend prin WebSocket
 */
function App() {
  const {
    state: wsState,
    isConnected,
    error,
    resetSimulation,
    toggleCooperation,
    grantClearance,
  } = useSimulation('ws://localhost:8000/ws');

  const [currentScenario, setCurrentScenario] = useState('perpendicular');
  const [cooperation,     setCooperation]     = useState(true);

  // Date live din backend
  const vehicles   = wsState?.vehicles   || [];
  const events     = wsState?.events     || [];
  const semaphore  = wsState?.semaphore  || {};
  const liveCooperation = wsState?.cooperation ?? cooperation;

  const handleToggleCooperation = async () => {
    const result = await toggleCooperation();
    if (result) setCooperation(result.cooperation);
  };

  const handleScenarioChange = async (scenarioId) => {
    setCurrentScenario(scenarioId);
    await resetSimulation(scenarioId);
  };

  const handleReset = async () => {
    await resetSimulation(currentScenario);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <h1>🚗 V2X Intersection Safety</h1>
        <div className="connection-status">
          {isConnected
            ? <span className="status-badge status-connected">🟢 Live Backend</span>
            : <span className="status-badge status-disconnected">🔴 Reconectare…</span>
          }
          {error && <span style={{ color: '#F87171', fontSize: 12, marginLeft: 8 }}>{error}</span>}
        </div>
      </header>

      {/* Main Layout */}
      <div className="app-layout">
        {/* Left Panel - Control Panel */}
        <aside className="left-panel">
          <ControlPanel
            cooperation={liveCooperation}
            currentScenario={currentScenario}
            onToggleCooperation={handleToggleCooperation}
            onScenarioChange={handleScenarioChange}
            onReset={handleReset}
          />
        </aside>

        {/* Center - Canvas */}
        <main className="main-content">
          <IntersectionCanvas
            vehicles={vehicles}
            semaphore={semaphore}
            cooperation={liveCooperation}
            onGrantClearance={!liveCooperation ? grantClearance : null}
            dimensions={{ width: 800, height: 800 }}
          />
        </main>

        {/* Right Panel - Dashboard */}
        <aside className="right-panel">
          <Dashboard
            vehicles={vehicles}
            semaphore={semaphore}
            cooperation={liveCooperation}
            onGrantClearance={!liveCooperation ? grantClearance : null}
          />
        </aside>
      </div>

      {/* Bottom - Event Log */}
      <footer className="app-footer">
        <EventLog events={events} maxEvents={50} />
      </footer>
    </div>
  );
}

export default App;

