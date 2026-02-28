import React, { useEffect, useRef } from 'react';

const ACTION_STYLE = {
  CLEARANCE: { color: '#22C55E', icon: '✅' },
  ASTEAPTA:  { color: '#F59E0B', icon: '⏸' },
  WAIT:      { color: '#F59E0B', icon: '⏸' },
  INFO:      { color: '#60A5FA', icon: 'ℹ' },
};

/**
 * EventLog - Log decizii agenți în timp real
 * Afișează evenimentele și deciziile agenților V2X
 */
const EventLog = ({ events = [], maxEvents = 100 }) => {
  const bottomRef = useRef(null);

  // Auto-scroll la ultimul eveniment
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const shown = events.slice(-maxEvents);

  return (
    <div style={s.container}>
      <div style={s.header}>
        <span style={s.title}>📋 Log decizii sistem central</span>
        <span style={{ color: '#6B7280', fontSize: 11 }}>{shown.length} intrări</span>
      </div>

      <div style={s.log}>
        {shown.length === 0 && (
          <span style={{ color: '#4B5563', fontSize: 12 }}>
            — Nicio decizie încă. Pornește simularea. —
          </span>
        )}
        {shown.map((evt, i) => {
          const action = (evt.action || evt.type || 'INFO').toUpperCase();
          const style  = ACTION_STYLE[action] || ACTION_STYLE.INFO;
          return (
            <div key={i} style={s.row}>
              <span style={{ color: '#4B5563', fontSize: 10, minWidth: 60 }}>
                {evt.time || new Date(evt.timestamp).toLocaleTimeString('ro-RO')}
              </span>
              <span style={{ color: style.color, fontSize: 11, minWidth: 14 }}>
                {style.icon}
              </span>
              <span style={{ color: '#D1D5DB', fontWeight: 700, fontSize: 11, minWidth: 28 }}>
                {evt.agent || evt.vehicleId || '?'}
              </span>
              <span style={{ color: style.color, fontWeight: 700, fontSize: 11, minWidth: 80 }}>
                {action}
              </span>
              <span style={{ color: '#9CA3AF', fontSize: 10, flex: 1 }}>
                {evt.reason || evt.message || ''}
              </span>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

const s = {
  container: {
    background: '#0F172A', borderTop: '1px solid #1E293B',
    display: 'flex', flexDirection: 'column', height: '100%',
    fontFamily: 'monospace',
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '6px 16px', borderBottom: '1px solid #1E293B',
  },
  title: { color: '#94A3B8', fontSize: 12, fontWeight: 700, letterSpacing: 1 },
  log: {
    flex: 1, overflowY: 'auto', padding: '6px 16px',
    display: 'flex', flexDirection: 'column', gap: 3,
    maxHeight: 130,
  },
  row: {
    display: 'flex', gap: 8, alignItems: 'flex-start',
    borderBottom: '1px solid #0F172A', paddingBottom: 2,
  },
};

export default EventLog;

