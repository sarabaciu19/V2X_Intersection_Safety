import React from 'react';

/**
 * ControlPanel - Butoanele de demo pentru control simulare
 *
 * Specificații:
 * - Buton 'Cooperation ON/OFF' - CEL MAI IMPORTANT! Schimbă culoarea după stare
 * - Buton 'Reset Scenario' - Resetează pozițiile mașinilor
 * - Selector scenariu: 'Perpendicular' / 'Urgență' / 'Viteze diferite'
 * - Butoane trimit POST requests la backend (sau modifică state local cu fake data)
 */
const ControlPanel = ({
  isRunning = false,
  cooperation = true,
  currentScenario = 'normal',
  onStart,
  onStop,
  onReset,
  onToggleCooperation,
  onScenarioChange,
  onResetScenario,
}) => {
  const handleToggleSimulation = () => {
    if (isRunning) {
      onStop?.();
    } else {
      onStart?.();
    }
  };

  const handleCooperationToggle = () => {
    onToggleCooperation?.();
  };

  const handleResetScenario = () => {
    onResetScenario?.();
  };

  const handleScenarioChange = (scenarioId) => {
    onScenarioChange?.(scenarioId);
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h3 style={styles.title}>🎮 Control Panel</h3>
      </div>

      {/* BUTON COOPERATION - CEL MAI IMPORTANT! */}
      <div style={styles.section}>
        <h4 style={styles.sectionTitle}>🤝 Cooperare V2X</h4>
        <button
          onClick={handleCooperationToggle}
          style={{
            ...styles.button,
            ...styles.cooperationButton,
            backgroundColor: cooperation ? '#059669' : '#DC2626', // Verde/Roșu
            boxShadow: cooperation
              ? '0 0 20px rgba(5, 150, 105, 0.5)'
              : '0 0 20px rgba(220, 38, 38, 0.5)',
          }}
        >
          <span style={styles.buttonIcon}>
            {cooperation ? '✓' : '✗'}
          </span>
          <span style={styles.buttonText}>
            Cooperation {cooperation ? 'ON' : 'OFF'}
          </span>
        </button>
        <p style={styles.description}>
          {cooperation
            ? '✅ Vehiculele comunică și cooperează pentru evitarea coliziunilor'
            : '❌ Comunicare V2X dezactivată - vehiculele acționează independent'}
        </p>
      </div>

      {/* Separator */}
      <div style={styles.separator}></div>

      {/* START/STOP Simulation */}
      <div style={styles.section}>
        <h4 style={styles.sectionTitle}>▶️ Simulare</h4>
        <button
          onClick={handleToggleSimulation}
          style={{
            ...styles.button,
            ...styles.simulationButton,
            backgroundColor: isRunning ? '#DC2626' : '#059669',
          }}
        >
          {isRunning ? (
            <>
              <span style={styles.buttonIcon}>⏸️</span>
              <span style={styles.buttonText}>STOP</span>
            </>
          ) : (
            <>
              <span style={styles.buttonIcon}>▶️</span>
              <span style={styles.buttonText}>START</span>
            </>
          )}
        </button>
      </div>

      {/* RESET SCENARIO Button */}
      <div style={styles.section}>
        <h4 style={styles.sectionTitle}>🔄 Reset</h4>
        <button
          onClick={handleResetScenario}
          style={{
            ...styles.button,
            ...styles.resetButton,
            backgroundColor: '#F59E0B',
          }}
        >
          <span style={styles.buttonIcon}>🔄</span>
          <span style={styles.buttonText}>Reset Scenario</span>
        </button>
        <p style={styles.descriptionSmall}>
          Resetează pozițiile mașinilor la starea inițială
        </p>
      </div>

      {/* Separator */}
      <div style={styles.separator}></div>

      {/* SELECTOR SCENARIU */}
      <div style={styles.section}>
        <h4 style={styles.sectionTitle}>🎬 Scenarii</h4>

        {/* Scenario Cards */}
        <div style={styles.scenarioGrid}>
          {/* Perpendicular */}
          <div
            onClick={() => handleScenarioChange('normal')}
            style={{
              ...styles.scenarioCard,
              ...(currentScenario === 'normal' ? styles.scenarioCardActive : {}),
            }}
          >
            <div style={styles.scenarioIcon}>⊥</div>
            <div style={styles.scenarioName}>Perpendicular</div>
            <div style={styles.scenarioDesc}>2 vehicule perpendiculare</div>
          </div>

          {/* Urgență */}
          <div
            onClick={() => handleScenarioChange('emergency_vehicle')}
            style={{
              ...styles.scenarioCard,
              ...(currentScenario === 'emergency_vehicle' ? styles.scenarioCardActive : {}),
            }}
          >
            <div style={styles.scenarioIcon}>🚑</div>
            <div style={styles.scenarioName}>Urgență</div>
            <div style={styles.scenarioDesc}>Vehicul cu prioritate</div>
          </div>

          {/* Viteze diferite */}
          <div
            onClick={() => handleScenarioChange('high_traffic')}
            style={{
              ...styles.scenarioCard,
              ...(currentScenario === 'high_traffic' ? styles.scenarioCardActive : {}),
            }}
          >
            <div style={styles.scenarioIcon}>⚡</div>
            <div style={styles.scenarioName}>Viteze diferite</div>
            <div style={styles.scenarioDesc}>Trafic variat, 5 vehicule</div>
          </div>

          {/* Coliziune iminentă */}
          <div
            onClick={() => handleScenarioChange('collision_imminent')}
            style={{
              ...styles.scenarioCard,
              ...(currentScenario === 'collision_imminent' ? styles.scenarioCardActive : {}),
            }}
          >
            <div style={styles.scenarioIcon}>🚨</div>
            <div style={styles.scenarioName}>Coliziune</div>
            <div style={styles.scenarioDesc}>Risc critic iminent</div>
          </div>
        </div>
      </div>

      {/* Separator */}
      <div style={styles.separator}></div>

      {/* Status Indicator */}
      <div style={styles.statusSection}>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>Simulare:</span>
          <div style={styles.statusIndicator}>
            <div
              style={{
                ...styles.statusDot,
                backgroundColor: isRunning ? '#22C55E' : '#6B7280',
              }}
            />
            <span style={styles.statusText}>
              {isRunning ? 'Activ' : 'Oprit'}
            </span>
          </div>
        </div>
        <div style={styles.statusRow}>
          <span style={styles.statusLabel}>Scenariu:</span>
          <span style={styles.statusValue}>
            {getScenarioDisplayName(currentScenario)}
          </span>
        </div>
      </div>
    </div>
  );
};

