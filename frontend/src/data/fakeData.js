/**
 * fakeData.js - Date hardcodate pentru dezvoltare independentă
 * FORMAT IDENTIC CU WEBSOCKET - gata pentru integrare backend
 *
 * Structura:
 * - vehicles: array cu id, x, y, vx, vy, state
 * - risk: {danger: bool, ttc: number}
 * - cooperation: bool
 */

// ===== FORMAT EXACT WEBSOCKET =====
// Același format pe care îl vei primi prin WebSocket
export const FAKE_STATE = {
  vehicles: [
    { id: 'A', x: 400, y: 150, vx: 0, vy: 3, state: 'normal' },
    { id: 'B', x: 150, y: 400, vx: 3, vy: 0, state: 'braking' },
    { id: 'C', x: 600, y: 200, vx: -2, vy: 0, state: 'normal' },
    { id: 'D', x: 350, y: 500, vx: 0, vy: -2.5, state: 'warning' },
  ],
  risk: {
    danger: true,
    ttc: 2.1, // Time to collision in seconds
  },
  cooperation: true,
};

// ===== SCENARII PREDEFINITE =====
export const SCENARIOS = {
  normal: {
    vehicles: [
      { id: 'A', x: 400, y: 150, vx: 0, vy: 3, state: 'normal' },
      { id: 'B', x: 150, y: 400, vx: 3, vy: 0, state: 'normal' },
    ],
    risk: { danger: false, ttc: 5.0 },
    cooperation: true,
  },

  collision_imminent: {
    vehicles: [
      { id: 'A', x: 400, y: 150, vx: 0, vy: 3, state: 'danger' },
      { id: 'B', x: 150, y: 400, vx: 3, vy: 0, state: 'danger' },
    ],
    risk: { danger: true, ttc: 1.2 },
    cooperation: true,
  },

  high_traffic: {
    vehicles: [
      { id: 'A', x: 400, y: 100, vx: 0, vy: 3, state: 'normal' },
      { id: 'B', x: 100, y: 400, vx: 3, vy: 0, state: 'normal' },
      { id: 'C', x: 400, y: 500, vx: 0, vy: -2.5, state: 'warning' },
      { id: 'D', x: 700, y: 400, vx: -3, vy: 0, state: 'normal' },
      { id: 'E', x: 350, y: 200, vx: 1, vy: 2, state: 'normal' },
    ],
    risk: { danger: true, ttc: 2.8 },
    cooperation: true,
  },

  emergency_vehicle: {
    vehicles: [
      { id: 'AMBULANCE', x: 400, y: 50, vx: 0, vy: 5, state: 'emergency' },
      { id: 'A', x: 150, y: 400, vx: 3, vy: 0, state: 'yielding' },
      { id: 'B', x: 650, y: 400, vx: -3, vy: 0, state: 'yielding' },
    ],
    risk: { danger: false, ttc: 10.0 },
    cooperation: true,
  },
};

// Helper: calculează direcția din viteze
function getDirection(vx, vy) {
  const angle = Math.atan2(vy, vx) * 180 / Math.PI;
  if (angle >= -45 && angle < 45) return 'Est';
  if (angle >= 45 && angle < 135) return 'Sud';
  if (angle >= 135 || angle < -135) return 'Vest';
  return 'Nord';
}

// ===== BACKWARDS COMPATIBILITY =====
// Conversie pentru componente care folosesc vechiul format
export const mockVehicles = FAKE_STATE.vehicles.map(v => ({
  id: v.id,
  x: v.x,
  y: v.y,
  speed: Math.sqrt(v.vx * v.vx + v.vy * v.vy) * 10, // Convert to km/h
  heading: Math.atan2(v.vy, v.vx),
  direction: getDirection(v.vx, v.vy),
  status: v.state,
  collisionRisk: FAKE_STATE.risk.danger ? FAKE_STATE.risk.ttc / 10 : 0,
  vx: v.vx,
  vy: v.vy,
}));


