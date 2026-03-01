import React from 'react';

const MEM_ACTION_STYLE = {
  GO:                   { color: '#22c55e', icon: '🟢' },
  YIELD:                { color: '#ef4444', icon: '🛑' },
  BRAKE:                { color: '#f59e0b', icon: '🟠' },
  WAIT:                 { color: '#b45309', icon: '⏸'  },
  CLEARANCE:            { color: '#34d399', icon: '✅' },
  CLEARANCE_SPEED:      { color: '#f97316', icon: '⚡' },
  YIELD_SPEED_OVERRIDE: { color: '#dc2626', icon: '⚠️' },
  V2I_STOP:             { color: '#ef4444', icon: '🚦' },
  V2I_REDUCE:           { color: '#f59e0b', icon: '📡' },
  V2I_GO:               { color: '#22c55e', icon: '📡' },
  STOP:                 { color: '#ef4444', icon: '🔴' },
  HOLD:                 { color: '#f59e0b', icon: '🟡' },
  CRASH:                { color: '#991b1b', icon: '💥' },
  // AEB Fallback — radar local, frânare violentă/târzie (non-V2X)
  'AEB_ACTIVAT':        { color: '#f97316', icon: '🛑' },
};

const EventLog = ({ agentsMemory = {} }) => {
  const agents = Object.entries(agentsMemory);

  return (
    <div style={s.container}>
      <div style={s.header}>
        <span style={s.title}>Memorie decizii agenți</span>
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
                <span style={{ color: '#c8b89a', fontSize: 10, padding: '4px 8px', display: 'block' }}>
                  — fără decizii —
                </span>
              )}
              {[...memory].reverse().map((entry, i) => {
                const st = MEM_ACTION_STYLE[entry.action] || { color: '#2563eb', icon: 'ℹ' };
                const isOverride  = entry.action === 'YIELD_SPEED_OVERRIDE';
                const isSpeedClear = entry.action === 'CLEARANCE_SPEED';
                const isAEB       = entry.action === 'AEB_ACTIVAT';
                return (
                  <div key={i} style={{
                    ...s.memRow,
                    background: isAEB        ? 'rgba(249,115,22,0.14)'
                              : isOverride   ? 'rgba(220,38,38,0.10)'
                              : isSpeedClear ? 'rgba(249,115,22,0.08)'
                              : 'transparent',
                    borderLeft: isAEB        ? '3px solid #f97316'
                              : isOverride   ? '3px solid #dc2626'
                              : isSpeedClear ? '3px solid #f97316'
                              : '3px solid transparent',
                  }}>
                    <span style={{ color: '#a08060', fontSize: 9, minWidth: 52 }}>{entry.tick_time}</span>
                    <span style={{ fontSize: 10, minWidth: 14 }}>{st.icon}</span>
                    <span style={{ color: st.color, fontWeight: 700, fontSize: 10, minWidth: 44 }}>
                      {entry.action === 'YIELD_SPEED_OVERRIDE' ? 'YIELD⚠'
                       : entry.action === 'CLEARANCE_SPEED'    ? 'GO⚡'
                       : entry.action === 'AEB_ACTIVAT'        ? '⚠AEB!'
                       : entry.action}
                    </span>
                    {entry.target_id && (
                      <span style={{
                        color: '#fff', background: '#374151', borderRadius: 3,
                        fontSize: 8, padding: '1px 5px', marginRight: 3, whiteSpace: 'nowrap',
                        fontWeight: 700,
                      }}>→{entry.target_id}</span>
                    )}
                    <span style={{
                      color: isOverride ? '#fca5a5' : '#6b4f35',
                      fontSize: 9, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {entry.reason}
                    </span>
                    {entry.ttc < 999 && (
                      <span style={{ color: '#a08060', fontSize: 9, marginLeft: 4 }}>
                        TTC={entry.ttc}s
                      </span>
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
