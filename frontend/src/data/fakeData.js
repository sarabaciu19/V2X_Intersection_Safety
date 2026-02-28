/**
 * fakeData.js - Date hardcodate pentru dezvoltare independentă
 * FORMAT IDENTIC CU WEBSOCKET - gata pentru integrare backend
 */

// ===== FORMAT EXACT WEBSOCKET =====
export const FAKE_STATE = {
  vehicles: [
    { id: 'A', x: 400, y: 150, vx: 0,  vy: 3,  state: 'normal'  },
    { id: 'B', x: 150, y: 400, vx: 3,  vy: 0,  state: 'braking' },
  ],
  risk: { danger: true, ttc: 2.1 },
  cooperation: true,
};

// ===== SCENARII =====
export const SCENARIOS = {
  normal: {
    vehicles: [
      { id: 'A', x: 400, y: 50,  vx: 0, vy: 4, state: 'normal' },
      { id: 'B', x: 50,  y: 400, vx: 4, vy: 0, state: 'normal' },
    ],
    risk: { danger: false, ttc: 5.0 },
  },
  collision_imminent: {
    vehicles: [
      { id: 'A', x: 400, y: 280, vx: 0, vy: 4, state: 'braking' },
      { id: 'B', x: 280, y: 400, vx: 4, vy: 0, state: 'yielding' },
    ],
    risk: { danger: true, ttc: 1.2 },
  },
  emergency_vehicle: {
    vehicles: [
      { id: 'AMB', x: 400, y: 50,  vx: 0,  vy: 6, state: 'normal',   priority: 'emergency' },
      { id: 'B',   x: 50,  y: 400, vx: 3,  vy: 0, state: 'yielding', priority: 'normal'    },
    ],
    risk: { danger: false, ttc: 8.0 },
  },
  speed_diff: {
    vehicles: [
      { id: 'A', x: 400, y: 50,  vx: 0, vy: 8, state: 'normal' },
      { id: 'B', x: 50,  y: 400, vx: 2, vy: 0, state: 'normal' },
    ],
    risk: { danger: false, ttc: 6.0 },
  },
};

// ===== BACKWARDS COMPAT (pentru componente vechi) =====
function getDirection(vx, vy) {
  const angle = Math.atan2(vy, vx) * 180 / Math.PI;
  if (angle >= -45  && angle < 45)   return 'Est';
  if (angle >= 45   && angle < 135)  return 'Sud';
  if (angle >= 135  || angle < -135) return 'Vest';
  return 'Nord';
}

export const mockVehicles = FAKE_STATE.vehicles.map(v => ({
  id:            v.id,
  x:             v.x,
  y:             v.y,
  speed:         Math.sqrt(v.vx * v.vx + v.vy * v.vy) * 10,
  heading:       Math.atan2(v.vy, v.vx),
  direction:     getDirection(v.vx, v.vy),
  status:        v.state,
  collisionRisk: FAKE_STATE.risk.danger ? FAKE_STATE.risk.ttc / 10 : 0,
  vx:            v.vx,
  vy:            v.vy,
}));

export const mockCollisionZones = [
  { x: 350, y: 350, width: 100, height: 100, risk: 0.8 },
];

export const mockEvents = [
  {
    type: 'v2x_message',
    message: 'Vehicul A a trimis BSM (Basic Safety Message)',
    timestamp: new Date(Date.now() - 5000).toISOString(),
    vehicleId: 'A',
    details: { messageType: 'BSM', frequency: '10 Hz' },
  },
  {
    type: 'warning',
    message: 'Risc de coliziune detectat între A și B',
    timestamp: new Date(Date.now() - 3000).toISOString(),
    vehicleId: 'A',
    details: { risk: 0.6, distance: '25m', ttc: 2.1 },
  },
  {
    type: 'decision',
    message: 'Agent B a decis: FRÂNARE MODERATĂ',
    timestamp: new Date(Date.now() - 2500).toISOString(),
    vehicleId: 'B',
    details: { action: 'brake', intensity: 0.5, reason: 'collision_avoidance' },
  },
  {
    type: 'collision_avoided',
    message: 'Coliziune evitată cu succes între A și B',
    timestamp: new Date(Date.now() - 1000).toISOString(),
    details: { vehicles: ['A', 'B'], minimumDistance: '12m' },
  },
];

export const mockSystemStatus = {
  running: true,
  simulationTime: '0:00',
  collisionsAvoided: 0,
  totalVehicles: 2,
  activeWarnings: 1,
};

