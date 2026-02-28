import React, { useState, useEffect } from 'react';
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

  // Auto-switch: dacă e conectat, folosim WebSocket, altfel mock
  const [useMockData, setUseMockData] = useState(!isConnected);

  // Update mock/websocket based on connection
  useEffect(() => {
    // Dacă e conectat la WebSocket, folosim date live
    if (isConnected) {
      setUseMockData(false);
      console.log('✅ Switched to WebSocket data');
    } else {
      // Altfel, fallback la mock data
      setUseMockData(true);
      console.log('📊 Switched to Mock data (fallback)');
    }
  }, [isConnected]);

  // State local pentru date mock
  const [mockState, setMockState] = useState({
    vehicles: mockVehicles,
    events: mockEvents,
    systemStatus: mockSystemStatus,
    risk: { danger: false, ttc: 5.0 },
    cooperation: true,
  });

  const [isRunning, setIsRunning] = useState(false);
  const [currentScenario, setCurrentScenario] = useState('normal');
  const [cooperation, setCooperation] = useState(true);

  // Selectează sursa de date
  const vehicles = useMockData ? mockState.vehicles : (wsState?.vehicles || []);
  const events = useMockData ? mockState.events : (wsState?.events || []);
  const systemStatus = useMockData ? mockState.systemStatus : (wsState?.systemStatus || {});
  const risk = useMockData ? mockState.risk : (wsState?.risk || { danger: false, ttc: 5.0 });

  // Handler pentru start/stop simulare
  const handleStart = () => {
    if (useMockData) {
      setIsRunning(true);
      const cleanup = createMockSimulation((data) => {
        setMockState({
          ...data,
          cooperation: cooperation,
        });
      }, 500, currentScenario);
      window.mockSimulationCleanup = cleanup;
    } else {
      setIsRunning(true);
      // Backend-ul va porni automat
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
      // Apelează backend API
      resetSimulation().then(() => {
        setIsRunning(false);
      });
    }
  };

  const handleScenarioChange = (scenarioId) => {
    setCurrentScenario(scenarioId);
    if (useMockData) {
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
      // Apelează backend API pentru schimbare scenariu
      resetSimulation(scenarioId).then(() => {
        console.log('✅ Scenario changed to:', scenarioId);
      });
    }
  };

  // TOGGLE COOPERATION - APELEAZĂ BACKEND
  const handleToggleCooperation = async () => {
    if (useMockData) {
      const newCooperation = !cooperation;
      setCooperation(newCooperation);
      setMockState(prev => ({
        ...prev,
        cooperation: newCooperation,
      }));
    } else {
      // Apelează backend API
      const result = await toggleCooperation();
      if (result) {
        console.log('✅ Cooperation toggled:', result);
      }
    }
  };

  // RESET SCENARIO - Resetează pozițiile mașinilor
  const handleResetScenario = async () => {
    if (useMockData) {
      if (window.mockSimulationCleanup) {
        window.mockSimulationCleanup();
        window.mockSimulationCleanup = null;
      }

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
      // Apelează backend API
      const result = await resetSimulation(currentScenario);
      if (result) {
        setIsRunning(false);
        console.log('✅ Scenario reset:', result);
      }
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

