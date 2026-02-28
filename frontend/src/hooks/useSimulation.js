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
export function useSimulation(url = 'ws://localhost:8000/ws') {
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

        // Update state cu datele primite
        setState(data);
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
        // Re-run effect by updating a dummy state (nu e necesar aici)
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

  // Return state și info conexiune
  return {
    state,           // Date simulare (fie de la WebSocket, fie FAKE_STATE)
    isConnected,     // Boolean: WebSocket conectat?
    error,           // Error message (dacă există)
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