// ===== EVENIMENTE MOCK =====
export const mockEvents = [
  {
    type: 'v2x_message',
    message: 'Vehicul A a trimis BSM (Basic Safety Message)',
    timestamp: new Date(Date.now() - 5000).toISOString(),
    vehicleId: 'A',
    details: {
      messageType: 'BSM',
      frequency: '10 Hz',
    },
  },
  {
    type: 'warning',
    message: 'Risc de coliziune detectat între A și B',
    timestamp: new Date(Date.now() - 3000).toISOString(),
    vehicleId: 'A',
    details: {
      risk: 0.6,
      distance: '25m',
      ttc: 2.1,
    },
  },
  {
    type: 'decision',
    message: 'Agent B a decis: FRÂNARE MODERATĂ',
    timestamp: new Date(Date.now() - 2500).toISOString(),
    vehicleId: 'B',
    details: {
      action: 'brake',
      intensity: 0.5,
      reason: 'collision_avoidance',
    },
  },
  {
    type: 'braking',
    message: 'Vehicul B frânează pentru evitarea coliziunii',
    timestamp: new Date(Date.now() - 2000).toISOString(),
    vehicleId: 'B',
    details: {
      initialSpeed: '50 km/h',
      currentSpeed: '35 km/h',
    },
  },
  {
    type: 'collision_avoided',
    message: 'Coliziune evitată cu succes între A și B',
    timestamp: new Date(Date.now() - 1000).toISOString(),
    details: {
      vehicles: ['A', 'B'],
      minimumDistance: '12m',
    },
  },
];

// Zone de coliziune mock
export const mockCollisionZones = [
  {
    x: 350,
    y: 250,
    width: 100,
    height: 100,
    risk: 0.8,
  },
  {
    x: 250,
    y: 350,
    width: 80,
    height: 80,
    risk: 0.5,
  },
];

// Stare sistem mock
export const mockSystemStatus = {
  running: true,
  simulationTime: '2:35',
  collisionsAvoided: 12,
  totalVehicles: 4,
  activeWarnings: 2,
};

// Scenarii disponibile
export const mockScenarios = [
  {
    id: 'normal',
    name: 'Intersecție normală',
    description: '4 vehicule, trafic normal',
  },
  {
    id: 'high_traffic',
    name: 'Trafic intens',
    description: '10+ vehicule, risc crescut',
  },
  {
    id: 'emergency',
    name: 'Vehicul urgență',
    description: 'Ambulanță cu prioritate',
  },
  {
    id: 'collision_imminent',
    name: 'Coliziune iminentă',
    description: 'Risc critic de coliziune',
  },
];

// ===== GENERARE DINAMICĂ =====

// Funcție pentru generarea de vehicule random (format WebSocket)
export const generateRandomVehicles = (count = 5) => {
  return Array.from({ length: count }, (_, i) => ({
    id: String.fromCharCode(65 + i), // A, B, C, D...
    x: Math.random() * 600 + 100,
    y: Math.random() * 400 + 100,
    vx: (Math.random() - 0.5) * 6,
    vy: (Math.random() - 0.5) * 6,
    state: ['normal', 'warning', 'braking', 'danger'][Math.floor(Math.random() * 4)],
  }));
};

// Funcție pentru generarea de evenimente random
export const generateRandomEvent = (vehicleId) => {
  const eventTypes = ['v2x_message', 'warning', 'decision', 'braking', 'acceleration'];
  const messages = [
    'Mesaj V2X transmis cu succes',
    'Risc de coliziune detectat',
    'Decizie luată de agent',
    'Frânare de urgență activată',
    'Accelerare pentru evitare',
  ];

  const type = eventTypes[Math.floor(Math.random() * eventTypes.length)];

  return {
    type,
    message: messages[Math.floor(Math.random() * messages.length)],
    timestamp: new Date().toISOString(),
    vehicleId: vehicleId || String.fromCharCode(65 + Math.floor(Math.random() * 10)),
    details: {
      speed: `${Math.floor(Math.random() * 60 + 20)} km/h`,
      risk: (Math.random()).toFixed(2),
    },
  };
};

// ===== SIMULARE LIVE =====

/**
 * Simulare în timp real - actualizează automat vehiculele
 * @param {Function} onUpdate - Callback cu state nou
 * @param {number} interval - Interval update (ms)
 * @param {string} scenarioId - ID scenariu de început
 * @returns {Function} Cleanup function
 */
