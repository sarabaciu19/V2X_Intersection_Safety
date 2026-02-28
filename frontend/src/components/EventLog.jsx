import React, { useEffect, useRef } from 'react';

const ACTION_STYLE = {
  CLEARANCE: { color: '#166534', icon: '✅' },
  ASTEAPTA:  { color: '#b45309', icon: '⏸' },
  WAIT:      { color: '#b45309', icon: '⏸' },
  INFO:      { color: '#2563eb', icon: 'ℹ' },
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
        <span style={{ color: '#a08060', fontSize: 11 }}>{shown.length} intrări</span>
      </div>
      <div style={s.log}>
        {shown.length === 0 && (
          <span style={{ color: '#c8b89a', fontSize: 12 }}>
            — Nicio decizie încă. Pornește simularea. —
          </span>
        )}
        {shown.map((evt, i) => {
          const action = (evt.action || evt.type || 'INFO').toUpperCase();
          const style  = ACTION_STYLE[action] || ACTION_STYLE.INFO;
          return (
            <div key={i} style={s.row}>
              <span style={{ color: '#a08060', fontSize: 10, minWidth: 60 }}>
                {evt.time || new Date(evt.timestamp).toLocaleTimeString('ro-RO')}
              </span>
              <span style={{ color: style.color, fontSize: 11, minWidth: 14 }}>{style.icon}</span>
              <span style={{ color: '#2c1e0f', fontWeight: 700, fontSize: 11, minWidth: 28 }}>
                {evt.agent || evt.vehicle_id || '?'}
              </span>
              <span style={{ color: style.color, fontWeight: 700, fontSize: 11, minWidth: 80 }}>
                {action}
              </span>
              <span style={{ color: '#6b4f35', fontSize: 10, flex: 1 }}>
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
    background: '#ede5d8', borderTop: '1px solid #c8b89a',
    display: 'flex', flexDirection: 'column', height: '100%',
    fontFamily: "'JetBrains Mono','Fira Code',monospace",
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '6px 16px', borderBottom: '1px solid #c8b89a',
    background: '#e6ddd0',
  },
  title: { color: '#6b4f35', fontSize: 12, fontWeight: 700, letterSpacing: 1 },
  log: {
    flex: 1, overflowY: 'auto', padding: '6px 16px',
    display: 'flex', flexDirection: 'column', gap: 3,
    maxHeight: 130,
  },
  row: {
    display: 'flex', gap: 8, alignItems: 'flex-start',
    borderBottom: '1px solid #e6ddd0', paddingBottom: 2,
  },
};

export default EventLog;

