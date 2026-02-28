# V2X Intersection Safety — Ce s-a făcut până acum

---

## Backend (Python / FastAPI)

### `models/vehicle.py`
Clasa `Vehicle` — unitatea de bază a simulării.
- **Atribute:** `id`, `x`, `y`, `vx`, `vy`, `state` (`normal`/`braking`/`yielding`), `priority` (`normal`/`emergency`)
- **`update()`** — mișcă vehiculul un tick: `x += vx`, `y += vy`
- **`reset()`** — revine la poziția inițială (pentru butonul Reset)
- **`to_dict()`** — returnează JSON-ul publicat pe V2X Bus și trimis la frontend

---

### `services/v2x_bus.py`
Canal de comunicare partajat — dict global `{ vehicle_id: state_dict }`.
- **`publish(id, data)`** — vehiculul își scrie starea
- **`get_others(id)`** — agentul citește stările celorlalți
- **`get_all()`** — toate stările (folosit de semafor și engine)
- **`clear()`** — resetat la schimbare scenariu

---

### `services/collision.py`
Calculul TTC și detecția riscului.
- **`time_to_intersection(v)`** — `distanță față de (400,400) / viteză proprie`
- **`assess_risk(vehicles)`** — evaluează toate perechile, returnează `{ risk, ttc, action, pair }`
- **`is_right_of(v1, v2)`** — regula priorității din dreapta (produs vectorial)
- **`check_physical_collision(vehicles)`** — detectează impact real (distanță < 20px)
- Praguri: `TTC_BRAKE = 3.0s` → frânează, `TTC_YIELD = 1.5s` → stop complet

---

### `models/agent.py`
Logica de decizie V2X per vehicul, apelată la fiecare tick.
- Dacă `cooperation=False` → ignoră bus-ul complet (demo coliziune)
- Dacă `cooperation=True` → citește V2X Bus, calculează TTC, aplică regula:
  - Urgență în jur → `yield`/`brake`
  - Eu sunt urgență → `go`
  - Celălalt vine din dreapta → `yield`/`brake`
  - Eu vin din dreapta → `go`
  - TTC al meu mai mare → `yield`/`brake`
- Aplică pe vehicul: `brake` → `vx/vy *= 0.85`, `yield` → `vx=vy=0`
- Loghează automat la schimbare de acțiune

---

### `services/infrastructure.py`
Agentul semafor V2I — citește bus-ul și publică recomandări.
- Ciclu normal: `verde 5s → galben 1s → roșu 5s` (la 30 FPS = 150/30/150 tick-uri)
- Dacă detectează vehicul cu `priority="emergency"` în raza de 200px → **comută imediat pe verde**
- Calculează recomandări de viteză per vehicul (`maintain`/`slow_down`/`stop`)
- Publică pe bus ca `v2x_bus["INFRA"]`

---

### `scenarios/`
- **`scenario_base.py`** — `ScenarioBase` (dataclass cu `name`, `description`, `vehicles`) și `VehicleDef`
- **`perpendicular.py`** — A (Nord, vy=+4) + B (Vest, vx=+4) → scenariu principal
- **`emergency.py`** — URGENTA (Vest, vx=+6, priority=emergency) + A (Nord, vy=+3)
- **`speed_diff.py`** — A (Nord, vy=+8 rapid) + B (Vest, vx=+2 lent)

---

### `simulation/engine.py`
Loop-ul principal la 30 FPS — orchestrează totul.

Ordinea per tick: `update()` → `publish()` → `decide()` → `semaphore.update()` → `check_collisions()` → `assess_risk()` → cachează snapshot

Metode publice: `reset(scenario)`, `toggle_cooperation()`, `get_state()`, `get_scenarios()`

Instanță globală `engine = SimulationEngine()` importată de server.

---

### `api/server.py`
FastAPI — pornit ca task asyncio împreună cu engine-ul.

| Endpoint | Ce face |
|----------|---------|
| `GET /state` | Snapshot JSON curent |
| `GET /scenarios` | Lista + scenariul activ |
| `POST /reset` | Body opțional: `{"scenario": "emergency"}` |
| `POST /toggle-cooperation` | V2X ON/OFF |
| `WS /ws` | Stream live 30 FPS |

CORS activat pentru `*` — frontend-ul merge pe orice port.

---

### `utils/logger.py`
- Loghează `BRAKE`/`YIELD`/`COLLISION` → consolă + `decisions.json`
- `get_recent(10)` inclus în fiecare snapshot WebSocket ca `event_log[]`
- `decisions.json` — păstrează ultimele 500 decizii, util de arătat juriului

---

## Frontend (React / Vite)

### `frontend/src/hooks/useSimulation.js`
Hook WebSocket cu fallback automat pe date fake.
- Versiunea completă: `{ state, isConnected, error }`
- La eroare/deconectare → cade automat pe `FAKE_STATE`

### `frontend/src/components/IntersectionCanvas.jsx`
Canvas 2D `800×800px`, intersecție la `(400, 400)`.
- Drumuri gri, marcaje albe întrerupte, linii de oprire
- Vehicule `30×50px`: `normal`→albastru, `braking`→portocaliu, `yielding`→roșu, `emergency`→violet
- Cerc roșu semi-transparent `r=80` când `risk.danger === true`

### `frontend/src/App.jsx`
Layout principal — asamblează toate componentele.
- Toggle între **Mock Data** și **WebSocket live**
- Gestionează `cooperation`, `isRunning`, `currentScenario` ca state global
- ⚠️ `POST /toggle-cooperation` și `POST /reset` spre backend **nu sunt încă conectate** (marcat TODO)

---

## Ce mai lipsește

| Cine | Task |
|------|------|
| **P2** | Conectează butoanele `ControlPanel` la `POST /toggle-cooperation` și `POST /reset` |
| **P2** | `Dashboard` + `EventLog` să consume `wsState` în loc de `mockState` |
| **P3** | Verifică end-to-end scenariul `emergency` |
| **P3** | Tunează pragurile TTC dacă e nevoie (`services/collision.py` liniile 17-18) |

---

## Pornire

```bash
# Backend
uvicorn api.server:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```
