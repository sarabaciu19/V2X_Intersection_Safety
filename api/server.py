"""
api/server.py — FastAPI + WebSocket
Endpoints:
  POST /start                          — porneste simularea
  POST /stop                           — pauzeaza simularea
  GET  /state                          — snapshot JSON curent
  GET  /scenarios                      — lista scenariilor
  POST /reset                          — resetare (body: {"scenario": "..."})
  POST /toggle-cooperation             — toggle V2X ON/OFF
  POST /grant-clearance/{vehicle_id}   — clearance manual
  GET  /custom/scenario                — citeste scenariul custom
  POST /custom/vehicle                 — adauga vehicul custom
  DELETE /custom/vehicle/{id}          — sterge vehicul custom
  PATCH /custom/vehicle/{id}           — modifica vehicul custom
  DELETE /custom/clear                 — goleste scenariul custom
  WS   /ws                             — stream live la 30 FPS
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal
from simulation.engine import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(engine.run())
    yield
    engine.stop()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="V2X Intersection Safety", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ──────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    scenario: Optional[str] = None

class CustomVehicleRequest(BaseModel):
    id: str = Field(..., description="ID unic, ex: 'A', 'CAR1'")
    direction: Literal['N', 'S', 'E', 'V'] = Field(..., description="Directia de intrare in intersectie")
    intent: Literal['straight', 'left', 'right'] = Field('straight', description="Intentia la intersectie")
    priority: Literal['normal', 'emergency'] = Field('normal', description="Prioritate vehicul")
    speed_multiplier: float = Field(1.0, ge=0.2, le=3.0, description="Multiplicator viteza (0.2–3.0)")
    v2x_enabled: bool = Field(True, description="True = vehicul cu V2X, False = fără V2X (ignoră semnale)")

class CustomVehicleUpdate(BaseModel):
    intent: Optional[Literal['straight', 'left', 'right']] = None
    priority: Optional[Literal['normal', 'emergency']] = None
    speed_multiplier: Optional[float] = Field(None, ge=0.2, le=3.0)
    v2x_enabled: Optional[bool] = None

# ── Control simulare ─────────────────────────────────────────────────────

@app.post("/start", summary="Porneste / reia simularea")
async def start_simulation():
    engine.start()
    return {"status": "running", "paused": False}

@app.post("/stop", summary="Pauzeaza simularea")
async def stop_simulation():
    engine.stop_sim()
    return {"status": "paused", "paused": True}

# ── State & scenarii ─────────────────────────────────────────────────────

@app.get("/state")
async def get_state():
    return engine.get_state()

@app.get("/scenarios")
async def get_scenarios():
    return {"scenarios": engine.get_scenarios(), "current": engine.scenario_name}

@app.post("/reset")
async def reset(body: ResetRequest = ResetRequest()):
    engine.reset(scenario=body.scenario)
    return {"status": "reset", "scenario": engine.scenario_name}

@app.post("/toggle-cooperation")
async def toggle_cooperation():
    new_state = engine.toggle_cooperation()
    return {"cooperation": new_state}

@app.post("/grant-clearance/{vehicle_id}")
async def grant_clearance(vehicle_id: str):
    return engine.grant_clearance(vehicle_id)

# ── Custom scenario ──────────────────────────────────────────────────────

@app.get("/custom/scenario", summary="Citeste definitia scenariului custom curent")
async def get_custom_scenario():
    return {"custom_scenario": engine.get_custom_scenario()}

@app.post("/custom/vehicle", summary="Adauga un vehicul in scenariul custom")
async def custom_add_vehicle(body: CustomVehicleRequest):
    result = engine.custom_add_vehicle(body.model_dump())
    if not result['ok']:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=result['reason'])
    return result

@app.delete("/custom/vehicle/{vehicle_id}", summary="Sterge un vehicul din scenariul custom")
async def custom_remove_vehicle(vehicle_id: str):
    result = engine.custom_remove_vehicle(vehicle_id)
    if not result['ok']:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=result['reason'])
    return result

@app.patch("/custom/vehicle/{vehicle_id}", summary="Modifica parametrii unui vehicul custom")
async def custom_update_vehicle(vehicle_id: str, body: CustomVehicleUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result = engine.custom_update_vehicle(vehicle_id, updates)
    if not result['ok']:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=result['reason'])
    return result

@app.delete("/custom/clear", summary="Goleste complet scenariul custom")
async def custom_clear():
    return engine.custom_clear()

@app.post("/custom/semaphore", summary="Setează dacă scenariul custom are semafor")
async def custom_set_semaphore(body: dict):
    has_sem = body.get('has_semaphore', True)
    return engine.set_custom_semaphore(bool(has_sem))

# ── WebSocket ────────────────────────────────────────────────────────────

class _Manager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

manager = _Manager()

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.send_json(engine.get_state())
            await asyncio.sleep(1 / 30)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
