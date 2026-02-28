"""
api/server.py — FastAPI + WebSocket
Endpoints:
  GET  /state               — snapshot JSON curent
  GET  /scenarios           — lista scenariilor
  POST /reset               — resetare (body: {"scenario": "..."})
  POST /toggle-cooperation  — toggle V2X ON/OFF
  WS   /ws                  — stream live la 30 FPS
Rulare:
  uvicorn api.server:app --reload --port 8000
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
app = FastAPI(title="V2X Intersection Safety", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------------------------------------------------
# HTTP Endpoints
# -----------------------------------------------------------------------
@app.get("/state")
async def get_state():
    return engine.get_state()
@app.get("/scenarios")
async def get_scenarios():
    return {"scenarios": engine.get_scenarios(), "current": engine.scenario_name}
class ResetRequest(BaseModel):
    scenario: str = None
@app.post("/reset")
async def reset(body: ResetRequest = ResetRequest()):
    engine.reset(scenario=body.scenario)
    return {"status": "reset", "scenario": engine.scenario_name}
@app.post("/toggle-cooperation")
async def toggle_cooperation():
    new_state = engine.toggle_cooperation()
    return {"cooperation": new_state}
# -----------------------------------------------------------------------
# WebSocket
# -----------------------------------------------------------------------
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
    """Stream live la ~30 FPS catre frontend."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.send_json(engine.get_state())
            await asyncio.sleep(1 / 30)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
