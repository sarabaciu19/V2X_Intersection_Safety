import React, { useState, useEffect } from 'react';
import IntersectionCanvas from './components/IntersectionCanvas';
import Dashboard from './components/Dashboard';
import ControlPanel from './components/ControlPanel';
import EventLog from './components/EventLog';
import useSimulation from './hooks/useSimulation';
import { mockVehicles, mockEvents, mockSystemStatus, createMockSimulation, FAKE_STATE, SCENARIOS } from './data/fakeData';
import './App.css';

/**
 * App.jsx - Layout principal al aplicației V2X Intersection Safety
 * Integrează toate componentele și gestionează starea globală
 * Conectează frontend cu backend prin WebSocket
 */
function App() {
  // WebSocket hook - cu fallback automat la FAKE_STATE
  const {
    state: wsState,
    isConnected,
    error,
    resetSimulation,
    toggleCooperation,
  } = useSimulation('ws://localhost:8000/ws');

  // Când backend-ul se conectează → trece automat pe date live
  const [useMockData, setUseMockData] = useState(true);
  useEffect(() => {
    if (isConnected) setUseMockData(false);
    else             setUseMockData(true);
  }, [isConnected]);

  // State local pentru date mock
  const [mockState, setMockState] = useState({
    vehicles:     mockVehicles,
    events:       mockEvents,
    systemStatus: mockSystemStatus,
    risk:         { danger: false, ttc: 5.0 },
    cooperation:  true,
  });

  const [isRunning,        setIsRunning]        = useState(false);
  const [currentScenario,  setCurrentScenario]  = useState('normal');
  const [cooperation,      setCooperation]      = useState(true);

  // Sursa de date — mock sau WebSocket
  const vehicles     = useMockData ? mockState.vehicles     : (wsState?.vehicles  || []);
  const events       = useMockData ? mockState.events       : (wsState?.events    || []);
  const systemStatus = useMockData ? mockState.systemStatus : (wsState?.systemStatus || {});
  const risk         = useMockData ? mockState.risk         : (wsState?.risk       || { danger: false, ttc: 5.0 });

  // Cooperation vine din backend când e conectat
  const liveCooperation = useMockData ? cooperation : (wsState?.cooperation ?? cooperation);

  // Handler pentru start/stop simulare
  const handleStart = () => {
    if (!useMockData) { setIsRunning(true); return; }
    setIsRunning(true);
    const cleanup = createMockSimulation(
      (data) => setMockState({ ...data, cooperation }),
      500,
      currentScenario,
    );
    window.mockSimulationCleanup = cleanup;
  };

  const handleStop = () => {
    setIsRunning(false);
    if (window.mockSimulationCleanup) {
      window.mockSimulationCleanup();
      window.mockSimulationCleanup = null;
    }
  };

  const handleReset = () => {
    if (useMockData) {
      handleStop();
      setMockState({
        vehicles:     mockVehicles,
        events:       mockEvents,
        systemStatus: { ...mockSystemStatus, running: false },
        risk:         { danger: false, ttc: 5.0 },
        cooperation,
      });
    } else {
      resetSimulation().then(() => setIsRunning(false));
    }
  };

  const handleScenarioChange = (scenarioId) => {
    setCurrentScenario(scenarioId);
    if (useMockData) {
      if (window.mockSimulationCleanup) window.mockSimulationCleanup();
      if (isRunning) {
        const cleanup = createMockSimulation(
          (data) => setMockState({ ...data, cooperation }),
          500,
          scenarioId,
        );
        window.mockSimulationCleanup = cleanup;
      }
    } else {
      // Map frontend scenario id → backend scenario name
      const backendMap = {
        normal:              'perpendicular',
        collision_imminent:  'perpendicular',
        emergency_vehicle:   'emergency',
        speed_diff:          'speed_diff',
        high_traffic:        'perpendicular',
      };
      resetSimulation(backendMap[scenarioId] || scenarioId);
    }
  };

  // TOGGLE COOPERATION - APELEAZĂ BACKEND
  const handleToggleCooperation = async () => {
    if (useMockData) {
      const next = !cooperation;
      setCooperation(next);
      setMockState(prev => ({ ...prev, cooperation: next }));
    } else {
      await toggleCooperation();
    }
  };

  // RESET SCENARIO - Resetează pozițiile mașinilor
  const handleResetScenario = async () => {
    if (useMockData) {
      handleStop();
      const scenarioData = SCENARIOS[currentScenario] || SCENARIOS.normal;
      setMockState({
        vehicles: scenarioData.vehicles.map(v => ({
          ...v,
          speed:   Math.sqrt((v.vx || 0) ** 2 + (v.vy || 0) ** 2) * 10,
          heading: Math.atan2(v.vy || 0, v.vx || 0),
          status:  v.state,
        })),
        events:       [],
        systemStatus: { ...mockSystemStatus, running: false },
        risk:         scenarioData.risk || { danger: false, ttc: 5.0 },
        cooperation,
      });
    } else {
      const backendMap = {
        normal:             'perpendicular',
        collision_imminent: 'perpendicular',
        emergency_vehicle:  'emergency',
        speed_diff:         'speed_diff',
        high_traffic:       'perpendicular',
      };
      await resetSimulation(backendMap[currentScenario] || currentScenario);
      setIsRunning(false);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <h1>🚗 V2X Intersection Safety System</h1>
        <div className="connection-status">
          {useMockData ? (
            <span className="status-badge status-mock">📊 Mock Data</span>
          ) : isConnected ? (
            <span className="status-badge status-connected">🟢 Live (Backend)</span>
          ) : (
            <span className="status-badge status-disconnected">🔴 Reconnecting…</span>
          )}
          <button className="toggle-mode-btn" onClick={() => setUseMockData(v => !v)}>
            {useMockData ? 'Switch to WebSocket' : 'Switch to Mock'}
          </button>
        </div>
      </header>

      {/* Error banner */}
      {error && !useMockData && (
        <div className="error-banner">⚠️ {error}</div>
      )}

      {/* Main Layout */}
      <div className="app-layout">
        {/* Left Panel - Control Panel */}
        <aside className="left-panel">
          <ControlPanel
            isRunning={isRunning || !!systemStatus?.running}
            cooperation={liveCooperation}
            currentScenario={currentScenario}
            onStart={handleStart}
            onStop={handleStop}
            onReset={handleReset}
            onToggleCooperation={handleToggleCooperation}
            onScenarioChange={handleScenarioChange}
            onResetScenario={handleResetScenario}
          />
        </aside>

        {/* Center - Canvas */}
        <main className="main-content">
          <IntersectionCanvas
            vehicles={vehicles}
            risk={risk}
            dimensions={{ width: 800, height: 800 }}
          />
        </main>

        {/* Right Panel - Dashboard */}
        <aside className="right-panel">
          <Dashboard
            vehicles={vehicles}
            systemStatus={{
              ...systemStatus,
              running:     isRunning || !!systemStatus?.running,
              cooperation: liveCooperation,
            }}
            risk={risk}
          />
        </aside>
      </div>

      {/* Bottom - Event Log */}
      <footer className="app-footer">
        <EventLog events={events} maxEvents={100} />
      </footer>
    </div>
  );
}

export default App;

