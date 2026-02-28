import React, { useState } from 'react';
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
    startSimulation,
    stopSimulation,
    resetSimulation,
    toggleCooperation,
    grantClearance,
    customAddVehicle,
    customRemoveVehicle,
    customUpdateVehicle,
    customClear,
  } = useSimulation('ws://localhost:8000/ws');

  const [currentScenario, setCurrentScenario] = useState('perpendicular');

  // Date live din backend
  const vehicles = wsState?.vehicles || [];
  const events = wsState?.event_log || [];
  const semaphore = wsState?.semaphore || {};
  const risk = wsState?.risk || { risk: false, pair: null, ttc: 999, ttc_per_vehicle: {} };
  const customScenario = wsState?.custom_scenario || [];
  const liveCooperation = wsState?.cooperation ?? true;
  const livePaused = wsState?.paused ?? false;
  const agentsMemory = wsState?.agents_memory ?? {};

  const handleToggleCooperation = async () => { await toggleCooperation(); };

  const handleScenarioChange = async (id) => {
    setCurrentScenario(id);
    await resetSimulation(id);
  };

  const handleReset = () => resetSimulation(currentScenario);

  return (
    <div className="app">
      {/* Header */}
      {/* Main Layout */}
      <div className="app-layout">
        {/* Left Panel - Control Panel */}
        <aside className="left-panel">
          <ControlPanel
            cooperation={liveCooperation}
            paused={livePaused}
            currentScenario={currentScenario}
            customScenario={customScenario}
            onToggleCooperation={handleToggleCooperation}
            onScenarioChange={handleScenarioChange}
            onReset={handleReset}
            onStart={startSimulation}
            onStop={stopSimulation}
            onCustomAdd={customAddVehicle}
            onCustomRemove={customRemoveVehicle}
            onCustomUpdate={customUpdateVehicle}
            onCustomClear={customClear}
          />
        </aside>

        {/* Center - Canvas */}
        <main className="main-content">
          <IntersectionCanvas
            vehicles={vehicles}
            semaphore={semaphore}
            risk={risk}
            agentsMemory={agentsMemory}
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
        <EventLog agentsMemory={agentsMemory} />
      </footer>
    </div>
  );
}

export default App;

