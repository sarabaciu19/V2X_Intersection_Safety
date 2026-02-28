# 🚀 GHID COMPLET - Cum să Rulezi Aplicația

## ✅ STRUCTURĂ ORGANIZATĂ

Proiectul are acum structura corectă:

```
V2X_Intersection_Safety/
├── frontend/          ← Frontend React + Vite
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/           ← Backend FastAPI + Python
│   ├── main.py
│   └── models/
└── README.md
```

---

## 🚀 RULARE FRONTEND

### Pas 1: Navighează în frontend
```bash
cd frontend
```

### Pas 2: Instalează dependencies (prima dată)
```bash
npm install
```

### Pas 3: Pornește aplicația
```bash
npm run dev
```

### Pas 4: Deschide în browser
```
http://localhost:3000
```

**SAU dacă portul e ocupat:**
```
http://localhost:3001
```

**Verifică în terminal ce port folosește:**
```
➜  Local:   http://localhost:3001/  ← Acest URL!
```

---

## 🎮 CE AR TREBUI SĂ VEZI:

```
╔══════════════════════════════════════════════════╗
║  🚗 V2X Intersection Safety System              ║
║  [📊 Mock Data]                                 ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  🎮 CONTROL    │   CANVAS      │  📊 DASHBOARD  ║
║   PANEL        │   800x800     │                ║
║  ────────────  │  ═══════════  │  TTC: 5.0s 🟢  ║
║                │  ║         ║  │  ✅ SIGUR      ║
║  🤝 Cooperare  │  ║    🚗   ║  │                ║
║  ┌──────────┐  │  ║         ║  │  🤝 Cooperare  ║
║  │ ✓ COOP ON│  │  ═══════════  │     ✓ ON 🟢   ║
║  └──────────┘  │               │                ║
║   🟢 Glow!     │               │  🚗 Vehicule   ║
║                │               │  4 active      ║
║  ▶️ [START]    │               │                ║
║  🔄 [Reset]    │               │                ║
║                │               │                ║
║  🎬 Scenarii   │               │                ║
║  ⊥ 🚑 ⚡ 🚨     │               │                ║
╠══════════════════════════════════════════════════╣
║  📋 EVENT LOG - Decizii Timp Real               ║
║  0 / 10 evenimente    [🔽 Auto]                 ║
║  🔴 LIVE - Sistem rulează în timp real         ║
╚══════════════════════════════════════════════════╝
```

---

## 🐛 TROUBLESHOOTING

### Problemă: Port ocupat
```
Port 3000 is in use, trying another one...
➜  Local:   http://localhost:3001/
```

**Soluție:** Deschide `http://localhost:3001` în loc de 3000

---

### Problemă: Ecran alb
```bash
# 1. Hard refresh în browser
Cmd + Shift + R (Mac)
Ctrl + Shift + R (Windows)

# 2. Verifică Console (F12)
# Caută erori roșii

# 3. Dacă sunt erori, curăță cache:
cd frontend
rm -rf node_modules/.vite dist
npm run dev
```

---

### Problemă: npm install eșuează
```bash
# Curățare completă
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

---

## 🎮 TEST RAPID

După ce aplicația pornește:

### 1. Click START
→ Vehiculele se mișcă pe canvas ✅

### 2. Click Cooperation ON/OFF
→ Verde ↔ Roșu cu glow ✅

### 3. Verifică EventLog
→ Vezi timestamps live `[HH:MM:SS]` ✅

### 4. Verifică TTC în Dashboard
→ Culoare se schimbă (verde/galben/roșu) ✅

---

## 🔧 COMENZI UTILE

```bash
# Pornire dezvoltare
cd frontend
npm run dev

# Build producție
npm run build

# Preview build
npm run preview

# Instalare dependencies
npm install

# Curățare cache
rm -rf node_modules/.vite dist
```

---

## 🎯 QUICK START (O singură comandă)

```bash
cd frontend && npm install && npm run dev
```

Apoi deschide browser la URL-ul afișat în terminal!

---

## 📞 SUPORT

Dacă întâmpini probleme:

1. Verifică că ești în folderul `frontend/`
2. Verifică că `npm install` a rulat cu succes
3. Verifică ce port folosește (vezi în terminal)
4. Deschide Console în browser (F12) pentru erori

---

**GATA! Aplicația ar trebui să ruleze perfect! 🎉**

