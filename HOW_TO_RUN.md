# 🚀 CUM SĂ RULEZI - V2X Intersection Safety

## ⚡ START RAPID (2 comenzi)

### Frontend (RECOMANDAT - cu Mock Data):

```bash
# 1. Instalare dependencies
npm install

# 2. Pornire aplicație
npm run dev
```

**Deschide browser:**
```
http://localhost:3000
```

✅ **Aplicația va rula cu MOCK DATA (FAKE_STATE)**  
✅ **Funcționează 100% FĂRĂ backend!**  
✅ **Perfect pentru dezvoltare și demo!**

---

## 📊 Modul de Funcționare

### Mode 1: Mock Data (RECOMANDAT pentru început) ✅

```bash
# Doar frontend
cd /Users/sara/Documents/GitHub/V2X_Intersection_Safety
npm install
npm run dev
```

**Ce se întâmplă:**
- ✅ Frontend pornește pe `http://localhost:3000`
- ✅ Folosește **FAKE_STATE** din `src/data/fakeData.js`
- ✅ **useSimulation hook** face fallback AUTOMAT la FAKE_STATE
- ✅ **Funcționează COMPLET** fără backend
- ✅ Vezi vehicule, TTC, cooperation, evenimente LIVE

**Avantaje:**
- 🚀 Pornire rapidă (1 comandă)
- 🎨 Dezvoltare UI instant
- 🎬 Demo pentru prezentări
- ✅ Zero dependență de backend

---

### Mode 2: Cu Backend (WebSocket LIVE)

```bash
# Terminal 1: Backend (Python)
cd /Users/sara/Documents/GitHub/V2X_Intersection_Safety/backend
pip install fastapi uvicorn websockets
python main.py

# Terminal 2: Frontend (React)
cd /Users/sara/Documents/GitHub/V2X_Intersection_Safety
npm install
npm run dev
```

**Ce se întâmplă:**
- ✅ Backend pornește pe `http://localhost:8000`
- ✅ Frontend pornește pe `http://localhost:3000`
- ✅ **WebSocket se conectează** automat la `ws://localhost:8000/ws`
- ✅ Date **LIVE** de la backend
- ✅ Frontend afișează: **"🟢 WebSocket Connected"**

**Avantaje:**
- 📡 Date LIVE de la simulare
- 🤖 Agenți AI activi
- 📊 Statistici reale
- 🔄 Comunicare bidirecțională

---

## 🎮 TEST RAPID (FĂRĂ BACKEND)

### Pași:

#### 1. Instalare (doar prima dată):
```bash
cd /Users/sara/Documents/GitHub/V2X_Intersection_Safety
npm install
```

#### 2. Pornire:
```bash
npm run dev
```

#### 3. Deschide Browser:
```
http://localhost:3000
```

#### 4. În UI:
- ✅ Verifică că vezi: **"📊 Mock Data"** în header
- ✅ Click **Cooperation ON/OFF** → vezi verde/roșu switch
- ✅ Click **START** → vezi vehicule mișcându-se
- ✅ Observă **EventLog** → evenimente apar live
- ✅ Verifică **TTC** în Dashboard → culoare schimbă
- ✅ Click pe **scenarii** → vehicule se schimbă

**TOTUL FUNCȚIONEAZĂ FĂRĂ BACKEND!** ✅

---

## 🔧 Troubleshooting

### Problema 1: `npm install` eșuează

```bash
# Curățare completă
rm -rf node_modules package-lock.json
npm cache clean --force

# Reinstalare
npm install
```

### Problema 2: `vite: command not found`

```bash
# Instalare explicită Vite
npm install --save-dev vite @vitejs/plugin-react

# Sau rulează cu npx
npx vite
```

### Problema 3: Port 3000 ocupat

```bash
# Verifică ce folosește portul
lsof -ti:3000

# Sau modifică portul în vite.config.js:
# server: { port: 3001 }
```

### Problema 4: "Cannot find module"

```bash
# Verifică că toate fișierele există
ls -la src/components/
ls -la src/data/
ls -la src/hooks/

# Reinstalează
npm install
```

---

## 📂 Structură Verificare

### Înainte de a rula, verifică că ai:

```bash
# Fișiere config
✅ package.json
✅ vite.config.js
✅ index.html

# Folder src/
✅ src/main.jsx
✅ src/App.jsx
✅ src/App.css

# Components
✅ src/components/IntersectionCanvas.jsx
✅ src/components/Dashboard.jsx
✅ src/components/ControlPanel.jsx
✅ src/components/EventLog.jsx

# Data & Hooks
✅ src/data/fakeData.js
✅ src/hooks/useSimulation.js
```

Verificare rapidă:
```bash
ls -R src/
```

---

## 🎯 Ce Vei Vedea

### În Browser (http://localhost:3000):

