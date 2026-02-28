import React, { useState } from 'react';
import CustomScenarioEditor from './CustomScenarioEditor';

const SCENARIOS = [
  { id: 'perpendicular', icon: '⊥', name: 'Perpendicular',  desc: 'N vs V — conflict direct'        },
  { id: 'multi',         icon: '✦', name: '4 Direcții',      desc: 'N, S, E, V simultan'              },
  { id: 'emergency',     icon: '🚑', name: 'Urgență',        desc: 'Ambulanță cu prioritate'          },
  { id: 'intents',       icon: '↰', name: 'Intenții mixte',  desc: 'Straight, stânga, dreapta'       },
  { id: 'custom',        icon: '🛠', name: 'Custom',          desc: 'Configurează tu vehiculele'      },
];

const TABS = ['control', 'scenarii', 'custom', 'legenda'];
const TAB_LABELS = { control: '⚙ Control', scenarii: '📋 Scenarii', custom: '🛠 Custom', legenda: '🗺 Legendă' };

const ControlPanel = ({
  cooperation        = true,
  paused             = false,
  currentScenario    = 'perpendicular',
  customScenario     = [],
  onToggleCooperation,
  onScenarioChange,
  onReset,
  onStart,
  onStop,
  onCustomAdd,
  onCustomRemove,
  onCustomUpdate,
  onCustomClear,
}) => {
  const [tab, setTab] = useState('control');

  const handleRunCustom = async () => {
    await onScenarioChange?.('custom');
  };

  return (
    <div style={s.outer}>
      {/* Tab bar */}
      <div style={s.tabBar}>
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            ...s.tabBtn,
            background:   tab === t ? '#e6ddd0' : 'transparent',
            borderBottom: tab === t ? '2px solid #7c5c38' : '2px solid transparent',
            color:        tab === t ? '#2c1e0f' : '#a08060',
          }}>
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      <div style={s.body}>

        {/* ── TAB: CONTROL ── */}
        {tab === 'control' && (
          <div style={s.section}>

            {/* START / STOP */}
            <div style={s.label}>Simulare</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={onStart} disabled={!paused}
                style={{
                  ...s.simBtn, flex: 1,
                  background:  !paused ? '#d4e8d4' : '#c8e6c8',
                  borderColor: !paused ? '#6aaa6a' : '#3a8a3a',
                  color:       !paused ? '#4a7a4a' : '#1a5a1a',
                  opacity:     !paused ? 0.55 : 1,
                  cursor:      !paused ? 'default' : 'pointer',
                  boxShadow:   !paused ? 'none' : '0 0 10px rgba(58,138,58,0.3)',
                }}>
                ▶ START
              </button>
              <button onClick={onStop} disabled={paused}
                style={{
                  ...s.simBtn, flex: 1,
                  background:  paused ? '#f0d8d8' : '#f5c8c8',
                  borderColor: paused ? '#cc8888' : '#aa4444',
                  color:       paused ? '#885555' : '#6b1e1e',
                  opacity:     paused ? 0.55 : 1,
                  cursor:      paused ? 'default' : 'pointer',
                  boxShadow:   paused ? 'none' : '0 0 10px rgba(185,28,28,0.2)',
                }}>
                ⏹ STOP
              </button>
            </div>
            <div style={{ color: paused ? '#b91c1c' : '#166534', fontSize: 11, textAlign: 'center', fontWeight: 700 }}>
              {paused ? '⏸ Simulare oprită' : '● Rulează live'}
            </div>

            <div style={s.sep} />

            {/* COOPERATION */}
            <div style={s.label}>Mod dirijare intersecție</div>
            <button onClick={onToggleCooperation} style={{
              ...s.bigBtn,
              background:  cooperation ? '#deeede' : '#f5e8d0',
              borderColor: cooperation ? '#3a8a3a' : '#b45309',
              boxShadow:   `0 0 12px ${cooperation ? 'rgba(58,138,58,0.2)' : 'rgba(180,83,9,0.2)'}`,
              color:       cooperation ? '#1a5a1a' : '#7c3a00',
            }}>
              {cooperation ? '🤖  AUTO — sistem central' : '✋  MANUAL — tu decizi'}
            </button>
            <p style={s.hint}>
              {cooperation
                ? 'Sistemul central aplică regulile de circulație automat'
                : 'Click pe vehicul portocaliu (canvas) sau buton în dashboard'}
            </p>

            <div style={s.sep} />

            {/* RESET */}
            <button onClick={onReset} style={{ ...s.bigBtn, background: '#ede5d8', borderColor: '#c8b89a', color: '#6b4f35', fontSize: 12 }}>
              🔄 Reset scenariu curent
            </button>

            <div style={{ color: '#a08060', fontSize: 10, textAlign: 'center', fontFamily: "'Inter',sans-serif" }}>
              Scenariu activ: <span style={{ color: '#2c1e0f', fontWeight: 700 }}>{currentScenario}</span>
            </div>
          </div>
        )}

        {/* ── TAB: SCENARII ── */}
        {tab === 'scenarii' && (
          <div style={s.section}>
            <div style={s.label}>Alege scenariu</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {SCENARIOS.filter(sc => sc.id !== 'custom').map(sc => (
                <div key={sc.id} onClick={() => onScenarioChange?.(sc.id)}
                  style={{
                    ...s.scenCard,
                    background:  currentScenario === sc.id ? '#ddd0c0' : '#e6ddd0',
                    borderColor: currentScenario === sc.id ? '#7c5c38' : '#c8b89a',
                    boxShadow:   currentScenario === sc.id ? '0 0 8px rgba(124,92,56,0.25)' : 'none',
                  }}>
                  <span style={{ fontSize: 24 }}>{sc.icon}</span>
                  <div>
                    <div style={{ color: '#2c1e0f', fontWeight: 700, fontSize: 12 }}>{sc.name}</div>
                    <div style={{ color: '#a08060', fontSize: 10 }}>{sc.desc}</div>
                  </div>
                  {currentScenario === sc.id && <span style={{ color: '#7c5c38', marginLeft: 'auto', fontSize: 16 }}>●</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── TAB: CUSTOM ── */}
        {tab === 'custom' && (
          <CustomScenarioEditor
            customScenario={customScenario}
            onAdd={onCustomAdd}
            onRemove={onCustomRemove}
            onUpdate={onCustomUpdate}
            onClear={onCustomClear}
            onRunCustom={handleRunCustom}
            isCustomActive={currentScenario === 'custom'}
          />
        )}

        {/* ── TAB: LEGENDA ── */}
        {tab === 'legenda' && (
          <div style={s.section}>
            <div style={s.label}>Stări vehicule</div>
            {[
              ['#2563eb', 'moving',   'Se apropie de intersecție'],
              ['#b45309', 'waiting',  'Așteaptă la linia de stop'],
              ['#166534', 'crossing', 'A primit clearance, traversează'],
              ['#b91c1c', 'urgență',  'Vehicul de urgență'],
            ].map(([col, name, desc]) => (
              <div key={name} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 6 }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: col, marginTop: 2, flexShrink: 0 }} />
                <div>
                  <span style={{ color: col, fontSize: 11, fontWeight: 700 }}>{name}</span>
                  <div style={{ color: '#a08060', fontSize: 10 }}>{desc}</div>
                </div>
              </div>
            ))}

            <div style={s.sep} />
            <div style={s.label}>Reguli de circulație (România)</div>
            {[
              '🚑 Urgența trece întotdeauna primul',
              '🔄 Vehicul în intersecție continuă traversarea',
              '➡ Prioritate de dreapta (cedezi celui din dreapta ta)',
              '↰ Viraj stânga cedează celor care merg înainte/dreapta',
              '⏱ La egalitate → FIFO (cine a așteptat mai mult trece)',
            ].map((r, i) => (
              <div key={i} style={{ color: '#6b4f35', fontSize: 10, marginBottom: 4 }}>{r}</div>
            ))}

            <div style={s.sep} />
            <div style={s.label}>Benzi — sens unic</div>
            {[
              ['#2563eb', 'N', '↓ Nord → Sud  (banda x=415)'],
              ['#166534', 'S', '↑ Sud → Nord  (banda x=385)'],
              ['#b45309', 'E', '← Est → Vest  (banda y=415)'],
              ['#7c3aed', 'V', '→ Vest → Est  (banda y=385)'],
            ].map(([col, dir, desc]) => (
              <div key={dir} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: col, flexShrink: 0 }} />
                <span style={{ color: col, fontSize: 11, fontWeight: 700, minWidth: 14 }}>{dir}</span>
                <span style={{ color: '#a08060', fontSize: 10 }}>{desc}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const s = {
  outer: {
    display: 'flex', flexDirection: 'column',
    background: '#ede5d8', color: '#2c1e0f',
    borderRadius: 8, height: '100%',
    fontFamily: "'Inter','Segoe UI',sans-serif", overflow: 'hidden',
    border: '1px solid #c8b89a',
  },
  tabBar: {
    display: 'flex', borderBottom: '1px solid #c8b89a', flexShrink: 0,
    background: '#e6ddd0',
  },
  tabBtn: {
    flex: 1, padding: '9px 2px', border: 'none', cursor: 'pointer',
    fontFamily: "'JetBrains Mono','Fira Code',monospace", fontSize: 9, fontWeight: 700,
    letterSpacing: 0.5, transition: 'all 0.15s', background: 'transparent',
  },
  body: { flex: 1, overflowY: 'auto', padding: 14 },
  section: { display: 'flex', flexDirection: 'column', gap: 10 },
  label: { fontSize: 10, color: '#a08060', letterSpacing: 2, textTransform: 'uppercase', fontFamily: "'Inter',sans-serif" },
  sep:   { height: 1, background: '#c8b89a' },
  hint:  { fontSize: 10, color: '#a08060', margin: 0, lineHeight: 1.5, fontFamily: "'Inter',sans-serif" },
  simBtn: {
    padding: '11px 0', border: '2px solid', borderRadius: 8,
    fontFamily: "'JetBrains Mono',monospace", fontWeight: 900, fontSize: 13, letterSpacing: 1,
    transition: 'all 0.2s',
  },
  bigBtn: {
    padding: '11px 14px', border: '2px solid', borderRadius: 8,
    fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 12, letterSpacing: 0.5,
    cursor: 'pointer', width: '100%', transition: 'all 0.2s',
  },
  scenCard: {
    display: 'flex', alignItems: 'center', gap: 10,
    padding: '10px 12px', border: '2px solid', borderRadius: 8,
    cursor: 'pointer', transition: 'all 0.15s',
  },
};

export default ControlPanel;
