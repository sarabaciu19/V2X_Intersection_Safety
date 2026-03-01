import React from 'react';

const MEM_ACTION_STYLE = {
  GO: { color: '#22c55e', icon: '🟢' },
  YIELD: { color: '#ef4444', icon: '🛑' },
  BRAKE: { color: '#f59e0b', icon: '🟠' }, WAIT: { color: '#b45309', icon: '⏸' },
};

/**
 * EventLog — Memorie decizii per agent (ultimele 10 per vehicul)
 */
const EventLog = ({ agentsMemory = {} }) => {
  const agents = Object.entries(agentsMemory);

  return (
    <div style={s.container}>
      <div style={s.header}>
        <span style={s.title}>🧠 Memorie decizii agenți</span>
        <span style={{ color: '#a08060', fontSize: 11 }}>live · ultimele 10 decizii per vehicul</span>
      </div>
      <div style={s.body}>
        {agents.length === 0 && (
          <span style={{ color: '#c8b89a', fontSize: 12, padding: '8px 16px' }}>
            — Nicio decizie încă. Pornește simularea. —
          </span>
        )}
        {agents.map(([vid, memory]) => (
          <div key={vid} style={s.agentCol}>
            <div style={s.agentHeader}>🚗 {vid}</div>
            <div style={s.agentRows}>
              {memory.length === 0 && (
                <span style={{ color: '#c8b89a', fontSize: 10, padding: '4px 8px', display: 'block' }}>— fără decizii —</span>
              )}
              {[...memory].reverse().map((entry, i) => {
                const st = MEM_ACTION_STYLE[entry.action] || { color: '#2563eb', icon: 'ℹ' };
                return (
                  <div key={i} style={s.memRow}>
                    <span style={{ color: '#a08060', fontSize: 9, minWidth: 52 }}>{entry.tick_time}</span>
                    <span style={{ fontSize: 10, minWidth: 14 }}>{st.icon}</span>
                    <span style={{ color: st.color, fontWeight: 700, fontSize: 10, minWidth: 44 }}>{entry.action}</span>
                    <span style={{ color: '#6b4f35', fontSize: 9, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {entry.reason}
                    </span>
                    {entry.ttc < 999 && (
                      <span style={{ color: '#a08060', fontSize: 9, marginLeft: 4 }}>TTC={entry.ttc}s</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
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
    padding: '5px 16px', borderBottom: '1px solid #c8b89a',
    background: '#e6ddd0',
  },
  title: { color: '#6b4f35', fontSize: 12, fontWeight: 700, letterSpacing: 1 },
  body: {
    flex: 1, display: 'flex', flexDirection: 'row', overflowY: 'auto',
  },
  agentCol: {
    flex: 1, borderRight: '1px solid #c8b89a', display: 'flex',
    flexDirection: 'column', minWidth: 0,
  },
  agentHeader: {
    background: '#e6ddd0', color: '#5c4028', fontSize: 11, fontWeight: 700,
    padding: '3px 8px', borderBottom: '1px solid #c8b89a', letterSpacing: 0.5,
  },
  agentRows: {
    flex: 1, overflowY: 'auto',
  },
  memRow: {
    display: 'flex', alignItems: 'center', gap: 4,
    padding: '2px 8px', borderBottom: '1px solid rgba(200,184,154,0.3)',
  },
};

export default EventLog;
