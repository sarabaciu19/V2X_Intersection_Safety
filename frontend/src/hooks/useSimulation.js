import { useState, useEffect, useRef } from 'react';
import { FAKE_STATE } from '../data/fakeData';

/**
 * useSimulation - Hook pentru conectare WebSocket
 *
 * Specificații:
 * - useEffect + WebSocket nativ (fără librării extra)
 * - Conectare la ws://localhost:8000/ws
 * - La fiecare mesaj primit: parse JSON și update state React
 * - Fallback: dacă WebSocket nu e conectat, folosește fakeData automat
 * - Astfel poți lucra independent și integrezi ușor când backend-ul e gata
 */
export function useSimulation(url = 'ws://localhost:8000/ws', apiUrl = 'http://localhost:8000') {
  // State pentru date simulare - începe cu FAKE_STATE
  const [state, setState] = useState(FAKE_STATE);

  // State pentru status conexiune
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);

  // Ref pentru WebSocket
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  /**
   * connect - funcție pentru a stabili conexiunea WebSocket
   */
  const connect = () => {
    // Nu reconecta dacă deja e deschis
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    // Handler pentru conexiune reușită
    ws.onopen = () => {
      console.log('✅ WebSocket connected to', url);
      setIsConnected(true);
      setError(null);
    };

    // Handler pentru mesaje primite - PARSE JSON și UPDATE STATE
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Transformă formatul backend → format frontend
        const transformed = {
          // Vehiculele vin direct — formatul e compatibil
          vehicles: (data.vehicles || []).map(v => ({
            ...v,
            status: v.state,           // alias pentru componente vechi
            speed:  Math.sqrt((v.vx || 0) ** 2 + (v.vy || 0) ** 2) * 10,
            heading: Math.atan2(v.vy || 0, v.vx || 0),
          })),
          risk: {
            danger: data.risk?.risk === true,
            ttc:    data.risk?.ttc   ?? 999,
            action: data.risk?.action ?? 'go',
            pair:   data.risk?.pair   ?? null,
          },
          cooperation: data.cooperation ?? true,
          scenario:    data.scenario    ?? 'perpendicular',
          tick:        data.tick        ?? 0,
          semaphore:   data.semaphore   ?? {},
          collisions:  data.collisions  ?? [],
          // event_log din backend → events pentru EventLog component
          events: (data.event_log || []).map(evt => ({
            timestamp: evt.timestamp ? new Date(evt.timestamp * 1000).toISOString() : new Date().toISOString(),
            type:      (evt.action || 'info').toLowerCase(),
            message:   `[${evt.time || ''}] Agent ${evt.agent}: ${evt.action}${evt.ttc ? ` — TTC=${evt.ttc}s` : ''}`,
            vehicleId: evt.agent,
            details:   { ttc: evt.ttc, reason: evt.reason },
          })),
        };

        setState(transformed);
      } catch (err) {
        console.error('❌ Error parsing WebSocket message:', err);
      }
    };

    // Handler pentru erori - FALLBACK la FAKE_STATE
    ws.onerror = () => {
      console.error('❌ WebSocket error');
      setIsConnected(false);
      setError('WebSocket connection failed — folosind date Mock');
      setState(FAKE_STATE);
    };

    // Handler pentru închidere conexiune
    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      setIsConnected(false);
      // Reconectare automată după 3s
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };
  };

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [url]); // eslint-disable-line

  // ===== METODE CONTROL BACKEND =====

  /**
   * Reset simulation - resets to initial state
   */
  const resetSimulation = async (scenario = null) => {
    try {
      const res = await fetch(`${apiUrl}/reset`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ scenario }),
      });
      return await res.json();
    } catch (err) {
      console.error('❌ Reset failed:', err);
      return null;
    }
  };

  /**
   * Toggle cooperation - ON/OFF for V2X
   */
  const toggleCooperation = async () => {
    try {
      const res = await fetch(`${apiUrl}/toggle-cooperation`, { method: 'POST' });
      return await res.json();
    } catch (err) {
      console.error('❌ Toggle cooperation failed:', err);
      return null;
    }
  };

  /**
   * Get scenarios list
   */
  const getScenarios = async () => {
    try {
      const res = await fetch(`${apiUrl}/scenarios`);
      return await res.json();
    } catch (err) {
      console.error('❌ Get scenarios failed:', err);
      return null;
    }
  };

  // Return state și metode
  return { state, isConnected, error, resetSimulation, toggleCooperation, getScenarios };
}

/**
 * Versiune simplificată EXACTĂ din specificații
 * Pentru uz minimal - doar state
 */
export function useSimulationSimple() {
  const [state, setState] = useState(FAKE_STATE);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    // Parse JSON și update state
    ws.onmessage = (e) => setState(JSON.parse(e.data));

    // Fallback la FAKE_STATE pe eroare
    ws.onerror = () => setState(FAKE_STATE);

    // Cleanup
    return () => ws.close();
  }, []);

  return state;
}

// Export default pentru versiunea completă
export default useSimulation;

