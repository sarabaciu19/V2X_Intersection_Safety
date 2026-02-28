import React, { useState, useEffect } from 'react';
const DIRECTION_INFO = {
  N: { label: 'Nord → Sud', icon: '↓', color: '#3B82F6', desc: 'Intră din sus, merge în jos' },
  S: { label: 'Sud → Nord', icon: '↑', color: '#22C55E', desc: 'Intră din jos, merge în sus' },
  E: { label: 'Est → Vest', icon: '←', color: '#F59E0B', desc: 'Intră din dreapta, merge spre stânga' },
  V: { label: 'Vest → Est', icon: '→', color: '#A78BFA', desc: 'Intră din stânga, merge spre dreapta' },
};
const INTENT_INFO = {
  straight: { label: 'Înainte', icon: '↑' },
  left:     { label: 'Stânga',  icon: '↰' },
  right:    { label: 'Dreapta', icon: '↱' },
};
const KMH_BASE   = 50;
const kmhToMult  = (kmh) => Math.max(0.1, +(kmh / KMH_BASE).toFixed(3));
const multToKmh  = (m)   => Math.max(1, Math.round(m * KMH_BASE));
const LS_KEY     = 'v2x_saved_scenarios';
const loadSaved  = () => { try { return JSON.parse(localStorage.getItem(LS_KEY) || '{}'); } catch { return {}; } };
const saveToDisk = (obj) => localStorage.setItem(LS_KEY, JSON.stringify(obj));
const DEFAULT_FORM = { id: '', direction: 'N', intent: 'straight', priority: 'normal', speed_kmh: 50 };
/* ── Sub-componente ──────────────────────────────────────────────────── */
const Tag = ({ label, value, color = '#6B7280' }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
    <span style={{ color: '#4B5563', fontSize: 8, textTransform: 'uppercase' }}>{label}</span>
    <span style={{ color, fontSize: 10, fontWeight: 700 }}>{value}</span>
  </div>
);
/* ── Stiluri ─────────────────────────────────────────────────────────── */
const s = {
  container:   { display: 'flex', flexDirection: 'column', gap: 10, background: '#111827', color: '#fff', padding: 16, borderRadius: 8, fontFamily: 'monospace', overflowY: 'auto', maxHeight: '100%' },
  title:       { fontSize: 15, fontWeight: 900, color: '#F9FAFB', borderBottom: '1px solid #374151', paddingBottom: 8 },
  label:       { fontSize: 10, color: '#6B7280', letterSpacing: 2, textTransform: 'uppercase' },
  sep:         { height: 1, background: '#1F2937', margin: '2px 0' },
  vehicleCard: { background: '#1F2937', border: '1px solid', borderRadius: 8, padding: '8px 10px' },
  fieldLabel:  { color: '#6B7280', fontSize: 9, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 3 },
  input:       { width: '100%', boxSizing: 'border-box', background: '#0F172A', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#F9FAFB', fontFamily: 'monospace', fontSize: 12, outline: 'none' },
  select:      { width: '100%', background: '#0F172A', border: '1px solid #374151', borderRadius: 6, padding: '6px 8px', color: '#F9FAFB', fontFamily: 'monospace', fontSize: 11 },
  dirBtn:      { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, padding: '6px 4px', border: '2px solid', borderRadius: 8, cursor: 'pointer', fontFamily: 'monospace', transition: 'all 0.15s' },
  intentBtn:   { flex: 1, padding: '6px 4px', border: '1px solid', borderRadius: 6, cursor: 'pointer', fontFamily: 'monospace', fontSize: 11, fontWeight: 700 },
  iconBtn:     { background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, padding: '0 4px' },
  saveBtn:     { padding: '7px', background: '#1E3A5F', border: '1px solid #3B82F6', borderRadius: 6, color: '#93C5FD', fontFamily: 'monospace', fontSize: 11, fontWeight: 700, cursor: 'pointer' },
  addBtn:      { padding: '10px', background: '#14532D', border: '1px solid #22C55E', borderRadius: 8, color: '#86EFAC', fontFamily: 'monospace', fontSize: 12, fontWeight: 900, cursor: 'pointer', letterSpacing: 1 },
  runBtn:      { padding: '12px', border: '2px solid', borderRadius: 8, color: '#fff', fontFamily: 'monospace', fontSize: 12, fontWeight: 900, cursor: 'pointer', letterSpacing: 1 },
  clearBtn:    { padding: '8px', background: '#1F2937', border: '1px solid #374151', borderRadius: 6, color: '#EF4444', fontFamily: 'monospace', fontSize: 11, cursor: 'pointer' },
  toggleBtn:   { background: 'none', border: '1px solid #374151', borderRadius: 4, color: '#6B7280', fontSize: 9, padding: '2px 6px', cursor: 'pointer', fontFamily: 'monospace' },
  savedBox:    { background: '#0F172A', border: '1px solid #1E293B', borderRadius: 6, padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 },
  savedCard:   { display: 'flex', gap: 8, alignItems: 'flex-start', background: '#1F2937', border: '1px solid #374151', borderRadius: 6, padding: '7px 8px' },
  smallBtn:    { background: 'none', border: '1px solid', borderRadius: 4, fontFamily: 'monospace', fontSize: 10, padding: '3px 7px', cursor: 'pointer', whiteSpace: 'nowrap' },
};
/* ── Componenta principala ───────────────────────────────────────────── */
const CustomScenarioEditor = ({
  customScenario = [],
  onAdd, onRemove, onUpdate, onClear, onRunCustom,
  isCustomActive = false,
}) => {
  const [form,          setForm]          = useState(DEFAULT_FORM);
  const [editId,        setEditId]        = useState(null);
  const [editData,      setEditData]      = useState({});
  const [err,           setErr]           = useState('');
  const [busy,          setBusy]          = useState(false);
  const [savedScenarios,setSavedScenarios]= useState(loadSaved);
  const [saveNameInput, setSaveNameInput] = useState('');
  const [saveErr,       setSaveErr]       = useState('');
  const [showSaved,     setShowSaved]     = useState(false);
  useEffect(() => { saveToDisk(savedScenarios); }, [savedScenarios]);
  /* Salvare scenariu curent */
  const handleSaveScenario = () => {
    setSaveErr('');
    const name = saveNameInput.trim();
    if (!name) { setSaveErr('Introdu un nume'); return; }
    if (customScenario.length === 0) { setSaveErr('Scenariul e gol'); return; }
    setSavedScenarios(prev => ({ ...prev, [name]: { name, vehicles: customScenario, savedAt: new Date().toLocaleString('ro-RO') } }));
    setSaveNameInput('');
    setShowSaved(true);
  };
  /* Incarcare scenariu salvat */
  const handleLoadScenario = async (scenario) => {
    if (busy) return;
    setBusy(true); setErr('');
    try {
      await onClear();
      for (const v of scenario.vehicles) {
        await onAdd({ id: v.id, direction: v.direction, intent: v.intent, priority: v.priority, speed_multiplier: v.speed_multiplier });
      }
    } catch (e) { setErr(e.message || 'Eroare la încărcare'); }
    finally { setBusy(false); }
  };
  const handleDeleteSaved = (name) => {
    setSavedScenarios(prev => { const n = { ...prev }; delete n[name]; return n; });
  };
  /* Handlers vehicule */
  const handleAdd = async () => {
    if (busy) return; setErr('');
    if (!form.id.trim()) { setErr('ID-ul este obligatoriu'); return; }
    if (!/^[A-Za-z0-9_-]+$/.test(form.id)) { setErr('ID doar litere, cifre, _ sau -'); return; }
    if (customScenario.find(v => v.id === form.id.trim())) { setErr(`ID "${form.id}" există deja`); return; }
    setBusy(true);
    try {
      await onAdd({ id: form.id.trim(), direction: form.direction, intent: form.intent, priority: form.priority, speed_multiplier: kmhToMult(form.speed_kmh) });
      setForm({ ...DEFAULT_FORM });
    } catch (e) { setErr(e.message || 'Eroare la adăugare'); }
    finally { setBusy(false); }
  };
  const handleRemove = async (vid) => {
    if (busy) return; setBusy(true);
    try { await onRemove(vid); }
    catch (e) { setErr(e.message || `Eroare la ștergere ${vid}`); }
    finally { setBusy(false); }
  };
  const handleSaveEdit = async (vid) => {
    if (busy) return; setBusy(true);
    const payload = { ...editData };
    if (payload.speed_kmh !== undefined) { payload.speed_multiplier = kmhToMult(payload.speed_kmh); delete payload.speed_kmh; }
    try { await onUpdate(vid, payload); setEditId(null); setEditData({}); }
    catch (e) { setErr(e.message || 'Eroare la modificare'); }
    finally { setBusy(false); }
  };
  const handleClear = async () => {
    if (busy) return; setBusy(true);
    try { await onClear(); }
    catch (e) { setErr(e.message || 'Eroare la golire'); }
    finally { setBusy(false); }
  };
  const handleRunCustom = async () => {
    if (busy) return; setErr('');
    if (customScenario.length === 0) { setErr('Adaugă cel puțin un vehicul'); return; }
    setBusy(true);
    try { await onRunCustom(); }
    catch (e) { setErr(e.message || 'Eroare la pornire'); }
    finally { setBusy(false); }
  };
  const savedList = Object.values(savedScenarios);
  return (
    <div style={s.container}>
      <div style={s.title}>Scenariu Custom</div>
      {/* ── Scenarii salvate ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={s.label}>Scenarii salvate ({savedList.length})</div>
        <button onClick={() => setShowSaved(v => !v)} style={s.toggleBtn}>
          {showSaved ? '▲ Ascunde' : '▼ Arată'}
        </button>
      </div>
      {showSaved && (
        <div style={s.savedBox}>
          {savedList.length === 0 && (
            <div style={{ color: '#4B5563', fontSize: 10, textAlign: 'center', padding: '8px 0' }}>
              Niciun scenariu salvat încă
            </div>
          )}
          {savedList.map(sc => (
            <div key={sc.name} style={s.savedCard}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: '#F9FAFB', fontWeight: 700, fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  💾 {sc.name}
                </div>
                <div style={{ color: '#6B7280', fontSize: 9, marginTop: 1 }}>
                  {sc.vehicles.length} vehicule · {sc.savedAt}
                </div>
                <div style={{ display: 'flex', gap: 4, marginTop: 3, flexWrap: 'wrap' }}>
                  {sc.vehicles.map(v => (
                    <span key={v.id} style={{ background: '#374151', borderRadius: 3, padding: '1px 5px', fontSize: 9, color: v.priority === 'emergency' ? '#EF4444' : '#9CA3AF' }}>
                      {v.id} {DIRECTION_INFO[v.direction]?.icon}
                    </span>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <button onClick={() => handleLoadScenario(sc)} disabled={busy}
                  style={{ ...s.smallBtn, borderColor: '#3B82F6', color: '#93C5FD' }} title="Încarcă">
                  ↓ Încarcă
                </button>
                <button onClick={() => handleDeleteSaved(sc.name)}
                  style={{ ...s.smallBtn, borderColor: '#EF444466', color: '#EF4444' }} title="Șterge">
                  🗑
                </button>
              </div>
            </div>
          ))}
          {/* Salvare */}
          <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div style={s.label}>Salvează scenariul curent</div>
            {saveErr && <div style={{ color: '#F87171', fontSize: 10 }}>⚠ {saveErr}</div>}
            <div style={{ display: 'flex', gap: 4, width: '100%' }}>
              <input
                style={{ ...s.input, flex: 1, fontSize: 11, padding: '5px 8px' }}
                placeholder="Nume scenariu…"
                value={saveNameInput}
                onChange={e => { setSaveNameInput(e.target.value); setSaveErr(''); }}
                onKeyDown={e => e.key === 'Enter' && handleSaveScenario()}
              />
              <button onClick={handleSaveScenario} disabled={customScenario.length === 0}
                style={{ ...s.smallBtn, borderColor: customScenario.length === 0 ? '#374151' : '#22C55E', color: customScenario.length === 0 ? '#4B5563' : '#86EFAC', padding: '5px 10px' }}>
                💾 Salvează
              </button>
            </div>
          </div>
        </div>
      )}
      <div style={s.sep} />
      {/* ── Lista vehicule ── */}
      <div style={s.label}>Vehicule în scenariu</div>
      {customScenario.length === 0 && (
        <div style={{ color: '#4B5563', fontSize: 11, textAlign: 'center', padding: '12px 0' }}>
          Niciun vehicul adăugat încă
        </div>
      )}
      {customScenario.map(v => {
        const dInfo = DIRECTION_INFO[v.direction];
        const isEditing = editId === v.id;
        return (
          <div key={v.id} style={{ ...s.vehicleCard, borderColor: dInfo.color + '66' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {v.priority === 'emergency' && <span style={{ fontSize: 12 }}>🚑</span>}
                <span style={{ color: dInfo.color, fontWeight: 900, fontSize: 14 }}>{v.id}</span>
                <span style={{ color: '#6B7280', fontSize: 10 }}>{dInfo.icon} {dInfo.label}</span>
              </div>
              <div style={{ display: 'flex', gap: 4 }}>
                <button onClick={() => { setEditId(isEditing ? null : v.id); setEditData({}); }}
                  style={{ ...s.iconBtn, color: isEditing ? '#FBBF24' : '#6B7280' }}>✏</button>
                <button onClick={() => handleRemove(v.id)} disabled={busy}
                  style={{ ...s.iconBtn, color: busy ? '#4B5563' : '#EF4444' }}>✕</button>
              </div>
            </div>
            {!isEditing && (
              <div style={{ display: 'flex', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
                <Tag label="intent" value={INTENT_INFO[v.intent]?.icon + ' ' + v.intent} />
                <Tag label="viteză" value={`${multToKmh(v.speed_multiplier)} km/h`} />
                <Tag label="tip" value={v.priority} color={v.priority === 'emergency' ? '#EF4444' : '#6B7280'} />
              </div>
            )}
            {isEditing && (
              <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  <div>
                    <div style={s.fieldLabel}>Intenție</div>
                    <select style={s.select} value={editData.intent ?? v.intent}
                      onChange={e => setEditData(d => ({ ...d, intent: e.target.value }))}>
                      {Object.entries(INTENT_INFO).map(([k, i]) => <option key={k} value={k}>{i.icon} {i.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <div style={s.fieldLabel}>Prioritate</div>
                    <select style={s.select} value={editData.priority ?? v.priority}
                      onChange={e => setEditData(d => ({ ...d, priority: e.target.value }))}>
                      <option value="normal">Normal</option>
                      <option value="emergency">Urgență</option>
                    </select>
                  </div>
                </div>
                <div>
                  {(() => {
                    const currentKmh = editData.speed_kmh ?? multToKmh(v.speed_multiplier);
                    return (<>
                      <div style={s.fieldLabel}>Viteză: <strong style={{ color: '#F9FAFB' }}>{currentKmh} km/h</strong></div>
                      <input type="range" min="10" max="120" step="5"
                        style={{ width: '100%', accentColor: dInfo.color }} value={currentKmh}
                        onChange={e => setEditData(d => ({ ...d, speed_kmh: parseInt(e.target.value) }))} />
                    </>);
                  })()}
                </div>
                <button onClick={() => handleSaveEdit(v.id)} style={s.saveBtn}>💾 Salvează modificările</button>
              </div>
            )}
          </div>
        );
      })}
      <div style={s.sep} />
      {/* ── Formular adăugare ── */}
      <div style={s.label}>Adaugă vehicul nou</div>
      {err && (
        <div style={{ background: '#EF444422', border: '1px solid #EF4444', borderRadius: 6, padding: '6px 10px', color: '#F87171', fontSize: 11, marginBottom: 6 }}>
          ⚠ {err}
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div>
          <div style={s.fieldLabel}>Nume vehicul *</div>
          <input style={s.input} placeholder="ex: A, CAR1, AMB2" value={form.id}
            onChange={e => { setForm(f => ({ ...f, id: e.target.value })); setErr(''); }} />
        </div>
        <div>
          <div style={s.fieldLabel}>Direcție de deplasare *</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
            {Object.entries(DIRECTION_INFO).map(([dir, info]) => (
              <button key={dir} onClick={() => setForm(f => ({ ...f, direction: dir }))}
                style={{ ...s.dirBtn, background: form.direction === dir ? info.color + '33' : '#1F2937', borderColor: form.direction === dir ? info.color : '#374151', color: form.direction === dir ? info.color : '#9CA3AF' }}>
                <span style={{ fontSize: 16 }}>{info.icon}</span>
                <span style={{ fontSize: 10 }}>{info.label}</span>
                <span style={{ fontSize: 9, color: '#6B7280' }}>{info.desc}</span>
              </button>
            ))}
          </div>
        </div>
        <div>
          <div style={s.fieldLabel}>Viraj</div>
          <div style={{ display: 'flex', gap: 4 }}>
            {Object.entries(INTENT_INFO).map(([k, i]) => (
              <button key={k} onClick={() => setForm(f => ({ ...f, intent: k }))}
                style={{ ...s.intentBtn, background: form.intent === k ? '#3B82F644' : '#1F2937', borderColor: form.intent === k ? '#3B82F6' : '#374151', color: form.intent === k ? '#93C5FD' : '#6B7280' }}>
                {i.icon} {i.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div style={s.fieldLabel}>Tip vehicul</div>
          <div style={{ display: 'flex', gap: 4 }}>
            {[['normal', '🚗 Normal', '#6B7280'], ['emergency', '🚑 Urgență', '#EF4444']].map(([k, l, c]) => (
              <button key={k} onClick={() => setForm(f => ({ ...f, priority: k }))}
                style={{ ...s.intentBtn, flex: 1, background: form.priority === k ? c + '22' : '#1F2937', borderColor: form.priority === k ? c : '#374151', color: form.priority === k ? c : '#6B7280' }}>
                {l}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div style={s.fieldLabel}>Viteză: <strong style={{ color: '#F9FAFB' }}>{form.speed_kmh} km/h</strong></div>
          <input type="range" min="10" max="120" step="5"
            style={{ width: '100%', accentColor: DIRECTION_INFO[form.direction].color }}
            value={form.speed_kmh}
            onChange={e => setForm(f => ({ ...f, speed_kmh: parseInt(e.target.value) }))} />
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#4B5563', fontSize: 9 }}>
            <span>10 km/h</span><span>50 km/h</span><span>120 km/h</span>
          </div>
        </div>
        <button onClick={handleAdd} disabled={busy} style={{ ...s.addBtn, opacity: busy ? 0.5 : 1 }}>
          {busy ? '⏳ Se procesează…' : '➕ Adaugă vehicul'}
        </button>
      </div>
      <div style={s.sep} />
      {/* ── Acțiuni scenariu ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <button onClick={handleRunCustom} disabled={customScenario.length === 0 || busy}
          style={{ ...s.runBtn, opacity: (customScenario.length === 0 || busy) ? 0.4 : 1, cursor: (customScenario.length === 0 || busy) ? 'not-allowed' : 'pointer', background: isCustomActive ? '#065F46' : '#1E3A5F', borderColor: isCustomActive ? '#10B981' : '#3B82F6' }}>
          {busy ? 'Se procesează…' : isCustomActive ? '🔄 Restart scenariu custom' : '▶ Rulează'}
        </button>
        <button onClick={handleClear} disabled={customScenario.length === 0 || busy}
          style={{ ...s.clearBtn, opacity: (customScenario.length === 0 || busy) ? 0.4 : 1 }}>
          🗑 Golește scenariul
        </button>
      </div>
    </div>
  );
};
export default CustomScenarioEditor;
