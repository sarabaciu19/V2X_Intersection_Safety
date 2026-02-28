import React from 'react';

const SCENARIOS = [
  { id: 'perpendicular', icon: '⊥', name: 'Perpendicular',     desc: 'N vs V — conflict direct'         },
  { id: 'multi',         icon: '✦', name: '4 Direcții',         desc: 'N, S, E, V simultan'               },
  { id: 'emergency',     icon: '🚑', name: 'Urgență',           desc: 'Ambulanță cu prioritate'           },
  { id: 'intents',       icon: '↰', name: 'Intenții mixte',     desc: 'Straight, stânga, dreapta'        },
];

const ControlPanel = ({
  cooperation     = true,
  currentScenario = 'perpendicular',
  onToggleCooperation,
  onScenarioChange,
  onReset,
}) => (
  <div style={s.container}>
    <div style={s.title}>🎮 Control</div>

    {/* COOPERATION TOGGLE */}
      <section style={s.section}>
        <div style={s.label}>Mod dirijare intersecție</div>
        <button
          onClick={onToggleCooperation}
          style={{
            ...s.btn,
            background:  cooperation ? '#059669' : '#92400e',
            boxShadow:   `0 0 18px ${cooperation ? '#05966966' : '#F59E0B66'}`,
            fontSize:    15,
            fontWeight:  900,
            letterSpacing: 1,
          }}
        >
          {cooperation ? '🤖  AUTO — sistem central' : '✋  MANUAL — tu decizi'}
        </button>
        <p style={s.hint}>
          {cooperation
            ? 'Sistemul central acordă clearance automat'
            : 'Tu dai clearance fiecărui vehicul prin click'}
        </p>
      </section>

    <div style={s.sep} />

    {/* SCENARII */}
    <section style={s.section}>
      <div style={s.label}>Scenariu</div>
      <div style={s.grid}>
        {SCENARIOS.map(sc => (
          <div
            key={sc.id}
            onClick={() => onScenarioChange?.(sc.id)}
            style={{
              ...s.card,
              ...(currentScenario === sc.id ? s.cardActive : {}),
            }}
          >
            <span style={{ fontSize: 22 }}>{sc.icon}</span>
            <span style={s.cardName}>{sc.name}</span>
            <span style={s.cardDesc}>{sc.desc}</span>
          </div>
        ))}
      </div>
    </section>

    <div style={s.sep} />

    {/* RESET */}
    <button onClick={onReset} style={{ ...s.btn, background: '#374151', fontSize: 13 }}>
      🔄  Reset scenariu
    </button>

    <div style={s.sep} />

    {/* LEGENDA STARI */}
    <section style={s.section}>
      <div style={s.label}>Stări vehicule</div>
      {[
        ['#3B82F6', 'moving',   'se apropie de intersecție'],
        ['#F59E0B', 'waiting',  'așteaptă la linia de stop'],
        ['#22C55E', 'crossing', 'a primit clearance, trece'],
        ['#EF4444', 'urgență',  'prioritate maximă'],
      ].map(([col, name, desc]) => (
        <div key={name} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
          <div style={{ width: 12, height: 12, borderRadius: 3, background: col, flexShrink: 0 }} />
          <span style={{ color: col, fontSize: 11, fontWeight: 700, minWidth: 60 }}>{name}</span>
          <span style={{ color: '#9CA3AF', fontSize: 10 }}>{desc}</span>
        </div>
      ))}
    </section>
  </div>
);

const s = {
  container: {
    display: 'flex', flexDirection: 'column', gap: 14,
    background: '#111827', color: '#fff',
    padding: 18, borderRadius: 8, height: '100%',
    fontFamily: 'monospace', overflowY: 'auto',
  },
  title: { fontSize: 18, fontWeight: 900, color: '#F9FAFB', borderBottom: '1px solid #374151', paddingBottom: 10 },
  section: { display: 'flex', flexDirection: 'column', gap: 8 },
  label: { fontSize: 11, color: '#6B7280', letterSpacing: 2, textTransform: 'uppercase' },
  hint:  { fontSize: 11, color: '#9CA3AF', margin: 0, lineHeight: 1.4 },
  sep:   { height: 1, background: '#1F2937' },
  btn: {
    padding: '12px 16px', border: 'none', borderRadius: 8,
    color: '#fff', cursor: 'pointer', fontFamily: 'monospace',
    width: '100%', transition: 'all 0.2s',
  },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 },
  card: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
    padding: '10px 6px', borderRadius: 8, cursor: 'pointer',
    background: '#1F2937', border: '2px solid #374151',
    transition: 'all 0.15s',
  },
  cardActive: { background: '#1E3A5F', borderColor: '#3B82F6', boxShadow: '0 0 10px #3B82F644' },
  cardName:   { fontSize: 11, fontWeight: 700, color: '#F9FAFB', textAlign: 'center' },
  cardDesc:   { fontSize: 9,  color: '#9CA3AF', textAlign: 'center', lineHeight: 1.3 },
};

export default ControlPanel;
