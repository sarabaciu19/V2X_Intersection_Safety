# 🚀 Quick Start Guide - V2X Intersection Safety

## Pași Rapidi pentru Rulare

### 1. Instalare Dependențe Frontend

```bash
npm install
```

### 2. Rulare Aplicație (mod Mock - fără backend)

```bash
npm run dev
```

Aplicația va porni pe `http://localhost:3000` și va folosi date mock.

### 3. Test Funcționalitate

1. Apasă butonul **▶️ START** din Control Panel
2. Observă vehiculele mișcându-se pe canvas
3. Verifică Dashboard-ul pentru starea vehiculelor
4. Monitorizează Event Log-ul pentru evenimente

### 4. (Opțional) Conectare la Backend Real

#### Pregătire Backend:

```bash
# Instalare dependențe Python
cd backend
pip install fastapi uvicorn websockets

# Rulare server
python main.py
```

#### În aplicația frontend:
- Click pe butonul **"Switch to WebSocket"** din header
- Backend-ul trebuie să ruleze pe `http://localhost:8000`

## 🎮 Controale Disponibile

| Control | Acțiune |
|---------|---------|
| **START** | Pornește simularea |
| **STOP** | Oprește simularea |
| **RESET** | Resetează tot |
| **Scenariu dropdown** | Schimbă scenariul de trafic |

## 🎨 Ce Vei Vedea

### Canvas (Centru)
- **Intersecție** cu drumuri orizontale și verticale
- **Vehicule** reprezentate ca dreptunghiuri colorate
- **Zone de risc** (roșu/portocaliu/galben)

### Dashboard (Dreapta)
- Status sistem
- Lista vehiculelor active
- Viteze și poziții
- Risc de coliziune

### Event Log (Jos)
- Stream de evenimente în timp real
- Mesaje V2X
- Decizii agenți
- Avertizări

## 🔧 Rezolvare Probleme

### Frontend nu pornește
```bash
# Șterge node_modules și reinstalează
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### WebSocket nu se conectează
- Verifică că backend-ul rulează pe port 8000
- Revino la "Mock Data Mode" pentru testare

### Vehicule nu se mișcă
- Apasă RESET apoi START din nou
- Verifică consola browser-ului pentru erori

## 📚 Next Steps

1. Explorează `src/data/fakeData.js` pentru a înțelege structura datelor
2. Modifică scenariile în `ControlPanel.jsx`
3. Personalizează culorile în `App.css`
4. Implementează backend-ul pentru date reale

## 💡 Tips

- **Mock Mode** e perfect pentru dezvoltare UI
- **WebSocket Mode** necesită backend funcțional
- Folosește Event Log pentru debugging
- Canvas e responsive la dimensiuni diferite

Enjoy! 🎉

