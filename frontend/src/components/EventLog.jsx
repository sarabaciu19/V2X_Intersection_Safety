import React, { useState, useEffect } from 'react';

/**
 * EventLog - Log decizii agenți în timp real
 * Afișează evenimentele și deciziile agenților V2X
 */
const EventLog = ({ events = [], maxEvents = 100 }) => {
  const [filteredEvents, setFilteredEvents] = useState(events);
  const [filter, setFilter] = useState('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const logRef = React.useRef(null);

  useEffect(() => {
    // Filtrare evenimente
    if (filter === 'all') {
      setFilteredEvents(events);
    } else {
      setFilteredEvents(events.filter(event => event.type === filter));
    }
  }, [events, filter]);

  useEffect(() => {
    // Auto-scroll la ultimul eveniment
    if (autoScroll && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [filteredEvents, autoScroll]);

  const getEventIcon = (type) => {
    switch (type) {
      case 'warning':
        return '⚠️';
      case 'danger':
        return '🚨';
      case 'braking':
        return '🛑';
      case 'acceleration':
        return '⚡';
      case 'collision_avoided':
        return '✅';
      case 'v2x_message':
        return '📡';
      case 'decision':
        return '🤖';
      default:
        return 'ℹ️';
    }
  };

  const getEventColor = (type) => {
    switch (type) {
      case 'warning':
        return '#FFA500';
      case 'danger':
        return '#FF0000';
      case 'braking':
        return '#FFD700';
      case 'collision_avoided':
        return '#00FF00';
      case 'v2x_message':
        return '#00BFFF';
      case 'decision':
        return '#9370DB';
      default:
        return '#888';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ro-RO', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 1
    });
  };

  const clearLog = () => {
    setFilteredEvents([]);
  };

  return (
    <div className="event-log" style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>📋 Event Log</h3>
        <div style={styles.controls}>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={styles.filterSelect}
          >
            <option value="all">Toate</option>
            <option value="warning">Avertizări</option>
            <option value="danger">Pericole</option>
            <option value="braking">Frânări</option>
            <option value="collision_avoided">Coliziuni evitate</option>
            <option value="v2x_message">Mesaje V2X</option>
            <option value="decision">Decizii</option>
          </select>

          <label style={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              style={styles.checkbox}
            />
            Auto-scroll
          </label>

          <button onClick={clearLog} style={styles.clearButton}>
            🗑️ Clear
          </button>
        </div>
      </div>

      <div ref={logRef} style={styles.logContainer}>
        {filteredEvents.length === 0 ? (
          <p style={styles.emptyMessage}>Nu există evenimente de afișat</p>
        ) : (
          filteredEvents.slice(-maxEvents).map((event, index) => (
            <div
              key={`${event.timestamp}-${index}`}
              style={{
                ...styles.eventItem,
                borderLeftColor: getEventColor(event.type),
              }}
            >
              <div style={styles.eventHeader}>
                <span style={styles.eventIcon}>{getEventIcon(event.type)}</span>
                <span style={styles.eventTime}>{formatTimestamp(event.timestamp)}</span>
                {event.vehicleId && (
                  <span style={styles.vehicleTag}>🚗 {event.vehicleId}</span>
                )}
              </div>
              <div style={styles.eventMessage}>{event.message}</div>
              {event.details && (
                <div style={styles.eventDetails}>
                  {Object.entries(event.details).map(([key, value]) => (
                    <span key={key} style={styles.detailItem}>
                      <strong>{key}:</strong> {JSON.stringify(value)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div style={styles.footer}>
        <span style={styles.eventCount}>
          {filteredEvents.length} evenimente {filter !== 'all' && `(${filter})`}
        </span>
      </div>
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: '#2a2a2a',
    color: '#ffffff',
    borderRadius: '8px',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: 'Arial, sans-serif',
  },
  header: {
    padding: '15px 20px',
    borderBottom: '2px solid #444',
  },
  title: {
    margin: '0 0 10px 0',
    fontSize: '20px',
  },
  controls: {
    display: 'flex',
    gap: '10px',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  filterSelect: {
    padding: '5px 10px',
    fontSize: '12px',
    borderRadius: '3px',
    border: '1px solid #444',
    backgroundColor: '#333',
    color: '#fff',
    cursor: 'pointer',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  checkbox: {
    cursor: 'pointer',
  },
  clearButton: {
    padding: '5px 10px',
    fontSize: '12px',
    backgroundColor: '#FF4444',
    color: '#fff',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
  },
  logContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '10px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  emptyMessage: {
    textAlign: 'center',
    color: '#888',
    fontStyle: 'italic',
    marginTop: '20px',
  },
  eventItem: {
    backgroundColor: '#333',
    padding: '10px',
    borderRadius: '5px',
    borderLeft: '4px solid',
    fontSize: '13px',
  },
  eventHeader: {
    display: 'flex',
    gap: '10px',
    alignItems: 'center',
    marginBottom: '5px',
  },
  eventIcon: {
    fontSize: '16px',
  },
  eventTime: {
    color: '#888',
    fontSize: '11px',
    fontFamily: 'monospace',
  },
  vehicleTag: {
    backgroundColor: '#444',
    padding: '2px 6px',
    borderRadius: '3px',
    fontSize: '11px',
  },
  eventMessage: {
    marginLeft: '26px',
    lineHeight: '1.4',
  },
  eventDetails: {
    marginTop: '5px',
    marginLeft: '26px',
    display: 'flex',
    flexDirection: 'column',
    gap: '3px',
    fontSize: '11px',
    color: '#aaa',
  },
  detailItem: {
    fontFamily: 'monospace',
  },
  footer: {
    padding: '10px 20px',
    borderTop: '1px solid #444',
    fontSize: '12px',
    color: '#888',
  },
  eventCount: {
    fontStyle: 'italic',
  },
};

export default EventLog;

