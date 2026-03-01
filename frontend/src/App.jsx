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
  const collisions = wsState?.collisions || [];

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
          {/* Risk Banner overlay */}
          {risk?.risk && (
            <div style={{
              position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)',
              zIndex: 100, pointerEvents: 'none',
              background: risk.ttc < 1.5 ? 'rgba(220,38,38,0.92)' : 'rgba(202,138,4,0.92)',
              border: `2px solid ${risk.ttc < 1.5 ? '#fca5a5' : '#fde68a'}`,
              borderRadius: 10, padding: '8px 22px',
              display: 'flex', alignItems: 'center', gap: 12,
              boxShadow: `0 0 24px ${risk.ttc < 1.5 ? '#ef444488' : '#f59e0b88'}`,
              animation: 'riskPulse 0.8s ease-in-out infinite alternate',
            }}>
              <span style={{ fontSize: 22 }}>{risk.ttc < 1.5 ? '🚨' : '⚠️'}</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <span style={{ color: '#fff', fontWeight: 900, fontSize: 14, letterSpacing: 1 }}>
                  {risk.ttc < 1.5 ? 'RISC CRITIC DE COLIZIUNE' : 'AVERTISMENT COLIZIUNE'}
                </span>
                <span style={{ color: 'rgba(255,255,255,0.9)', fontSize: 12 }}>
                  TTC: <b>{risk.ttc?.toFixed(2)}s</b>
                  {risk.pair && <> · Vehicule: <b>{risk.pair[0]}</b> ↔ <b>{risk.pair[1]}</b></>}
                </span>
              </div>
            </div>
          )}
          {/* Collision Banner overlay */}
          {collisions.length > 0 && (
            <div style={{
              position: 'absolute', top: risk?.risk ? 70 : 12, left: '50%', transform: 'translateX(-50%)',
              zIndex: 101, pointerEvents: 'none',
              background: 'rgba(153,27,27,0.95)',
              border: '2px solid #FCA5A5',
              borderRadius: 10, padding: '8px 22px',
              display: 'flex', alignItems: 'center', gap: 12,
              boxShadow: '0 0 24px rgba(239,68,68,0.6)',
              animation: 'riskPulse 0.5s ease-in-out infinite alternate',
            }}>
              <span style={{ fontSize: 22 }}>💥</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <span style={{ color: '#fff', fontWeight: 900, fontSize: 14, letterSpacing: 1 }}>
                  COLIZIUNE DETECTATĂ!
                </span>
                <span style={{ color: 'rgba(255,255,255,0.9)', fontSize: 12 }}>
                  {collisions.map(c => c.vehicles.join(' ↔ ')).join(', ')}
                </span>
              </div>
            </div>
          )}
          <IntersectionCanvas
            vehicles={vehicles}
            semaphore={semaphore}
            risk={risk}
            collisions={collisions}
            agentsMemory={agentsMemory}
            cooperation={liveCooperation}
            scenario={currentScenario}
            onGrantClearance={!liveCooperation ? grantClearance : null}
            dimensions={{ width: 800, height: 800 }}
          />
        </main>

        {/* Right Panel - Dashboard */}
        <aside className="right-panel">
          <Dashboard
            vehicles={vehicles}
            semaphore={semaphore}
            risk={risk}
            cooperation={liveCooperation}
            agentsMemory={agentsMemory}
            collisions={collisions}
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

