import React from 'react';

/**
 * Dashboard - Panel lateral cu informații detaliate
 *
 * Specificații:
 * - Pentru fiecare vehicul: ID, viteză curentă, stare agent
 * - TTC (Time To Collision) cu culori:
 *   - Verde: > 5s
 *   - Galben: 2-5s
 *   - Roșu: < 2s
 * - Status cooperare: ON (verde) / OFF (roșu)
 * - Design: flex column, background închis, text alb, profesional
 */
const Dashboard = ({ vehicles = [], systemStatus = {}, risk = { danger: false, ttc: 5.0 } }) => {
  /**
   * Returnează culoarea pentru TTC
   */
  const getTTCColor = (ttc) => {
    if (ttc > 5) return '#22C55E'; // Verde
    if (ttc >= 2) return '#FBBF24'; // Galben
    return '#EF4444'; // Roșu
  };

  /**
   * Returnează text stare agent
   */
  const getStateText = (state) => {
    switch (state) {
      case 'normal':
        return 'Normal';
      case 'braking':
        return 'Frânare';
      case 'yielding':
        return 'Cedează';
      case 'danger':
        return 'Pericol';
      case 'warning':
        return 'Avertizare';
      case 'emergency':
        return 'Urgență';
      default:
        return state || 'N/A';
    }
  };

  /**
   * Returnează culoarea pentru starea agentului
   */
  const getStateColor = (state) => {
    switch (state) {
      case 'danger':
        return '#EF4444'; // Roșu
      case 'yielding':
        return '#EF4444'; // Roșu
      case 'braking':
        return '#F59E0B'; // Portocaliu
      case 'warning':
        return '#FBBF24'; // Galben
      case 'emergency':
        return '#8B5CF6'; // Violet
      case 'normal':
      default:
        return '#3B82F6'; // Albastru
    }
  };

  // Cooperare status
  const cooperation = systemStatus.cooperation !== undefined ? systemStatus.cooperation : true;

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h2 style={styles.title}>📊 Dashboard</h2>
      </div>

      {/* TTC Section - PRIORITATE */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>⏱️ Time To Collision (TTC)</h3>
        <div style={styles.ttcDisplay}>
          <div style={styles.ttcValue}>
            <span
              style={{
                ...styles.ttcNumber,
                color: getTTCColor(risk.ttc || 5.0)
              }}
            >
              {(risk.ttc || 5.0).toFixed(1)}s
            </span>
          </div>
          <div style={styles.ttcLabel}>
            {risk.danger ? '⚠️ RISC DETECTAT' : '✅ SIGUR'}
          </div>
        </div>

        {/* TTC Legend */}
        <div style={styles.ttcLegend}>
          <div style={styles.legendItem}>
            <span style={{...styles.legendDot, backgroundColor: '#22C55E'}}></span>
            <span style={styles.legendText}>&gt; 5s: Sigur</span>
          </div>
          <div style={styles.legendItem}>
            <span style={{...styles.legendDot, backgroundColor: '#FBBF24'}}></span>
            <span style={styles.legendText}>2-5s: Atenție</span>
          </div>
          <div style={styles.legendItem}>
            <span style={{...styles.legendDot, backgroundColor: '#EF4444'}}></span>
            <span style={styles.legendText}>&lt; 2s: Pericol</span>
          </div>
        </div>
      </div>

      {/* Cooperation Status */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>🤝 Status Cooperare</h3>
        <div style={styles.cooperationStatus}>
          <div
            style={{
              ...styles.cooperationBadge,
              backgroundColor: cooperation ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
              borderColor: cooperation ? '#22C55E' : '#EF4444',
            }}
          >
            <span style={{
              ...styles.cooperationText,
              color: cooperation ? '#22C55E' : '#EF4444',
            }}>
              {cooperation ? '✓ ON' : '✗ OFF'}
            </span>
          </div>
          <p style={styles.cooperationDesc}>
            {cooperation
              ? 'Vehiculele comunică și cooperează'
              : 'Comunicare V2X dezactivată'}
          </p>
        </div>
      </div>

      {/* Vehicles Section */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>🚗 Vehicule Active ({vehicles.length})</h3>

        {vehicles.length === 0 ? (
          <p style={styles.emptyMessage}>Nu există vehicule active</p>
        ) : (
          <div style={styles.vehicleList}>
            {vehicles.map(vehicle => {
              const state = vehicle.state || vehicle.status || 'normal';
              const speed = vehicle.speed !== undefined
                ? vehicle.speed
                : Math.sqrt((vehicle.vx || 0) ** 2 + (vehicle.vy || 0) ** 2) * 10;

              return (
                <div key={vehicle.id} style={styles.vehicleCard}>
                  {/* Vehicle Header */}
                  <div style={styles.vehicleHeader}>
                    <span style={styles.vehicleId}>🚗 {vehicle.id}</span>
                    <span
                      style={{
                        ...styles.stateBadge,
                        backgroundColor: getStateColor(state),
                      }}
                    >
                      {getStateText(state)}
                    </span>
                  </div>

                  {/* Vehicle Details */}
                  <div style={styles.vehicleDetails}>
                    {/* Viteză */}
                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>Viteză:</span>
                      <span style={styles.detailValue}>
                        {Math.round(speed)} km/h
                      </span>
                    </div>

                    {/* Poziție */}
                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>Poziție:</span>
                      <span style={styles.detailValue}>
                        ({Math.round(vehicle.x)}, {Math.round(vehicle.y)})
                      </span>
                    </div>

                    {/* Direcție (dacă există) */}
                    {vehicle.direction && (
                      <div style={styles.detailRow}>
                        <span style={styles.detailLabel}>Direcție:</span>
                        <span style={styles.detailValue}>{vehicle.direction}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* System Info */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>ℹ️ Info Sistem</h3>
        <div style={styles.systemInfo}>
          <div style={styles.infoRow}>
            <span style={styles.infoLabel}>Timp simulare:</span>
            <span style={styles.infoValue}>{systemStatus.simulationTime || '0:00'}</span>
          </div>
          <div style={styles.infoRow}>
            <span style={styles.infoLabel}>Coliziuni evitate:</span>
            <span style={styles.infoValue}>{systemStatus.collisionsAvoided || 0}</span>
          </div>
          <div style={styles.infoRow}>
            <span style={styles.infoLabel}>Avertizări active:</span>
            <span style={styles.infoValue}>{systemStatus.activeWarnings || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// ===== STYLES =====
const styles = {
  // Container principal - flex column, background închis
  container: {
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#1F2937', // Background închis
    color: '#FFFFFF', // Text alb
    padding: '20px',
    borderRadius: '8px',
    height: '100%',
    overflowY: 'auto',
    fontFamily: 'Arial, sans-serif',
    gap: '20px',
  },

  // Header
  header: {
    borderBottom: '2px solid #374151',
    paddingBottom: '15px',
  },

  title: {
    margin: 0,
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#FFFFFF',
  },

  // Section
  section: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },

  sectionTitle: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#60A5FA',
    margin: 0,
    borderBottom: '1px solid #374151',
    paddingBottom: '8px',
  },

  // TTC Display
  ttcDisplay: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    backgroundColor: '#111827',
    padding: '20px',
    borderRadius: '8px',
    border: '2px solid #374151',
  },

  ttcValue: {
    marginBottom: '10px',
  },

  ttcNumber: {
    fontSize: '48px',
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },

  ttcLabel: {
    fontSize: '14px',
    color: '#9CA3AF',
    fontWeight: 'bold',
  },

  // TTC Legend
  ttcLegend: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    fontSize: '12px',
  },

  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },

  legendDot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    display: 'inline-block',
  },

  legendText: {
    color: '#D1D5DB',
  },

  // Cooperation Status
  cooperationStatus: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '10px',
  },

  cooperationBadge: {
    padding: '12px 24px',
    borderRadius: '8px',
    border: '2px solid',
    fontWeight: 'bold',
    fontSize: '18px',
  },

  cooperationText: {
    fontWeight: 'bold',
  },

  cooperationDesc: {
    fontSize: '12px',
    color: '#9CA3AF',
    margin: 0,
    textAlign: 'center',
  },

  // Vehicle List
  vehicleList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },

  emptyMessage: {
    textAlign: 'center',
    color: '#6B7280',
    fontStyle: 'italic',
    padding: '20px',
  },

  // Vehicle Card
  vehicleCard: {
    backgroundColor: '#111827',
    border: '1px solid #374151',
    borderRadius: '6px',
    padding: '12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },

  vehicleHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  vehicleId: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#FFFFFF',
  },

  stateBadge: {
    padding: '4px 10px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 'bold',
    color: '#FFFFFF',
  },

  // Vehicle Details
  vehicleDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },

  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '13px',
  },

  detailLabel: {
    color: '#9CA3AF',
  },

  detailValue: {
    color: '#FFFFFF',
    fontWeight: '500',
  },

  // System Info
  systemInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    backgroundColor: '#111827',
    padding: '12px',
    borderRadius: '6px',
  },

  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '13px',
  },

  infoLabel: {
    color: '#9CA3AF',
  },

  infoValue: {
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
};

export default Dashboard;

