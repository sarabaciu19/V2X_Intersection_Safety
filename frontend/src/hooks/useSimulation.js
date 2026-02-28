import { useState, useEffect, useRef, useCallback } from 'react';
import { FAKE_STATE } from '../data/fakeData';

const API_URL = (wsUrl) => wsUrl.replace('ws://', 'http://').replace('/ws', '');

export default function useSimulation(wsUrl = 'ws://localhost:8000/ws') {
  const [state,       setState]       = useState(FAKE_STATE);
  const [isConnected, setIsConnected] = useState(false);
  const [error,       setError]       = useState(null);
  const wsRef  = useRef(null);
  const apiUrl = API_URL(wsUrl);

  // ── WebSocket ────────────────────────────────────────────────────
  useEffect(() => {
    let ws;
    let retryTimeout;

    const connect = () => {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen    = () => { setIsConnected(true); setError(null); };
      ws.onmessage = (e) => { try { setState(JSON.parse(e.data)); } catch {} };
      ws.onerror   = ()  => setError('WebSocket eroare');
      ws.onclose   = ()  => {
        setIsConnected(false);
        retryTimeout = setTimeout(connect, 2000);
      };
    };

    connect();
    return () => { clearTimeout(retryTimeout); ws?.close(); };
  }, [wsUrl]);

  // ── Generic fetch helper ─────────────────────────────────────────
  const call = useCallback(async (method, path, body = undefined) => {
    try {
      const res = await fetch(`${apiUrl}${path}`, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : {},
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`❌ ${method} ${path}:`, err.message);
      throw err;
    }
  }, [apiUrl]);

  // ── Control simulare ─────────────────────────────────────────────
  const startSimulation    = () => call('POST', '/start');
  const stopSimulation     = () => call('POST', '/stop');
  const resetSimulation    = (scenario) => call('POST', '/reset', scenario ? { scenario } : {});
  const toggleCooperation  = () => call('POST', '/toggle-cooperation');
  const grantClearance     = (id) => call('POST', `/grant-clearance/${id}`);

  // ── Custom scenario ──────────────────────────────────────────────
  const customAddVehicle    = (def)  => call('POST',   '/custom/vehicle', def);
  const customRemoveVehicle = (id)   => call('DELETE', `/custom/vehicle/${id}`);
  const customUpdateVehicle = (id, updates) => call('PATCH', `/custom/vehicle/${id}`, updates);
  const customClear         = ()     => call('DELETE', '/custom/clear');
  const getCustomScenario   = ()     => call('GET',    '/custom/scenario');

  return {
    state, isConnected, error,
    startSimulation, stopSimulation,
    resetSimulation, toggleCooperation, grantClearance,
    customAddVehicle, customRemoveVehicle, customUpdateVehicle,
    customClear, getCustomScenario,
  };
}
