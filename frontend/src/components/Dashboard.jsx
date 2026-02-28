import React from 'react';

const STATE_COLOR = {
  moving:   '#3B82F6',
  waiting:  '#F59E0B',
  crossing: '#22C55E',
  done:     '#6B7280',
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
const Dashboard = ({ vehicles = [], semaphore = {}, cooperation = true, onGrantClearance = null }) => {
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
          background: cooperation ? '#05966922' : '#92400e22',
          borderColor: cooperation ? '#059669'   : '#F59E0B',
          color:       cooperation ? '#22C55E'   : '#FBBF24',
        }}>
          {cooperation
            ? '✓ AUTO — sistemul central decide'
            : '✋ MANUAL — tu decizi cine trece'}
        </div>
        {!cooperation && (
          <p style={{ color: '#9CA3AF', fontSize: 11, margin: 0 }}>
            Click pe un vehicul portocaliu din canvas, sau apasă butonul de mai jos.
          </p>
        )}
      </section>

      {/* Semafor */}
      <section style={s.section}>
        <div style={s.label}>Semafor V2I</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 20, height: 20, borderRadius: '50%',
            background: semaphore.light === 'green'  ? '#22C55E'
                      : semaphore.light === 'yellow' ? '#FBBF24' : '#EF4444',
            boxShadow: `0 0 12px ${semaphore.light === 'green'  ? '#22C55E'
                                 : semaphore.light === 'yellow' ? '#FBBF24' : '#EF4444'}`,
          }} />
          <span style={{ color: '#D1D5DB', fontSize: 13 }}>
            {semaphore.light === 'green'  ? 'Verde — liber'
           : semaphore.light === 'yellow' ? 'Galben — atenție'
                                          : 'Roșu — stop'}
          </span>
          {semaphore.emergency && (
            <span style={{ color: '#F87171', fontSize: 11, fontWeight: 700 }}>🚑 URGENȚĂ</span>
          )}
        </div>
      </section>

      {/* Sumar */}
      <section style={s.section}>
        <div style={s.label}>Sumar intersecție</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
          {[
            { val: vehicles.length, label: 'total',     col: '#D1D5DB' },
            { val: waiting,         label: 'așteaptă',  col: '#F59E0B' },
            { val: crossing,        label: 'traversează', col: '#22C55E' },
          ].map(({ val, label, col }) => (
            <div key={label} style={{ ...s.stat, borderColor: col }}>
              <span style={{ fontSize: 22, fontWeight: 900, color: col }}>{val}</span>
              <span style={{ fontSize: 9, color: '#9CA3AF' }}>{label}</span>
            </div>
          ))}
        </div>
      </section>

      <div style={s.sep} />

      {/* Vehicule */}
      <section style={s.section}>
        <div style={s.label}>Vehicule ({vehicles.length})</div>
        {vehicles.length === 0 && (
          <p style={{ color: '#6B7280', fontSize: 12, textAlign: 'center', padding: '16px 0' }}>
            Niciun vehicul activ
          </p>
        )}
        {vehicles.map(v => {
          const col = v.priority === 'emergency' ? '#EF4444' : (STATE_COLOR[v.state] || '#3B82F6');
          return (
            <div key={v.id} style={{ ...s.card, borderColor: col + '55' }}>
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {v.priority === 'emergency' && <span>🚑</span>}
                  <span style={{ color: '#F9FAFB', fontWeight: 700, fontSize: 14 }}>{v.id}</span>
                  <span style={{ ...s.pill, background: col + '33', color: col }}>
                    {v.state}
                  </span>
                </div>
                <span style={{ ...s.pill, background: '#1F2937', color: '#9CA3AF', fontSize: 10 }}>
                  {v.clearance ? '🟢 clearance' : '🔴 stop'}
                </span>
              </div>

              {/* Detalii */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px', marginTop: 6 }}>
                <Row label="Direcție" value={DIR_LABEL[v.direction] || v.direction} />
                <Row label="Intenție" value={INTENT_LABEL[v.intent] || v.intent} />
                <Row label="Distanță" value={`${v.dist_to_intersection ?? '—'}px`} />
                <Row label="Viteză"   value={`${Math.round(Math.sqrt((v.vx||0)**2+(v.vy||0)**2)*10)} km/h`} />
              </div>

              {/* Buton manual clearance — doar în modul manual și când vehiculul așteaptă */}
              {onGrantClearance && v.state === 'waiting' && (
                <button
                  onClick={() => onGrantClearance(v.id)}
                  style={{
                    marginTop: 8, width: '100%',
                    padding: '7px 0', border: 'none', borderRadius: 6,
                    background: '#F59E0B', color: '#000',
                    fontFamily: 'monospace', fontWeight: 900, fontSize: 12,
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
    </div>
  );
};

const Row = ({ label, value }) => (
  <div style={{ display: 'flex', flexDirection: 'column' }}>
    <span style={{ fontSize: 9, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1 }}>{label}</span>
    <span style={{ fontSize: 11, color: '#D1D5DB', fontWeight: 600 }}>{value}</span>
  </div>
);

const s = {
  container: {
    display: 'flex', flexDirection: 'column', gap: 14,
    background: '#111827', color: '#fff',
    padding: 18, borderRadius: 8, height: '100%',
    fontFamily: 'monospace', overflowY: 'auto',
  },
  title:   { fontSize: 18, fontWeight: 900, borderBottom: '1px solid #374151', paddingBottom: 10 },
  section: { display: 'flex', flexDirection: 'column', gap: 8 },
  label:   { fontSize: 10, color: '#6B7280', letterSpacing: 2, textTransform: 'uppercase' },
  sep:     { height: 1, background: '#1F2937' },
  badge: {
    padding: '8px 12px', borderRadius: 6, border: '1px solid',
    fontSize: 12, fontWeight: 700,
  },
  stat: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    background: '#1F2937', padding: '8px 4px', borderRadius: 6,
    border: '1px solid',
  },
  card: {
    background: '#1F2937', border: '1px solid',
    borderRadius: 8, padding: '10px 12px',
  },
  pill: {
    padding: '2px 7px', borderRadius: 10, fontSize: 10, fontWeight: 700,
  },
};

export default Dashboard;