export const mockScenarios = [
  { id: 'normal',             name: 'Intersecție normală',  description: '2 vehicule, trafic normal'       },
  { id: 'collision_imminent', name: 'Coliziune iminentă',   description: 'Risc critic de coliziune'        },
  { id: 'emergency_vehicle',  name: 'Vehicul urgență',      description: 'Ambulanță cu prioritate'         },
  { id: 'speed_diff',         name: 'Viteze diferite',      description: 'Un vehicul rapid, unul lent'     },
];

// ===== GENERARE RANDOM =====
export const generateRandomVehicles = (count = 4) =>
  Array.from({ length: count }, (_, i) => ({
    id:    String.fromCharCode(65 + i),
    x:     Math.random() * 600 + 100,
    y:     Math.random() * 600 + 100,
    vx:    (Math.random() - 0.5) * 6,
    vy:    (Math.random() - 0.5) * 6,
    state: ['normal', 'braking', 'yielding'][Math.floor(Math.random() * 3)],
  }));

export const generateRandomEvent = (vehicleId) => {
  const types    = ['v2x_message', 'warning', 'decision', 'braking'];
  const messages = ['Mesaj V2X trimis', 'Risc detectat', 'Decizie agent', 'Frânare activată'];
  const i        = Math.floor(Math.random() * types.length);
  return {
    type:      types[i],
    message:   messages[i],
    timestamp: new Date().toISOString(),
    vehicleId: vehicleId || 'A',
    details:   { speed: `${Math.floor(Math.random() * 60 + 20)} km/h` },
  };
};

// ===== SIMULARE LIVE =====
export const createMockSimulation = (onUpdate, interval = 500, scenarioId = 'normal') => {
  let state  = JSON.parse(JSON.stringify(SCENARIOS[scenarioId] || SCENARIOS.normal));
  let events = [...mockEvents];
  let time   = 0;
  let collisionsAvoided = 0;

  const id = setInterval(() => {
    // Mișcă vehiculele
    state.vehicles = state.vehicles.map(v => {
      let nx = v.x + v.vx;
      let ny = v.y + v.vy;
      if (nx < 0 || nx > 800) { nx = Math.max(0, Math.min(800, nx)); }
      if (ny < 0 || ny > 800) { ny = Math.max(0, Math.min(800, ny)); }
      return { ...v, x: nx, y: ny };
    });

    // Risc simplu
    const minDist = (() => {
      const vs = state.vehicles;
      if (vs.length < 2) return 999;
      let m = Infinity;
      for (let i = 0; i < vs.length; i++)
        for (let j = i + 1; j < vs.length; j++) {
          const d = Math.sqrt((vs[i].x - vs[j].x) ** 2 + (vs[i].y - vs[j].y) ** 2);
          if (d < m) m = d;
        }
      return m;
    })();
    state.risk = { danger: minDist < 60, ttc: +(minDist / 10).toFixed(1) };

    if (state.risk.danger && Math.random() > 0.9) {
      collisionsAvoided++;
      events = [...events, {
        type: 'collision_avoided',
        message: 'Coliziune evitată prin cooperare V2X',
        timestamp: new Date().toISOString(),
        details: { ttc: state.risk.ttc },
      }];
    }

    time += interval / 1000;

    const vehicles = state.vehicles.map(v => ({
      ...v,
      speed:         Math.sqrt(v.vx ** 2 + v.vy ** 2) * 10,
      heading:       Math.atan2(v.vy, v.vx),
      direction:     getDirection(v.vx, v.vy),
      status:        v.state,
      collisionRisk: state.risk.danger ? 1 - state.risk.ttc / 5 : 0,
    }));

    onUpdate({
      vehicles,
      events:       events.slice(-50),
      systemStatus: {
        running:           true,
        simulationTime:    `${Math.floor(time / 60)}:${String(Math.floor(time % 60)).padStart(2, '0')}`,
        collisionsAvoided,
        totalVehicles:     vehicles.length,
        activeWarnings:    vehicles.filter(v => v.status === 'braking' || v.status === 'yielding').length,
      },
      risk:        state.risk,
      cooperation: state.cooperation ?? true,
    });
  }, interval);

  return () => clearInterval(id);
};

export default {
  FAKE_STATE, SCENARIOS,
  mockVehicles, mockCollisionZones, mockEvents, mockSystemStatus, mockScenarios,
  generateRandomVehicles, generateRandomEvent, createMockSimulation,
};
