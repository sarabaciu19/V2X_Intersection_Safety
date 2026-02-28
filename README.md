# 🚗 V2X Intersection Safety System

Sistem inteligent de siguranță la intersecții bazat pe comunicație V2X (Vehicle-to-Everything) cu agenți AI pentru prevenirea coliziunilor.

## 📋 Descriere

Acest proiect implementează un sistem de simulare și vizualizare în timp real pentru siguranța vehiculelor la intersecții. Sistemul folosește:
- **Comunicație V2X** pentru schimb de date între vehicule
- **Agenți AI** pentru luarea deciziilor de evitare a coliziunilor
- **Vizualizare interactivă** pentru monitorizare în timp real

## 🏗️ Arhitectură

### Frontend (React + Vite)
- **IntersectionCanvas.jsx** - Canvas 2D (800x800px) cu intersecție centrată la (400,400), vehicule 30x50px colorate după state, zonă de risc roșie când danger=true
- **Dashboard.jsx** - Panel lateral cu:
  - TTC (Time To Collision) cu culori: verde >5s, galben 2-5s, roșu <2s
  - Status cooperare: ON (verde) / OFF (roșu)
  - Pentru fiecare vehicul: ID, viteză curentă, stare agent
  - Design profesional: flex column, background închis, text alb
- **ControlPanel.jsx** - Butoane de control:
  - **Cooperation ON/OFF** (cel mai important!) - Verde (#059669) când ON, Roșu (#DC2626) când OFF, cu glow effect
  - **Reset Scenario** - Resetează pozițiile mașinilor
  - **Selector Scenarii** - Grid 2x2 cu 4 scenarii:
    - Perpendicular (⊥) - 2 vehicule perpendiculare
    - Urgență (🚑) - Vehicul cu prioritate  
    - Viteze diferite (⚡) - Trafic variat
    - Coliziune (🚨) - Risc critic
  - POST requests la backend (sau modifică state local)
- **EventLog.jsx** - Log decizii agenți în timp real:
  - **Ultimele 10 decizii** ale agenților (configurabil)
  - **Scroll automat** (toggle ON/OFF)
  - **Format**: `[12:34:05] Agent B: FRÂNEAZĂ — TTC = 1.8s`
  - **Culori semantice**:
    - 🔴 Roșu (#EF4444) pentru frânare
    - 🟡 Galben (#FBBF24) pentru cedare
    - 🟢 Verde (#22C55E) pentru normal
    - 🔵 Albastru (#3B82F6) pentru V2X messages
  - **Indicator LIVE** cu dot pulsând - dovadă că sistemul rulează live, nu e animație
  - **Animații slideIn** pentru evenimente noi
  - **Timestamp real** pentru fiecare decizie
- **useSimulation.js** - WebSocket hook pentru conectare backend:
  - useEffect + WebSocket nativ (fără librării extra)
  - Conectare la ws://localhost:8000/ws
  - Parse JSON și update state React automat
  - **Fallback automat la fakeData** când WebSocket nu e conectat
  - Astfel poți lucra independent și integrezi ușor când backend-ul e gata
- **fakeData.js** - Date hardcodate în format WebSocket pentru dezvoltare independentă
- **App.jsx** - Layout principal

### Backend (FastAPI + Python)
- **main.py** - Server FastAPI cu WebSocket
- **simulator.py** - Logica de simulare a intersecției
- **vehicle.py** - Model vehicul cu agent AI

## 🚀 Instalare și Rulare

### Prerequisite
- Node.js (v18+)
- Python (v3.9+)
- npm sau yarn

### Frontend

```bash
# Navighează în folderul frontend
cd frontend

# Instalare dependențe
npm install

# Rulare în modul dezvoltare
npm run dev

# Build pentru producție
npm run build

# Preview build producție
npm run preview
```

Frontend-ul va rula pe `http://localhost:3000` (sau `http://localhost:3001` dacă portul 3000 e ocupat)

### Backend

```bash
# Instalare dependențe Python
pip install -r requirements.txt

# Rulare server
cd backend
python main.py
```

Backend-ul va rula pe `http://localhost:8000`

## 🎮 Utilizare

### Moduri de Funcționare

1. **Mock Data Mode** - Date hardcodate pentru testare fără backend
   - Ideal pentru dezvoltare frontend
   - Click pe "Switch to Mock" în header

2. **WebSocket Mode** - Conexiune live cu backend
   - Date în timp real de la simulare
   - Click pe "Switch to WebSocket" în header

### Controale

- **START** - Pornește simularea
- **STOP** - Oprește simularea
- **RESET** - Resetează simularea la starea inițială
- **Scenariu** - Selectează diferite scenarii de trafic:
  - Intersecție normală
  - Trafic intens
  - Vehicul urgență
  - Cu pietoni
  - Risc multiplu

### Interpretare Culori Vehicule

- 🟢 **Verde** - Status normal
- 🟡 **Galben** - Avertizare
- 🟠 **Portocaliu** - Frânare
- 🔴 **Roșu** - Pericol iminent

## 📊 Caracteristici

### Vizualizare
- Canvas 2D interactiv (800x800px) cu intersecție
- Intersecție centrată la (400, 400)
- Drumuri cu marcaje de stradă (linii albe)
- Vehicule 30x50px colorate după state:
  - Normal: albastru (#3B82F6)
  - Braking: portocaliu (#F59E0B)
  - Yielding: roșu (#EF4444)
- Zonă de risc: cerc roșu semi-transparent când danger=true
- Indicatori direcție și viteză pe vehicule

### Dashboard
- **TTC (Time To Collision)** cu sistem de culori:
  - 🟢 Verde (>5s): Sigur
  - 🟡 Galben (2-5s): Atenție
  - 🔴 Roșu (<2s): Pericol
- **Status cooperare V2X**: ON (verde) / OFF (roșu)
- Pentru fiecare vehicul:
  - ID vehicul
  - Viteză curentă (km/h)
  - Stare agent (badge colorat)
  - Poziție și direcție
- Info sistem: timp simulare, coliziuni evitate, avertizări active
- Design profesional: flex column, dark theme, contrast maxim

### Event Log
- **Format profesional**: `[HH:MM:SS] Agent ID: MESAJ — TTC = Xs`
- **Timestamp real** pentru fiecare eveniment
- **Ultimele 10 evenimente** (configurable)
- **Culori semantice**:
  - 🔴 Roșu: Frânare, pericol
  - 🟡 Galben: Cedare, avertizare
  - 🟢 Verde: Normal, coliziune evitată
  - 🔵 Albastru: Mesaje V2X, decizii
- **Scroll automat** (toggle ON/OFF)
- **Indicator LIVE** cu dot pulsând (🔴)
- **Animații slideIn** pentru evenimente noi
- **Dovadă vizuală** că sistemul rulează LIVE, nu e animație pre-făcută
- **Legend** cu explicații culori
- **Icons emoji** pentru fiecare tip eveniment

## 🛠️ Tehnologii Utilizate

### Frontend
- React 18
- Vite
- Canvas 2D API
- WebSocket API
- CSS3

### Backend
- FastAPI
- WebSockets
- Python 3.9+
- Asyncio

## 📁 Structură Proiect

```
V2X_Intersection_Safety/
├── frontend/                    # Frontend React + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── IntersectionCanvas.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── ControlPanel.jsx
│   │   │   └── EventLog.jsx
│   │   ├── hooks/
│   │   │   └── useSimulation.js
│   │   ├── data/
│   │   │   └── fakeData.js
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── backend/                     # Backend FastAPI + Python
│   ├── main.py
│   └── models/
│       ├── simulator.py
│       └── vehicle.py
├── pyproject.toml
└── README.md
```

## 🔧 Configurare Avansată

### WebSocket URL
Modifică URL-ul WebSocket în `src/hooks/useSimulation.js`:
```javascript
const useSimulation = (url = 'ws://localhost:8000/ws')
```

### Port Frontend
Modifică portul în `vite.config.js`:
```javascript
server: {
  port: 3000,
  // ...
}
```

### Dimensiuni Canvas
Modifică în `src/App.jsx`:
```javascript
<IntersectionCanvas
  vehicles={vehicles}
  dimensions={{ width: 800, height: 600 }}
/>
```

## 🤝 Contribuții

Contribuțiile sunt binevenite! Pentru schimbări majore, deschideți mai întâi un issue pentru a discuta ce doriți să schimbați.

## 📝 Licență

MIT

## 👥 Autori

Sara - V2X Intersection Safety System

## 📞 Contact

Pentru întrebări sau sugestii, deschideți un issue pe GitHub.
