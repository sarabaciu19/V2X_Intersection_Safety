import React from 'react';

const STATE_COLOR = {
  moving:   '#2563eb',
  waiting:  '#b45309',
  crossing: '#166534',
  done:     '#a08060',
};

const INTENT_LABEL = { straight: '↑ Înainte', left: '← Stânga', right: '→ Dreapta' };
const DIR_LABEL    = { N: '↓ Nord→Sud', S: '↑ Sud→Nord', E: '← Est→Vest', V: '→ Vest→Est' };

/**
 * Dashboard - Panoul principal cu informații despre trafic și vehicule
 *
 * Specificații:
 * - Direcție vehicul: Nord, Sud, Est, Vest
 * - Intenție vehicul: Dreapta, Stânga, Înainte
 * - Stare vehicul: În mișcare, Așteptând, Traversând, Finalizat
 * - Status clearance: liber / stop
 * - Semafor: stare (verde, galben, roșu) și urgență
 * - Sumar intersecție: număr total vehicule, număr vehicule în așteptare, număr vehicule traversând
 * - Design: aspect întunecat, text alb, organizat pe secțiuni
 */
const Dashboard = ({ vehicles = [], semaphore = {}, cooperation = true, agentsMemory = {}, onGrantClearance = null }) => {
  const waiting  = vehicles.filter(v => v.state === 'waiting').length;
  const crossing = vehicles.filter(v => v.state === 'crossing').length;

  return (
    <div style={s.container}>
      <div style={s.title}>📊 Dashboard</div>

      {/* Sistem central status */}
      <section style={s.section}>
        <div style={s.label}>Sistem Central</div>
        <div style={{
          ...s.badge,
          background:  cooperation ? '#deeede' : '#f5e8d0',
          borderColor: cooperation ? '#3a8a3a' : '#b45309',
          color:       cooperation ? '#1a5a1a' : '#7c3a00',
        }}>
          {cooperation ? '✓ AUTO — sistemul central decide' : '✋ MANUAL — tu decizi cine trece'}
        </div>
        {!cooperation && (
          <p style={{ color: '#6b4f35', fontSize: 11, margin: 0 }}>
            Click pe un vehicul portocaliu din canvas, sau apasă butonul de mai jos.
          </p>
        )}
      </section>

      {/* Semafor */}
      <section style={s.section}>
        <div style={s.label}>
          Semafoare V2I
          {semaphore.emergency && (
            <span style={{ marginLeft: 8, color: '#b91c1c', fontSize: 11, fontWeight: 700 }}>🚑 URGENȚĂ</span>
          )}
        </div>

        {/* Grid 2×2: N sus-stânga, V sus-dreapta, S jos-stânga, E jos-dreapta */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
          {[
            { dir: 'N', label: '↓ Nord→Sud' },
            { dir: 'V', label: '→ Vest→Est' },
            { dir: 'S', label: '↑ Sud→Nord' },
            { dir: 'E', label: '← Est→Vest' },
          ].map(({ dir, label }) => {
            const lights = semaphore.lights || {};
            const lc = lights[dir] || 'red';
            const bg   = lc === 'green' ? '#16a34a' : lc === 'yellow' ? '#ca8a04' : '#dc2626';
            const glow = lc === 'green' ? 'rgba(22,163,74,0.4)'
                       : lc === 'yellow' ? 'rgba(202,138,4,0.4)' : 'rgba(220,38,38,0.4)';
            const txt  = lc === 'green' ? 'Verde' : lc === 'yellow' ? 'Galben' : 'Roșu';
            return (
              <div key={dir} style={{
                display: 'flex', alignItems: 'center', gap: 7,
                background: '#e6ddd0', borderRadius: 6, padding: '6px 8px',
                border: `1px solid ${bg}44`,
              }}>
                <div style={{
                  width: 14, height: 14, borderRadius: '50%', flexShrink: 0,
                  background: bg, boxShadow: `0 0 7px ${glow}`,
                }} />
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: 9, color: '#a08060', fontWeight: 700 }}>{dir}</span>
                  <span style={{ fontSize: 10, color: '#2c1e0f' }}>{txt}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Legenda faze */}
        <div style={{ fontSize: 10, color: '#a08060', marginTop: 2 }}>
          Faza A: N/S verde · Faza B: E/V verde · Galben = tranziție
        </div>
      </section>

      {/* Sumar */}
      <section style={s.section}>
        <div style={s.label}>Sumar intersecție</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
          {[
            { val: vehicles.length, label: 'total',       col: '#6b4f35' },
            { val: waiting,         label: 'așteaptă',    col: '#b45309' },
            { val: crossing,        label: 'traversează', col: '#166534' },
          ].map(({ val, label, col }) => (
            <div key={label} style={{ ...s.stat, borderColor: col }}>
              <span style={{ fontSize: 22, fontWeight: 900, color: col }}>{val}</span>
              <span style={{ fontSize: 9, color: '#a08060' }}>{label}</span>
            </div>
          ))}
        </div>
      </section>

      <div style={s.sep} />

      {/* Vehicule */}
      <section style={s.section}>
        <div style={s.label}>Vehicule ({vehicles.length})</div>
        {vehicles.length === 0 && (
          <p style={{ color: '#a08060', fontSize: 12, textAlign: 'center', padding: '16px 0' }}>
            Niciun vehicul activ
          </p>
        )}
        {vehicles.map(v => {
          const col = v.priority === 'emergency' ? '#b91c1c' : (STATE_COLOR[v.state] || '#2563eb');
          return (
            <div key={v.id} style={{ ...s.card, borderColor: col + '66' }}>
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {v.priority === 'emergency' && <span>🚑</span>}
                  <span style={{ color: '#2c1e0f', fontWeight: 700, fontSize: 14 }}>{v.id}</span>
                  <span style={{ ...s.pill, background: col + '22', color: col }}>
                    {v.state}
                  </span>
                </div>
                <span style={{ ...s.pill, background: '#e6ddd0', color: '#a08060', fontSize: 10 }}>
                  {v.clearance ? '🟢 clearance' : '🔴 stop'}
                </span>
              </div>

              {/* Detalii */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px', marginTop: 6 }}>
                <Row label="Direcție" value={DIR_LABEL[v.direction] || v.direction} />
                <Row label="Intenție" value={INTENT_LABEL[v.intent] || v.intent} />
                <Row label="Distanță" value={`${v.dist_to_intersection ?? '—'}px`} />
                <Row label="Viteză"   value={v.speed_kmh != null ? `${v.speed_kmh} km/h` : `${Math.round(Math.sqrt((v.vx||0)**2+(v.vy||0)**2)*30/90*50)} km/h`} />
              </div>

              {/* Buton manual clearance — doar în modul manual și când vehiculul așteaptă */}
              {onGrantClearance && v.state === 'waiting' && (
                <button
                  onClick={() => onGrantClearance(v.id)}
                  style={{
                    marginTop: 8, width: '100%',
                    padding: '7px 0', border: '2px solid #b45309', borderRadius: 6,
                    background: '#f5e8d0', color: '#7c3a00',
                    fontFamily: "'JetBrains Mono',monospace", fontWeight: 900, fontSize: 12,
                    cursor: 'pointer', letterSpacing: 1,
                  }}
                >
                  ✅ ACORDĂ CLEARANCE → {v.id}
                </button>
              )}
            </div>
          );
        })}
      </section>

      {/* Memoria agentilor autonomi */}
      {Object.keys(agentsMemory).length > 0 && (
        <>
          <div style={s.sep} />
          <section style={s.section}>
            <div style={s.label}>🧠 Memorie agenți (ultimele 10 decizii)</div>
            {Object.entries(agentsMemory).map(([vid, mem]) => {
              if (!mem || mem.length === 0) return null;
              const last = mem[mem.length - 1];
              const actionColor =
                last.action === 'YIELD' ? '#b91c1c'
                : last.action === 'BRAKE' ? '#b45309'
                : '#166534';
              return (
                <div key={vid} style={{ ...s.card, borderColor: actionColor + '55', padding: '8px 10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontWeight: 700, fontSize: 13, color: '#2c1e0f' }}>{vid}</span>
                    <span style={{ ...s.pill, background: actionColor + '22', color: actionColor }}>
                      {last.action}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {mem.slice(-10).map((m, i) => {
                      const c = m.action === 'YIELD' ? '#b91c1c'
                              : m.action === 'BRAKE' ? '#b45309'
                              : '#166534';
                      return (
                        <span key={i} title={`${m.action} TTC=${m.ttc}s ${m.reason}`}
                          style={{
                            width: 14, height: 14, borderRadius: 3,
                            background: c + '33', border: `1px solid ${c}`,
                            display: 'inline-block', cursor: 'default',
                            fontSize: 8, color: c, textAlign: 'center', lineHeight: '14px',
                          }}>
                          {m.action[0]}
                        </span>
                      );
                    })}
                  </div>
                  <div style={{ fontSize: 9, color: '#a08060', marginTop: 3 }}>
                    {last.reason} · TTC={last.ttc}s
                  </div>
                </div>
              );
            })}
          </section>
        </>
      )}
    </div>
  );
};

const Row = ({ label, value }) => (
  <div style={{ display: 'flex', flexDirection: 'column' }}>
    <span style={{ fontSize: 9, color: '#a08060', textTransform: 'uppercase', letterSpacing: 1 }}>{label}</span>
    <span style={{ fontSize: 11, color: '#2c1e0f', fontWeight: 600 }}>{value}</span>
  </div>
);

const s = {
  container: {
    display: 'flex', flexDirection: 'column', gap: 14,
    background: '#ede5d8', color: '#2c1e0f',
    padding: 18, borderRadius: 8, height: '100%',
    fontFamily: "'Inter','Segoe UI',sans-serif", overflowY: 'auto',
    border: '1px solid #c8b89a',
  },
  title:   { fontSize: 18, fontWeight: 900, borderBottom: '1px solid #c8b89a', paddingBottom: 10, color: '#2c1e0f' },
  section: { display: 'flex', flexDirection: 'column', gap: 8 },
  label:   { fontSize: 10, color: '#a08060', letterSpacing: 2, textTransform: 'uppercase' },
  sep:     { height: 1, background: '#c8b89a' },
  badge:   { padding: '8px 12px', borderRadius: 6, border: '1px solid', fontSize: 12, fontWeight: 700 },
  stat: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    background: '#e6ddd0', padding: '8px 4px', borderRadius: 6, border: '1px solid',
  },
  card:  { background: '#e6ddd0', border: '1px solid', borderRadius: 8, padding: '10px 12px' },
  pill:  { padding: '2px 7px', borderRadius: 10, fontSize: 10, fontWeight: 700 },
};

export default Dashboard;

