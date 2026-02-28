import React, { useState } from 'react';
import IntersectionCanvas from './components/IntersectionCanvas';
import Dashboard from './components/Dashboard';
import ControlPanel from './components/ControlPanel';
import EventLog from './components/EventLog';
import useSimulation from './hooks/useSimulation';
import { mockVehicles, mockEvents, mockSystemStatus, createMockSimulation, FAKE_STATE } from './data/fakeData';
import './App.css';

/**
 * App.jsx - Layout principal al aplicației V2X Intersection Safety
 * Integrează toate componentele și gestionează starea globală
 */
function App() {
  // Opțiune pentru a folosi date mock sau WebSocket
  const [useMockData, setUseMockData] = useState(true);

  // WebSocket hook - cu fallback automat la FAKE_STATE
  const { state: wsState, isConnected, error } = useSimulation('ws://localhost:8000/ws');

  // State local pentru date mock
  const [mockState, setMockState] = useState({
    vehicles: mockVehicles,
    events: mockEvents,
    systemStatus: mockSystemStatus,
    risk: { danger: false, ttc: 5.0 },
    cooperation: true, // Adaugă cooperation
  });

  const [isRunning, setIsRunning] = useState(false);
  const [currentScenario, setCurrentScenario] = useState('normal');
  const [cooperation, setCooperation] = useState(true); // State pentru cooperation

  // Selectează sursa de date
  const vehicles = useMockData ? mockState.vehicles : (wsState.vehicles || []);
  const events = useMockData ? mockState.events : [];
  const systemStatus = useMockData ? mockState.systemStatus : {};
  const risk = useMockData ? mockState.risk : (wsState.risk || { danger: false, ttc: 5.0 });

  // Handler pentru start/stop simulare
  const handleStart = () => {
    if (useMockData) {
      setIsRunning(true);
      // Pornește simularea mock
      const cleanup = createMockSimulation((data) => {
        setMockState({
          ...data,
          cooperation: cooperation,
        });
      }, 500, currentScenario);

      // Salvează cleanup pentru stop
      window.mockSimulationCleanup = cleanup;
    } else {
      // Pentru WebSocket, doar setează running
      // Backend-ul va trimite date automat
      setIsRunning(true);
    }
  };

  const handleStop = () => {
    if (useMockData) {
      setIsRunning(false);
      if (window.mockSimulationCleanup) {
        window.mockSimulationCleanup();
        window.mockSimulationCleanup = null;
      }
    } else {
      // Pentru WebSocket, doar setează stopped
      setIsRunning(false);
    }
  };

  const handleReset = () => {
    if (useMockData) {
      setMockState({
        vehicles: mockVehicles,
        events: mockEvents,
        systemStatus: { ...mockSystemStatus, running: false },
        risk: { danger: false, ttc: 5.0 },
        cooperation: cooperation,
      });
      setIsRunning(false);
      if (window.mockSimulationCleanup) {
        window.mockSimulationCleanup();
        window.mockSimulationCleanup = null;
      }
    } else {
      // Pentru WebSocket, doar resetează local state
      // Backend-ul va trimite date fresh
      setIsRunning(false);
    }
  };

  const handleScenarioChange = (scenarioId) => {
    setCurrentScenario(scenarioId);
    if (useMockData) {
      // Restart simulation cu noul scenariu
      if (isRunning && window.mockSimulationCleanup) {
        window.mockSimulationCleanup();
      }
      if (isRunning) {
        const cleanup = createMockSimulation((data) => {
          setMockState({
            ...data,
            cooperation: cooperation,
          });
        }, 500, scenarioId);
        window.mockSimulationCleanup = cleanup;
      }
    } else {
      // Pentru WebSocket, doar schimbă scenariul
      // Backend-ul va trimite date noi automat
      console.log('Scenario changed to:', scenarioId);
    }
  };

  // TOGGLE COOPERATION - CEL MAI IMPORTANT!
  const handleToggleCooperation = () => {
    const newCooperation = !cooperation;
    setCooperation(newCooperation);

    if (useMockData) {
      setMockState(prev => ({
        ...prev,
        cooperation: newCooperation,
      }));
    } else {
      // TODO: Send POST request la backend
      // fetch('/api/cooperation', { method: 'POST', body: JSON.stringify({ cooperation: newCooperation }) })
    }
  };

  // RESET SCENARIO - Resetează pozițiile mașinilor
  const handleResetScenario = () => {
    if (useMockData) {
      // Stop simularea curentă
      if (window.mockSimulationCleanup) {
        window.mockSimulationCleanup();
        window.mockSimulationCleanup = null;
      }

      // Resetează la scenariul curent cu poziții noi
      const { SCENARIOS } = require('./data/fakeData');
      const scenarioData = SCENARIOS[currentScenario] || SCENARIOS.normal;

      setMockState({
        vehicles: scenarioData.vehicles.map(v => ({
          ...v,
          speed: Math.sqrt(v.vx * v.vx + v.vy * v.vy) * 10,
          heading: Math.atan2(v.vy, v.vx),
          status: v.state,
        })),
        events: [],
        systemStatus: { ...mockSystemStatus, running: false },
        risk: scenarioData.risk,
        cooperation: cooperation,
      });

      setIsRunning(false);
    } else {
      // Pentru WebSocket, doar resetează local
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
            <span className="status-badge status-connected">🟢 Connected</span>
          ) : (
            <span className="status-badge status-disconnected">🔴 Disconnected</span>
          )}
          <button
            className="toggle-mode-btn"
            onClick={() => setUseMockData(!useMockData)}
          >
            {useMockData ? 'Switch to WebSocket' : 'Switch to Mock'}
          </button>
        </div>
      </header>

      {/* Error banner */}
      {error && !useMockData && (
        <div className="error-banner">
          ⚠️ {error}
        </div>
      )}

      {/* Main Layout */}
      <div className="app-layout">
        {/* Left Panel - Control Panel */}
        <aside className="left-panel">
          <ControlPanel
            isRunning={isRunning || systemStatus.running}
            cooperation={cooperation}
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
            risk={useMockData ? mockState.risk : (wsSystemStatus.risk || { danger: false })}
            dimensions={{ width: 800, height: 800 }}
          />
        </main>

        {/* Right Panel - Dashboard */}
        <aside className="right-panel">
          <Dashboard
            vehicles={vehicles}
            systemStatus={{
              ...systemStatus,
              running: isRunning || systemStatus.running,
              cooperation: cooperation, // Folosește state-ul de cooperation
            }}
            risk={useMockData ? mockState.risk : (wsSystemStatus.risk || { danger: false, ttc: 5.0 })}
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

