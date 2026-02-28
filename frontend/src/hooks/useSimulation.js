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

  useEffect(() => {
    // Încearcă să conectezi la WebSocket
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
        console.log('📡 WebSocket message received:', data);

        // Transformează date de la backend în format frontend
        // Backend trimite: {tick, cooperation, scenario, vehicles, risk, semaphore, collisions, event_log}
        // Frontend așteaptă: {vehicles, risk, cooperation, events}
        const transformedState = {
          vehicles: data.vehicles || [],
          risk: {
            danger: data.risk?.risk === true,
            ttc: data.risk?.ttc || 999,
            action: data.risk?.action || 'go',
          },
          cooperation: data.cooperation || true,
          events: (data.event_log || []).map(evt => ({
            timestamp: evt.timestamp || new Date().toISOString(),
            type: evt.action?.toLowerCase() || 'info',
            message: `${evt.agent}: ${evt.action}`,
            details: { ttc: evt.ttc },
            vehicleId: evt.agent,
          })),
          semaphore: data.semaphore || {},
          collisions: data.collisions || [],
          tick: data.tick || 0,
        };

        // Update state cu datele transformate
        setState(transformedState);
      } catch (err) {
        console.error('❌ Error parsing WebSocket message:', err);
        // Fallback la FAKE_STATE dacă parse failed
        setState(FAKE_STATE);
      }
    };

    // Handler pentru erori - FALLBACK la FAKE_STATE
    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      console.log('🔄 Fallback to FAKE_STATE');

      setIsConnected(false);
      setError('WebSocket connection failed');

      // FALLBACK: folosește fakeData automat
      setState(FAKE_STATE);
    };

    // Handler pentru închidere conexiune
    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      setIsConnected(false);

      // FALLBACK: folosește fakeData automat
      setState(FAKE_STATE);

      // Optional: Auto-reconnect după 3 secunde
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('🔄 Attempting to reconnect...');
      }, 3000);
    };

    // Cleanup function - închide WebSocket la unmount
    return () => {
      console.log('🧹 Cleaning up WebSocket connection');

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [url]);

  // ===== METODE DE CONTROL =====

  /**
   * Reset simulation - resets to initial state
   */
  const resetSimulation = async (scenario = null) => {
    try {
      const response = await fetch(`${apiUrl}/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario }),
      });
      const data = await response.json();
      console.log('✅ Reset successful:', data);
      return data;
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
      const response = await fetch(`${apiUrl}/toggle-cooperation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await response.json();
      console.log('✅ Cooperation toggled:', data);
      return data;
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
      const response = await fetch(`${apiUrl}/scenarios`);
      const data = await response.json();
      console.log('✅ Scenarios loaded:', data);
      return data;
    } catch (err) {
      console.error('❌ Get scenarios failed:', err);
      return null;
    }
  };

  // Return state și metode
  return {
    state,           // Date simulare (fie de la WebSocket, fie FAKE_STATE)
    isConnected,     // Boolean: WebSocket conectat?
    error,           // Error message (dacă există)
    resetSimulation, // Metoda: reset
    toggleCooperation, // Metoda: toggle cooperation
    getScenarios,    // Metoda: get scenarios
  };
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