export const createMockSimulation = (onUpdate, interval = 500, scenarioId = 'normal') => {
  let state = JSON.parse(JSON.stringify(SCENARIOS[scenarioId] || FAKE_STATE));
  let events = [...mockEvents];
  let time = 0;
  let collisionsAvoided = 0;

  const intervalId = setInterval(() => {
    // Actualizează poziția vehiculelor
    state.vehicles = state.vehicles.map(vehicle => {
      let newX = vehicle.x + vehicle.vx;
      let newY = vehicle.y + vehicle.vy;

      // Wrap around canvas (800x600)
      if (newX < 0) newX = 800;
      if (newX > 800) newX = 0;
      if (newY < 0) newY = 600;
      if (newY > 600) newY = 0;

      return {
        ...vehicle,
        x: newX,
        y: newY,
      };
    });

    // Calculează risc coliziune
    const minDistance = calculateMinDistance(state.vehicles);
    state.risk.danger = minDistance < 50;
    state.risk.ttc = minDistance / 10; // Simplist TTC calculation

    // Generează evenimente aleatorii
    if (Math.random() > 0.7 && state.vehicles.length > 0) {
      const randomVehicle = state.vehicles[Math.floor(Math.random() * state.vehicles.length)];
      events = [...events, generateRandomEvent(randomVehicle.id)];
    }

    // Detectare coliziune evitată
    if (state.risk.danger && Math.random() > 0.9) {
      collisionsAvoided++;
      events = [...events, {
        type: 'collision_avoided',
        message: 'Coliziune evitată prin cooperare V2X',
        timestamp: new Date().toISOString(),
        details: { ttc: state.risk.ttc.toFixed(2) },
      }];
    }

    time += interval / 1000;

    // Convert to format compatibil cu componente
    const vehicles = state.vehicles.map(v => ({
      id: v.id,
      x: v.x,
      y: v.y,
      speed: Math.sqrt(v.vx * v.vx + v.vy * v.vy) * 10,
      heading: Math.atan2(v.vy, v.vx),
      direction: getDirection(v.vx, v.vy),
      status: v.state,
      collisionRisk: state.risk.danger ? 1 - (state.risk.ttc / 5) : 0,
      vx: v.vx,
      vy: v.vy,
    }));

    onUpdate({
      vehicles,
      events: events.slice(-50), // Păstrează ultimele 50
      systemStatus: {
        running: true,
        simulationTime: `${Math.floor(time / 60)}:${String(Math.floor(time % 60)).padStart(2, '0')}`,
        collisionsAvoided,
        totalVehicles: vehicles.length,
        activeWarnings: vehicles.filter(v => v.status === 'warning' || v.status === 'danger').length,
      },
      rawState: state, // State în format WebSocket
    });
  }, interval);

  return () => clearInterval(intervalId);
};

// Helper: calculează distanța minimă între vehicule
function calculateMinDistance(vehicles) {
  if (vehicles.length < 2) return 1000;

  let minDist = Infinity;
  for (let i = 0; i < vehicles.length; i++) {
    for (let j = i + 1; j < vehicles.length; j++) {
      const dx = vehicles[i].x - vehicles[j].x;
      const dy = vehicles[i].y - vehicles[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      minDist = Math.min(minDist, dist);
    }
  }
  return minDist;
}

// ===== DEFAULT EXPORT =====
export default {
  FAKE_STATE,
  SCENARIOS,
  mockVehicles,
  mockCollisionZones,
  mockEvents,
  mockSystemStatus,
  mockScenarios,
  generateRandomVehicles,
  generateRandomEvent,
  createMockSimulation,
};
  {
    x: 350,
    y: 250,
    width: 100,
    height: 100,
    risk: 0.8,
  },
  {
    x: 250,
    y: 350,
    width: 80,
    height: 80,
    risk: 0.5,
  },
];

// Evenimente mock
export const mockEvents = [
  {
    type: 'v2x_message',
    message: 'Vehicul V001 a trimis BSM (Basic Safety Message)',
    timestamp: new Date(Date.now() - 5000).toISOString(),
    vehicleId: 'V001',
    details: {
      messageType: 'BSM',
      frequency: '10 Hz',
    },
  },
  {
    type: 'warning',
    message: 'Risc de coliziune detectat între V002 și V003',
    timestamp: new Date(Date.now() - 3000).toISOString(),
    vehicleId: 'V002',
    details: {
      risk: 0.6,
      distance: '25m',
    },
  },
  {
    type: 'decision',
    message: 'Agent V003 a decis: FRÂNARE MODERATĂ',
    timestamp: new Date(Date.now() - 2500).toISOString(),
    vehicleId: 'V003',
    details: {
      action: 'brake',
      intensity: 0.5,
      reason: 'collision_avoidance',
    },
  },
  {
    type: 'braking',
    message: 'V003 frânează pentru evitarea coliziunii',
    timestamp: new Date(Date.now() - 2000).toISOString(),
    vehicleId: 'V003',
    details: {
      initialSpeed: '50 km/h',
      currentSpeed: '35 km/h',
    },
  },
  {
    type: 'collision_avoided',
    message: 'Coliziune evitată cu succes între V002 și V003',
    timestamp: new Date(Date.now() - 1000).toISOString(),
    details: {
      vehicles: ['V002', 'V003'],
      minimumDistance: '12m',
    },
  },
  {
    type: 'danger',
    message: 'PERICOL IMINENT! V004 se apropie cu viteză mare',
    timestamp: new Date(Date.now() - 500).toISOString(),
    vehicleId: 'V004',
    details: {
      speed: '60 km/h',
      risk: 0.95,
    },
  },
];