```
┌───────────────────────────────────────────────────────────┐
│  🚗 V2X Intersection Safety System   [📊 Mock Data]     │
├─────────────┬─────────────────────────┬───────────────────┤
│             │                         │                   │
│ 🎮 Control  │    CANVAS 800x800       │ 📊 Dashboard      │
│  Panel      │                         │                   │
│             │    ════════════         │ ⏱️ TTC: 5.2s 🟢  │
│ ┌─────────┐ │    ║   ⭕    ║         │ 🤝 Cooperare      │
│ │✓ COOP ON│ │🚗  ║  RISC   ║  🚗     │    ✓ ON 🟢       │
│ └─────────┘ │    ════════════         │                   │
│             │                         │ 🚗 Vehicule (4)   │
│  [START]    │                         │                   │
│  [Reset]    │                         │ ℹ️ Info Sistem   │
│             │                         │                   │
│ 🎬 Scenarii │                         │                   │
│ ⊥ 🚑 ⚡ 🚨   │                         │                   │
│             │                         │                   │
├─────────────┴─────────────────────────┴───────────────────┤
│  📋 EVENT LOG                                             │
│  [14:23:44] 🚨 Agent B: FRÂNEAZĂ — TTC = 1.8s           │
│  [14:23:45] ⚠️  Agent A: CEDEAZĂ — TTC = 2.1s           │
│  [14:23:46] ✅ Coliziune evitată cu succes              │
│  🔴 LIVE - Sistem rulează în timp real                  │
└───────────────────────────────────────────────────────────┘
```

---

## 🎮 Test Checklist

După ce aplicația pornește, testează:

### 1. ✅ Canvas
- [ ] Vezi intersecția desenată (drumuri gri + marcaje albe)
- [ ] Vezi vehiculele (dreptunghiuri colorate)
- [ ] Vechiculele au ID-uri (A, B, C, D)

### 2. ✅ Cooperation Toggle
- [ ] Click pe **"Cooperation ON/OFF"**
- [ ] Vezi culoarea schimbându-se (🟢 Verde ↔ 🔴 Roșu)
- [ ] Vezi glow effect
- [ ] Dashboard se actualizează

### 3. ✅ START Simulare
- [ ] Click pe **START**
- [ ] Vehiculele încep să se miște
- [ ] TTC se actualizează în Dashboard
- [ ] Evenimente apar în EventLog

### 4. ✅ EventLog
- [ ] Vezi timestamp-uri reale `[HH:MM:SS]`
- [ ] Vezi dot LIVE pulsând 🔴
- [ ] Vezi culori: roșu/galben/verde
- [ ] Scroll automat funcționează

### 5. ✅ Scenarii
- [ ] Click pe **Perpendicular** (⊥)
- [ ] Click pe **Urgență** (🚑)
- [ ] Click pe **Viteze diferite** (⚡)
- [ ] Vehiculele se schimbă

### 6. ✅ Reset
- [ ] Click pe **Reset Scenario**
- [ ] Poziții resetate
- [ ] Simulare oprită

---

## 🐛 Dacă Ceva Nu Merge

### Check 1: Node modules instalate?
```bash
ls -la node_modules/ | head -5
```
Ar trebui să vezi multe foldere.

### Check 2: Vite instalat?
```bash
npm list vite
```
Ar trebui să vezi versiunea (^5.0.0).

### Check 3: Port liber?
```bash
lsof -ti:3000
```
Dacă returnează ceva, portul e ocupat.

### Check 4: Console errors?
```
Deschide DevTools (F12) în browser
Check Console pentru erori
```

---

## 💡 Tips

### Dezvoltare Rapidă:
```bash
# Hot reload e activat!
# Modifici fișierele → salvezi → browser se reîmprospătează AUTOMAT
```

### Testare Scenarii:
```bash
# Modifică src/data/fakeData.js
# Schimbă FAKE_STATE cu propriile date
# Salvează → vezi schimbările instant
```

### Debug:
```bash
# Console logs în browser (F12):
- "✅ WebSocket connected" → backend activ
- "📊 Using Mock Data" → mode mock activ
- "📡 WebSocket message received" → date primite
```

---

## 📝 Comenzi Utile

```bash
# Instalare
npm install

# Dezvoltare
npm run dev

# Build producție
npm run build

# Preview build
npm run preview

# Curățare
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Verificare versiuni
node --version    # Ar trebui v18+
npm --version     # Ar trebui v9+
```

---

## 🎯 Quick Start pentru Demo

### Vrei demo RAPID pentru juriu?

```bash
# 1 comandă:
cd /Users/sara/Documents/GitHub/V2X_Intersection_Safety && npm install && npm run dev
```

Apoi:
1. ✅ Deschide `http://localhost:3000`
2. ✅ Click **START**
3. ✅ Arată **EventLog** cu timestamps reale
4. ✅ Arată **Cooperation toggle** (verde/roșu)
5. ✅ Arată **TTC** colorat în Dashboard
6. ✅ Arată **zona de risc** roșie pe canvas

**Dovadă clară că sistemul e LIVE!** 🎉

---

## ✅ SUCCESS!

Dacă vezi asta în terminal:
```
  VITE v5.0.0  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**TOTUL E GATA! Deschide browser-ul! 🎊**

---

## 🎉 GATA!

**Frontend-ul rulează cu Mock Data!**

Acum poți:
- ✅ Dezvolta UI independent
- ✅ Testa toate features
- ✅ Face demo pentru juriu
- ✅ Integra backend când e gata

**Happy coding! 🚗💨**

