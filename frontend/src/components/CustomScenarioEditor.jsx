import React, { useState } from 'react';

// Benzile corecte per directie (sens unic)
// N: vine din Nord, merge spre Sud → banda dreapta = x=415
// S: vine din Sud, merge spre Nord → banda dreapta = x=385
// E: vine din Est,  merge spre Vest → banda dreapta = y=415
// V: vine din Vest, merge spre Est  → banda dreapta = y=385
const DIRECTION_INFO = {
  N: { label: 'Nord → Sud',  icon: '↓', color: '#3B82F6', banda: 'banda dreapta (x=415)', desc: 'Intră din sus, merge în jos' },
  S: { label: 'Sud → Nord',  icon: '↑', color: '#22C55E', banda: 'banda dreapta (x=385)', desc: 'Intră din jos, merge în sus' },
  E: { label: 'Est → Vest',  icon: '←', color: '#F59E0B', banda: 'banda dreapta (y=415)', desc: 'Intră din dreapta, merge spre stânga' },
  V: { label: 'Vest → Est',  icon: '→', color: '#A78BFA', banda: 'banda dreapta (y=385)', desc: 'Intră din stânga, merge spre dreapta' },
};

const INTENT_INFO = {
  straight: { label: 'Înainte',  icon: '↑' },
  left:     { label: 'Stânga',   icon: '↰' },
  right:    { label: 'Dreapta',  icon: '↱' },
};

const DEFAULT_FORM = {
  id: '',
  direction: 'N',
  intent: 'straight',
  priority: 'normal',
  speed_multiplier: 1.0,
};

