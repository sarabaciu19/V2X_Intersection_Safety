# 📊 fakeData.js - Ghid de Utilizare

## 🎯 Scop

Fișierul `fakeData.js` conține date hardcodate în **format identic cu WebSocket** pentru dezvoltare independentă de backend.

## 📋 Format Date (IDENTIC WEBSOCKET)

```javascript
export const FAKE_STATE = {
  vehicles: [
    { id: 'A', x: 400, y: 150, vx: 0, vy: 3, state: 'normal' },
    { id: 'B', x: 150, y: 400, vx: 3, vy: 0, state: 'braking' }
  ],
  risk: {
    danger: true,
    ttc: 2.1  // Time to collision (seconds)
  },
  cooperation: true
};
```

## 🔧 Structura Datelor

### Vehicle Object
```javascript
{
  id: 'A',          // ID unic vehicul (string)
  x: 400,           // Poziție X (pixels)
  y: 150,           // Poziție Y (pixels)
  vx: 0,            // Viteza pe X (pixels/frame)
  vy: 3,            // Viteza pe Y (pixels/frame)
  state: 'normal'   // Stare: 'normal', 'warning', 'braking', 'danger', 'emergency'
}
```

### Risk Object
```javascript
{
  danger: true,     // Boolean: există risc iminent?
  ttc: 2.1          // Time To Collision în secunde
}
```

## 🎬 Scenarii Disponibile

### 1. Normal (default)
```javascript
SCENARIOS.normal
```
- 2 vehicule
- Trafic normal
- TTC: 5.0s

### 2. Collision Imminent
```javascript
SCENARIOS.collision_imminent
```
- 2 vehicule în coliziune
- State: 'danger'
- TTC: 1.2s

### 3. High Traffic
```javascript
SCENARIOS.high_traffic
```
- 5 vehicule
- Trafic intens
- TTC: 2.8s

### 4. Emergency Vehicle
```javascript
SCENARIOS.emergency_vehicle
```
- Ambulanță cu prioritate
- Alte vehicule yielding
- TTC: 10.0s

## 💻 Utilizare în Cod

### Import Date Statice

```javascript
import { FAKE_STATE, SCENARIOS } from './data/fakeData';

// Folosește state-ul default
const vehicles = FAKE_STATE.vehicles;
const risk = FAKE_STATE.risk;

// Sau un scenariu specific
const highTraffic = SCENARIOS.high_traffic;
```

### Simulare Live

```javascript
import { createMockSimulation } from './data/fakeData';

// Pornește simularea
const cleanup = createMockSimulation(
  (data) => {
    console.log('Vehicles:', data.vehicles);
    console.log('Events:', data.events);
    console.log('Status:', data.systemStatus);
    console.log('Raw State (WebSocket format):', data.rawState);
  },
  500,  // Update la fiecare 500ms
  'normal'  // Scenariu de început
);

// Oprește simularea
cleanup();
```

### Backwards Compatibility

```javascript
import { mockVehicles, mockEvents, mockSystemStatus } from './data/fakeData';

// Format vechi (pentru componente existente)
<IntersectionCanvas vehicles={mockVehicles} />
<EventLog events={mockEvents} />
<Dashboard systemStatus={mockSystemStatus} />
```

## 🔄 Conversie Automat

Fișierul convertește automat între formatele:

**WebSocket Format** → **Component Format**

```javascript
// WebSocket (backend)
{ id: 'A', x: 400, y: 150, vx: 0, vy: 3, state: 'normal' }

// Component (frontend)
{
  id: 'A',
  x: 400,
  y: 150,
  speed: 30,              // calculat din vx, vy
  heading: 1.57,          // radiani
  direction: 'Sud',       // text
  status: 'normal',       // alias pentru state
  collisionRisk: 0.21,    // calculat din ttc
  vx: 0,
  vy: 3
}
```

## 🎲 Generare Dinamică

### Vehicule Random

```javascript
import { generateRandomVehicles } from './data/fakeData';

const vehicles = generateRandomVehicles(5);  // Generează 5 vehicule
```

### Evenimente Random

```javascript
import { generateRandomEvent } from './data/fakeData';

const event = generateRandomEvent('A');  // Event pentru vehicul A
```

## 📝 States Disponibile

| State | Descriere | Culoare UI |
|-------|-----------|------------|
| `normal` | Trafic normal | 🟢 Verde |
| `warning` | Avertizare | 🟡 Galben |
| `braking` | Frânare | 🟠 Portocaliu |
| `danger` | Pericol iminent | 🔴 Roșu |
| `emergency` | Vehicul urgență | 🔵 Albastru |
| `yielding` | Cedează trecerea | ⚪ Alb |

## 🔮 Tranziție la Backend Real

Când backend-ul e gata, datele vor veni **EXACT** în același format:

```javascript
// Mock Mode (acum)
import { FAKE_STATE } from './data/fakeData';
const data = FAKE_STATE;

// WebSocket Mode (mai târziu)
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);  // ACELAȘI format!
};
```

**ZERO SCHIMBĂRI NECESARE** în componentele tale!

## ✅ Best Practices

1. **Dezvoltare UI**: Folosește `createMockSimulation()` pentru testare live
2. **Testing**: Folosește `SCENARIOS` pentru cazuri edge
3. **Demo**: Folosește `FAKE_STATE` pentru prezentări
4. **Backend Ready**: Switch la WebSocket fără modificări cod

## 🚀 Quick Start

```javascript
// 1. În App.jsx
import { createMockSimulation } from './data/fakeData';

// 2. În useEffect
useEffect(() => {
  const cleanup = createMockSimulation((data) => {
    setVehicles(data.vehicles);
    setEvents(data.events);
    setSystemStatus(data.systemStatus);
  });
  
  return cleanup;
}, []);

// 3. Profit! 🎉
```

## 📞 Suport

Pentru întrebări despre format sau probleme de integrare, verifică:
- `STATUS.md` - Status general proiect
- `QUICKSTART.md` - Ghid rapid pornire
- `README.md` - Documentație completă

