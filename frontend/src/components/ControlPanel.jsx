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
            background:  tab === t ? '#1E3A5F' : 'transparent',
            borderBottom: tab === t ? '2px solid #3B82F6' : '2px solid transparent',
            color: tab === t ? '#93C5FD' : '#4B5563',
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
                  ...s.simBtn,
                  flex: 1,
                  background:  !paused ? '#065F46' : '#14532D',
                  borderColor: !paused ? '#10B981' : '#22C55E',
                  color:       !paused ? '#6EE7B7' : '#86EFAC',
                  opacity:     !paused ? 0.5 : 1,
                  cursor:      !paused ? 'default' : 'pointer',
                  boxShadow:   !paused ? 'none' : '0 0 14px #22C55E55',
                }}>
                ▶ START
              </button>
              <button onClick={onStop} disabled={paused}
                style={{
                  ...s.simBtn,
                  flex: 1,
                  background:  paused  ? '#7F1D1D' : '#450A0A',
                  borderColor: paused  ? '#EF4444' : '#DC2626',
                  color:       paused  ? '#FCA5A5' : '#F87171',
                  opacity:     paused  ? 0.5 : 1,
                  cursor:      paused  ? 'default' : 'pointer',
                  boxShadow:   paused  ? 'none' : '0 0 14px #EF444455',
                }}>
                ⏹ STOP
              </button>
            </div>
            <div style={{ color: paused ? '#F87171' : '#22C55E', fontSize: 11, textAlign: 'center', fontWeight: 700 }}>
              {paused ? '⏸ Simulare oprită' : '● Rulează live'}
            </div>

            <div style={s.sep} />

            {/* COOPERATION */}
            <div style={s.label}>Mod dirijare intersecție</div>
            <button onClick={onToggleCooperation} style={{
              ...s.bigBtn,
              background:   cooperation ? '#065F4622' : '#92400e22',
              borderColor:  cooperation ? '#059669'   : '#F59E0B',
              boxShadow:    `0 0 18px ${cooperation ? '#05966944' : '#F59E0B44'}`,
              color:        cooperation ? '#6EE7B7'   : '#FBBF24',
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
            <button onClick={onReset} style={{ ...s.bigBtn, background: '#1F2937', borderColor: '#374151', color: '#9CA3AF', fontSize: 12 }}>
              🔄 Reset scenariu curent
            </button>

            <div style={{ color: '#4B5563', fontSize: 10, textAlign: 'center' }}>
              Scenariu activ: <span style={{ color: '#F9FAFB', fontWeight: 700 }}>{currentScenario}</span>
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
                    background:   currentScenario === sc.id ? '#1E3A5F' : '#1F2937',
                    borderColor:  currentScenario === sc.id ? '#3B82F6' : '#374151',
                    boxShadow:    currentScenario === sc.id ? '0 0 10px #3B82F644' : 'none',
                  }}>
                  <span style={{ fontSize: 24 }}>{sc.icon}</span>
                  <div>
                    <div style={{ color: '#F9FAFB', fontWeight: 700, fontSize: 12 }}>{sc.name}</div>
                    <div style={{ color: '#6B7280', fontSize: 10 }}>{sc.desc}</div>
                  </div>
                  {currentScenario === sc.id && <span style={{ color: '#3B82F6', marginLeft: 'auto' }}>●</span>}
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
              ['#3B82F6', 'moving',   'Se apropie de intersecție'],
              ['#F59E0B', 'waiting',  'Așteaptă la linia de stop'],
              ['#22C55E', 'crossing', 'A primit clearance, traversează'],
              ['#EF4444', 'urgență',  'Vehicul de urgență'],
            ].map(([col, name, desc]) => (
              <div key={name} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 6 }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: col, marginTop: 2, flexShrink: 0 }} />
                <div>
                  <span style={{ color: col, fontSize: 11, fontWeight: 700 }}>{name}</span>
                  <div style={{ color: '#6B7280', fontSize: 10 }}>{desc}</div>
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
              <div key={i} style={{ color: '#9CA3AF', fontSize: 10, marginBottom: 4 }}>{r}</div>
            ))}

            <div style={s.sep} />
            <div style={s.label}>Benzi — sens unic</div>
            {[
              ['#3B82F6', 'N', '↓ Nord → Sud  (banda x=415)'],
              ['#22C55E', 'S', '↑ Sud → Nord  (banda x=385)'],
              ['#F59E0B', 'E', '← Est → Vest  (banda y=415)'],
              ['#A78BFA', 'V', '→ Vest → Est  (banda y=385)'],
            ].map(([col, dir, desc]) => (
              <div key={dir} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: col, flexShrink: 0 }} />
                <span style={{ color: col, fontSize: 11, fontWeight: 700, minWidth: 14 }}>{dir}</span>
                <span style={{ color: '#6B7280', fontSize: 10 }}>{desc}</span>
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
    background: '#111827', color: '#fff',
    borderRadius: 8, height: '100%',
    fontFamily: 'monospace', overflow: 'hidden',
  },
  tabBar: {
    display: 'flex', borderBottom: '1px solid #1F2937', flexShrink: 0,
  },
  tabBtn: {
    flex: 1, padding: '8px 2px', border: 'none', cursor: 'pointer',
    fontFamily: 'monospace', fontSize: 9, fontWeight: 700,
    letterSpacing: 0.5, transition: 'all 0.15s',
  },
  body: { flex: 1, overflowY: 'auto', padding: 14 },
  section: { display: 'flex', flexDirection: 'column', gap: 10 },
  label: { fontSize: 10, color: '#6B7280', letterSpacing: 2, textTransform: 'uppercase' },
  sep:   { height: 1, background: '#1F2937' },
  hint:  { fontSize: 10, color: '#6B7280', margin: 0, lineHeight: 1.4 },
  simBtn: {
    padding: '11px 0', border: '2px solid', borderRadius: 8,
    fontFamily: 'monospace', fontWeight: 900, fontSize: 14, letterSpacing: 1,
    transition: 'all 0.2s',
  },
  bigBtn: {
    padding: '11px 14px', border: '2px solid', borderRadius: 8,
    fontFamily: 'monospace', fontWeight: 900, fontSize: 13, letterSpacing: 1,
    cursor: 'pointer', width: '100%', transition: 'all 0.2s',
  },
  scenCard: {
    display: 'flex', alignItems: 'center', gap: 10,
    padding: '10px 12px', border: '2px solid', borderRadius: 8,
    cursor: 'pointer', transition: 'all 0.15s',
  },
};

export default ControlPanel;