const CustomScenarioEditor = ({
  customScenario = [],
  onAdd,
  onRemove,
  onUpdate,
  onClear,
  onRunCustom,
  isCustomActive = false,
}) => {
  const [form, setForm]         = useState(DEFAULT_FORM);
  const [editId, setEditId]     = useState(null);
  const [editData, setEditData] = useState({});
  const [err, setErr]           = useState('');

  // ── Validare ID ────────────────────────────────────────────────
  const usedDirections = customScenario.map(v => v.direction);

  const handleAdd = async () => {
    setErr('');
    if (!form.id.trim()) { setErr('ID-ul este obligatoriu'); return; }
    if (!/^[A-Za-z0-9_-]+$/.test(form.id)) { setErr('ID doar litere, cifre, _ sau -'); return; }
    if (customScenario.find(v => v.id === form.id.trim())) { setErr(`ID "${form.id}" există deja`); return; }
    try {
      await onAdd({ ...form, id: form.id.trim() });
      setForm(f => ({ ...DEFAULT_FORM }));
      setErr('');
    } catch (e) {
      setErr(e.message || 'Eroare la adăugare');
    }
  };

  const handleRemove = async (vid) => {
    setErr('');
    try {
      await onRemove(vid);
    } catch (e) {
      setErr(e.message || `Eroare la ștergere ${vid}`);
    }
  };

  const handleSaveEdit = async (vid) => {
    setErr('');
    try {
      await onUpdate(vid, editData);
      setEditId(null);
      setEditData({});
    } catch (e) {
      setErr(e.message || 'Eroare la modificare');
    }
  };

  const handleClear = async () => {
    setErr('');
    try {
      await onClear();
    } catch (e) {
      setErr(e.message || 'Eroare la golire');
    }
  };

  const handleRunCustom = async () => {
    setErr('');
    if (customScenario.length === 0) { setErr('Adaugă cel puțin un vehicul'); return; }
    try {
      await onRunCustom();
    } catch (e) {
      setErr(e.message || 'Eroare la pornire');
    }
  };

  return (
    <div style={s.container}>
      <div style={s.title}>🛠 Scenariu Custom</div>

      {/* Harta benzi */}
      <div style={s.laneMap}>
        <div style={s.laneMapTitle}>Benzi disponibile (sens unic)</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
          {Object.entries(DIRECTION_INFO).map(([dir, info]) => (
            <div key={dir} style={{
              ...s.laneCard,
              borderColor: usedDirections.includes(dir) ? info.color : '#c8b89a',
              opacity: usedDirections.includes(dir) ? 1 : 0.5,
            }}>
              <span style={{ color: info.color, fontSize: 18 }}>{info.icon}</span>
              <div>
                <div style={{ color: '#2c1e0f', fontSize: 10, fontWeight: 700 }}>{info.label}</div>
                <div style={{ color: '#a08060', fontSize: 9 }}>{info.banda}</div>
              </div>
              {usedDirections.includes(dir) && (
                <span style={{ color: info.color, fontSize: 9, fontWeight: 700 }}>✓ ocupat</span>
              )}
            </div>
          ))}
        </div>
        <div style={{ color: '#a08060', fontSize: 9, marginTop: 4 }}>
          ⚠ Fiecare direcție are o singură bandă de intrare — sens unic.
        </div>
      </div>

      <div style={s.sep} />

      {/* Lista vehicule existente */}
      <div style={s.label}>Vehicule în scenariu ({customScenario.length})</div>

      {customScenario.length === 0 && (
        <div style={{ color: '#a08060', fontSize: 11, textAlign: 'center', padding: '12px 0' }}>
          Niciun vehicul adăugat încă
        </div>
      )}

      {customScenario.map(v => {
        const dInfo = DIRECTION_INFO[v.direction];
        const isEditing = editId === v.id;
        return (
          <div key={v.id} style={{ ...s.vehicleCard, borderColor: dInfo.color + '66' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {v.priority === 'emergency' && <span style={{ fontSize: 12 }}>🚑</span>}
                <span style={{ color: dInfo.color, fontWeight: 900, fontSize: 14 }}>{v.id}</span>
                <span style={{ color: '#a08060', fontSize: 10 }}>
                  {dInfo.icon} {dInfo.label}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 4 }}>
                <button onClick={() => { setEditId(isEditing ? null : v.id); setEditData({}); }}
                  style={{ ...s.iconBtn, color: isEditing ? '#b45309' : '#a08060' }}>✏</button>
                <button onClick={() => handleRemove(v.id)}
                  style={{ ...s.iconBtn, color: '#b91c1c' }}>✕</button>
              </div>
            </div>

            {/* Info compact */}
            {!isEditing && (
              <div style={{ display: 'flex', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
                <Tag label="intent" value={INTENT_INFO[v.intent]?.icon + ' ' + v.intent} />
                <Tag label="viteză" value={`×${v.speed_multiplier}`} />
                <Tag label="tip" value={v.priority} color={v.priority === 'emergency' ? '#b91c1c' : '#a08060'} />
              </div>
            )}

            {/* Edit inline */}
            {isEditing && (
              <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  <div>
                    <div style={s.fieldLabel}>Intenție</div>
                    <select style={s.select}
                      value={editData.intent ?? v.intent}
                      onChange={e => setEditData(d => ({ ...d, intent: e.target.value }))}>
                      {Object.entries(INTENT_INFO).map(([k, i]) =>
                        <option key={k} value={k}>{i.icon} {i.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <div style={s.fieldLabel}>Prioritate</div>
                    <select style={s.select}
                      value={editData.priority ?? v.priority}
                      onChange={e => setEditData(d => ({ ...d, priority: e.target.value }))}>
                      <option value="normal">Normal</option>
                      <option value="emergency">🚑 Urgență</option>
                    </select>
                  </div>
                </div>
                <div>
                  <div style={s.fieldLabel}>
                    Viteză: ×{(editData.speed_multiplier ?? v.speed_multiplier).toFixed(1)}
                    <span style={{ color: '#a08060', marginLeft: 6 }}>
                      ({editData.speed_multiplier ?? v.speed_multiplier >= 2 ? '🔴 rapid' :
                        editData.speed_multiplier ?? v.speed_multiplier <= 0.5 ? '🐢 lent' : '🟢 normal'})
                    </span>
                  </div>
                  <input type="range" min="0.2" max="3.0" step="0.1"
                    style={{ width: '100%', accentColor: dInfo.color }}
                    value={editData.speed_multiplier ?? v.speed_multiplier}
                    onChange={e => setEditData(d => ({ ...d, speed_multiplier: parseFloat(e.target.value) }))} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#a08060', fontSize: 9 }}>
                    <span>×0.2 lent</span><span>×1.0 normal</span><span>×3.0 rapid</span>
                  </div>
                </div>
                <button onClick={() => handleSaveEdit(v.id)} style={s.saveBtn}>
                  💾 Salvează modificările
                </button>
              </div>
            )}
          </div>
        );
      })}

      <div style={s.sep} />

      {/* Formular adăugare */}
      <div style={s.label}>➕ Adaugă vehicul nou</div>

      {err && (
        <div style={{ background: '#fde8e8', border: '1px solid #b91c1c', borderRadius: 6,
          padding: '6px 10px', color: '#7f1d1d', fontSize: 11, marginBottom: 6 }}>
          ⚠ {err}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {/* ID */}
        <div>
          <div style={s.fieldLabel}>ID vehicul *</div>
          <input style={s.input} placeholder="ex: A, CAR1, AMB2"
            value={form.id}
            onChange={e => { setForm(f => ({ ...f, id: e.target.value })); setErr(''); }} />
        </div>

        {/* Directie */}
        <div>
          <div style={s.fieldLabel}>Direcție de intrare *</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
            {Object.entries(DIRECTION_INFO).map(([dir, info]) => (
              <button key={dir}
                onClick={() => setForm(f => ({ ...f, direction: dir }))}
                style={{
                  ...s.dirBtn,
                  background:  form.direction === dir ? info.color + '22' : '#e6ddd0',
                  borderColor: form.direction === dir ? info.color : '#c8b89a',
                  color:       form.direction === dir ? info.color : '#6b4f35',
                }}>
                <span style={{ fontSize: 16 }}>{info.icon}</span>
                <span style={{ fontSize: 10 }}>{info.label}</span>
                <span style={{ fontSize: 9, color: '#a08060' }}>{info.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Intentie */}
        <div>
          <div style={s.fieldLabel}>Intenție la intersecție</div>
          <div style={{ display: 'flex', gap: 4 }}>
            {Object.entries(INTENT_INFO).map(([k, i]) => (
              <button key={k} onClick={() => setForm(f => ({ ...f, intent: k }))}
                style={{
                  ...s.intentBtn,
                  background:  form.intent === k ? '#ddd0c0' : '#e6ddd0',
                  borderColor: form.intent === k ? '#7c5c38' : '#c8b89a',
                  color:       form.intent === k ? '#2c1e0f' : '#a08060',
                }}>
                {i.icon} {i.label}
              </button>
            ))}
          </div>
        </div>

        {/* Prioritate */}
        <div>
          <div style={s.fieldLabel}>Tip vehicul</div>
          <div style={{ display: 'flex', gap: 4 }}>
            {[['normal','🚗 Normal','#6b4f35'],['emergency','🚑 Urgență','#b91c1c']].map(([k,l,c]) => (
              <button key={k} onClick={() => setForm(f => ({ ...f, priority: k }))}
                style={{
                  ...s.intentBtn, flex: 1,
                  background:  form.priority === k ? c + '15' : '#e6ddd0',
                  borderColor: form.priority === k ? c : '#c8b89a',
                  color:       form.priority === k ? c : '#a08060',
                }}>
                {l}
              </button>
            ))}
          </div>
        </div>

        {/* Viteza */}
        <div>
          <div style={s.fieldLabel}>
            Viteză: ×{form.speed_multiplier.toFixed(1)}
            <span style={{ color: '#a08060', marginLeft: 6, fontSize: 9 }}>
              {form.speed_multiplier >= 2 ? '🔴 rapid' : form.speed_multiplier <= 0.5 ? '🐢 lent' : '🟢 normal'}
            </span>
          </div>
          <input type="range" min="0.2" max="3.0" step="0.1"
            style={{ width: '100%', accentColor: DIRECTION_INFO[form.direction].color }}
            value={form.speed_multiplier}
            onChange={e => setForm(f => ({ ...f, speed_multiplier: parseFloat(e.target.value) }))} />
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#a08060', fontSize: 9 }}>
            <span>×0.2 lent</span><span>×1.0 normal</span><span>×3.0 rapid</span>
          </div>
        </div>

        <button onClick={handleAdd} style={s.addBtn}>
          ➕ Adaugă vehicul
        </button>
      </div>

      <div style={s.sep} />

      {/* Actiuni scenariu */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <button
          onClick={handleRunCustom}
          disabled={customScenario.length === 0}
          style={{
            ...s.runBtn,
            opacity: customScenario.length === 0 ? 0.4 : 1,
            cursor:  customScenario.length === 0 ? 'not-allowed' : 'pointer',
            background:  isCustomActive ? '#3a8a3a' : '#7c5c38',
            borderColor: isCustomActive ? '#166534' : '#5c4028',
          }}>
          {isCustomActive ? '🔄 Restart scenariu custom' : '▶ Rulează scenariu custom'}
        </button>
        <button onClick={handleClear} style={{ ...s.clearBtn }}
          disabled={customScenario.length === 0}>
          🗑 Golește scenariul
        </button>
      </div>
    </div>
  );
};

const Tag = ({ label, value, color = '#a08060' }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
    <span style={{ color: '#c8b89a', fontSize: 8, textTransform: 'uppercase' }}>{label}</span>
    <span style={{ color, fontSize: 10, fontWeight: 700 }}>{value}</span>
  </div>
);

const s = {
  container: {
    display: 'flex', flexDirection: 'column', gap: 10,
    background: '#ede5d8', color: '#2c1e0f',
    padding: 16, borderRadius: 8,
    fontFamily: "'Inter','Segoe UI',sans-serif", overflowY: 'auto',
    maxHeight: '100%',
  },
  title:        { fontSize: 15, fontWeight: 900, color: '#2c1e0f', borderBottom: '1px solid #c8b89a', paddingBottom: 8 },
  label:        { fontSize: 10, color: '#a08060', letterSpacing: 2, textTransform: 'uppercase' },
  sep:          { height: 1, background: '#c8b89a', margin: '2px 0' },
  laneMap:      { background: '#faf7f2', border: '1px solid #c8b89a', borderRadius: 6, padding: 8 },
  laneMapTitle: { color: '#a08060', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 6 },
  laneCard: {
    display: 'flex', alignItems: 'center', gap: 6,
    background: '#e6ddd0', border: '1px solid', borderRadius: 4, padding: '4px 6px',
  },
  vehicleCard: {
    background: '#e6ddd0', border: '1px solid', borderRadius: 8, padding: '8px 10px',
  },
  fieldLabel: { color: '#a08060', fontSize: 9, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 3 },
  input: {
    width: '100%', boxSizing: 'border-box',
    background: '#faf7f2', border: '1px solid #c8b89a', borderRadius: 6,
    padding: '7px 10px', color: '#2c1e0f',
    fontFamily: "'JetBrains Mono',monospace", fontSize: 12, outline: 'none',
  },
  select: {
    width: '100%', background: '#faf7f2', border: '1px solid #c8b89a', borderRadius: 6,
    padding: '6px 8px', color: '#2c1e0f',
    fontFamily: "'JetBrains Mono',monospace", fontSize: 11,
  },
  dirBtn: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
    padding: '6px 4px', border: '2px solid', borderRadius: 8, cursor: 'pointer',
    fontFamily: "'JetBrains Mono',monospace", transition: 'all 0.15s',
  },
  intentBtn: {
    flex: 1, padding: '6px 4px', border: '1px solid', borderRadius: 6,
    cursor: 'pointer', fontFamily: "'JetBrains Mono',monospace", fontSize: 11, fontWeight: 700,
  },
  iconBtn: {
    background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, padding: '0 4px',
  },
  saveBtn: {
    padding: '7px', background: '#e6ddd0', border: '1px solid #7c5c38',
    borderRadius: 6, color: '#5c4028',
    fontFamily: "'JetBrains Mono',monospace", fontSize: 11, fontWeight: 700, cursor: 'pointer',
  },
  addBtn: {
    padding: '10px', background: '#deeede', border: '1px solid #3a8a3a',
    borderRadius: 8, color: '#1a5a1a',
    fontFamily: "'JetBrains Mono',monospace", fontSize: 12, fontWeight: 900, cursor: 'pointer', letterSpacing: 1,
  },
  runBtn: {
    padding: '12px', border: '2px solid', borderRadius: 8,
    color: '#faf7f2', fontFamily: "'JetBrains Mono',monospace", fontSize: 12, fontWeight: 900,
    cursor: 'pointer', letterSpacing: 1,
  },
  clearBtn: {
    padding: '8px', background: '#faf7f2', border: '1px solid #c8b89a',
    borderRadius: 6, color: '#b91c1c',
    fontFamily: "'JetBrains Mono',monospace", fontSize: 11, cursor: 'pointer',
  },
};

export default CustomScenarioEditor;