// Stare sistem mock
export const mockSystemStatus = {
  running: true,
  simulationTime: '2:35',
  collisionsAvoided: 12,
  totalVehicles: 4,
  activeWarnings: 2,
};

// Scenarii disponibile
export const mockScenarios = [
  {
    id: 'default',
    name: 'Intersecție normală',
    description: '4 vehicule, trafic normal',
  },
  {
    id: 'high_traffic',
    name: 'Trafic intens',
    description: '10+ vehicule, risc crescut',
  },
  {
    id: 'emergency',
    name: 'Vehicul urgență',
    description: 'Ambulanță cu prioritate',
  },
  {
    id: 'pedestrian',
    name: 'Cu pietoni',
    description: 'Pietoni traversează intersecția',
  },
  {
    id: 'multi_collision',
    name: 'Risc multiplu',
    description: 'Multiple riscuri de coliziune simultane',
  },
];

// Funcție pentru generarea de vehicule random
export const generateRandomVehicles = (count = 5) => {
  const directions = ['Nord', 'Sud', 'Est', 'Vest'];
  const statuses = ['normal', 'warning', 'braking', 'danger'];
  const headings = [0, Math.PI / 2, Math.PI, -Math.PI / 2];

  return Array.from({ length: count }, (_, i) => ({
    id: `V${String(i + 1).padStart(3, '0')}`,
    x: Math.random() * 600 + 100,
    y: Math.random() * 400 + 100,
    speed: Math.random() * 40 + 20,
    heading: headings[Math.floor(Math.random() * headings.length)],
    direction: directions[Math.floor(Math.random() * directions.length)],
    status: statuses[Math.floor(Math.random() * statuses.length)],
    collisionRisk: Math.random(),
  }));
};

// Funcție pentru generarea de evenimente random
export const generateRandomEvent = (vehicleId) => {
  const eventTypes = ['v2x_message', 'warning', 'decision', 'braking', 'acceleration'];
  const messages = [
    'Mesaj V2X transmis cu succes',
    'Risc de coliziune detectat',
    'Decizie luată de agent',
    'Frânare de urgență activată',
    'Accelerare pentru evitare',
  ];

  const type = eventTypes[Math.floor(Math.random() * eventTypes.length)];

  return {
    type,
    message: messages[Math.floor(Math.random() * messages.length)],
    timestamp: new Date().toISOString(),
    vehicleId: vehicleId || `V${String(Math.floor(Math.random() * 10) + 1).padStart(3, '0')}`,
    details: {
      speed: `${Math.floor(Math.random() * 60 + 20)} km/h`,
      risk: (Math.random()).toFixed(2),
    },
  };
};

// Funcție pentru simularea actualizărilor în timp real
export const createMockSimulation = (onUpdate, interval = 1000) => {
  let vehicles = [...mockVehicles];
  let events = [...mockEvents];
  let time = 0;

  const intervalId = setInterval(() => {
    // Actualizează poziția vehiculelor
    vehicles = vehicles.map(vehicle => {
      const dx = Math.cos(vehicle.heading) * (vehicle.speed / 10);
      const dy = Math.sin(vehicle.heading) * (vehicle.speed / 10);

      return {
        ...vehicle,
        x: (vehicle.x + dx) % 800,
        y: (vehicle.y + dy) % 600,
        collisionRisk: Math.max(0, Math.min(1, vehicle.collisionRisk + (Math.random() - 0.5) * 0.1)),
      };
    });

    // Generează evenimente aleatorii
    if (Math.random() > 0.7) {
      const randomVehicle = vehicles[Math.floor(Math.random() * vehicles.length)];
      events = [...events, generateRandomEvent(randomVehicle.id)];
    }

    time += interval / 1000;

    onUpdate({
      vehicles,
      events: events.slice(-50), // Păstrează ultimele 50 de evenimente
      systemStatus: {
        running: true,
        simulationTime: `${Math.floor(time / 60)}:${String(Math.floor(time % 60)).padStart(2, '0')}`,
        collisionsAvoided: Math.floor(time / 10),
      },
    });
  }, interval);

  return () => clearInterval(intervalId);
};

export default {
  mockVehicles,
  mockCollisionZones,
  mockEvents,
  mockSystemStatus,
  mockScenarios,
  generateRandomVehicles,
  generateRandomEvent,
  createMockSimulation,
};