// Helper function
function getScenarioDisplayName(scenarioId) {
  const names = {
    'normal': 'Perpendicular',
    'emergency_vehicle': 'Urgență',
    'high_traffic': 'Viteze diferite',
    'collision_imminent': 'Coliziune iminentă',
  };
  return names[scenarioId] || scenarioId;
}

// ===== STYLES =====
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#1F2937',
    color: '#FFFFFF',
    padding: '20px',
    borderRadius: '8px',
    height: '100%',
    fontFamily: 'Arial, sans-serif',
    gap: '15px',
    overflowY: 'auto',
  },

  header: {
    borderBottom: '2px solid #374151',
    paddingBottom: '12px',
  },

  title: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#FFFFFF',
  },

  section: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },

  sectionTitle: {
    fontSize: '14px',
    fontWeight: 'bold',
    color: '#60A5FA',
    margin: 0,
  },

  separator: {
    height: '1px',
    backgroundColor: '#374151',
    margin: '5px 0',
  },

  // Buttons
  button: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    padding: '14px 20px',
    fontSize: '16px',
    fontWeight: 'bold',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    color: '#FFFFFF',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
  },

  // COOPERATION BUTTON - CEL MAI IMPORTANT!
  cooperationButton: {
    fontSize: '18px',
    padding: '16px 24px',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    animation: 'pulse 2s infinite',
  },

  simulationButton: {
    fontSize: '16px',
  },

  resetButton: {
    fontSize: '16px',
  },

  buttonIcon: {
    fontSize: '20px',
  },

  buttonText: {
    fontSize: 'inherit',
  },

  description: {
    fontSize: '12px',
    color: '#9CA3AF',
    lineHeight: '1.4',
    margin: '0',
  },

  descriptionSmall: {
    fontSize: '11px',
    color: '#6B7280',
    lineHeight: '1.3',
    margin: '0',
  },

  // Scenario Grid
  scenarioGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '8px',
  },

  scenarioCard: {
    backgroundColor: '#111827',
    border: '2px solid #374151',
    borderRadius: '6px',
    padding: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
  },

  scenarioCardActive: {
    backgroundColor: '#1E3A5F',
    borderColor: '#60A5FA',
    boxShadow: '0 0 10px rgba(96, 165, 250, 0.3)',
  },

  scenarioIcon: {
    fontSize: '24px',
    marginBottom: '4px',
  },

  scenarioName: {
    fontSize: '13px',
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
  },

  scenarioDesc: {
    fontSize: '10px',
    color: '#9CA3AF',
    textAlign: 'center',
    lineHeight: '1.2',
  },

  // Status Section
  statusSection: {
    backgroundColor: '#111827',
    padding: '12px',
    borderRadius: '6px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },

  statusRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '13px',
  },

  statusLabel: {
    color: '#9CA3AF',
  },

  statusValue: {
    color: '#FFFFFF',
    fontWeight: 'bold',
  },

  statusIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },

  statusDot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    animation: 'pulse 2s infinite',
  },

  statusText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
};

export default ControlPanel;

