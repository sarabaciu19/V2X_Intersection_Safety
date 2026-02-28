"""
services/infrastructure.py — Agentul semafor V2I
Citeste V2X Bus → emite recomandari:
  - Vehicul de urgenta → verde pentru el, rosu ceilalti
  - Ciclu semafor: verde 5s, galben 1s, rosu 5s (la 30 FPS = 150/30/150 ticks)
  - Publica pe bus ca 'INFRA': { light, recommendation, emergency }
"""
import time
from services import v2x_bus
from services.collision import time_to_intersection, TTC_BRAKE
from utils import logger
# Durate faze (tick-uri la 30 FPS)
GREEN_TICKS  = 150   # 5s
YELLOW_TICKS = 30    # 1s
RED_TICKS    = 150   # 5s
class InfrastructureAgent:
    """Agentul semafor inteligent."""
    def __init__(self):
        self.light: str = "green"         # "green" | "yellow" | "red"
        self.timer: int = 0
        self.emergency_active: bool = False
        self.emergency_id: str | None = None
        self.phase: str = "NS"            # "NS" | "EW"
        self._last_light: str = ""
    def update(self) -> dict:
        """
        Apelat la fiecare tick de engine.
        Returneaza starea semaforului pentru snapshot.
        """
        vehicles = v2x_bus.get_all()
        emergency = self._detect_emergency(vehicles)
        if emergency:
            state = self._handle_emergency(emergency, vehicles)
        else:
            self.emergency_active = False
            self.emergency_id = None
            state = self._handle_normal(vehicles)
        # Publica pe V2X Bus ca agent infrastructura
        v2x_bus.publish("INFRA", {
            "id": "INFRA",
            "light": state["light"],
            "recommendation": state["recommendation"],
            "emergency": state["emergency"],
            "x": 400, "y": 400,
            "vx": 0, "vy": 0,
            "state": "normal",
            "priority": "infrastructure",
            "timestamp": time.time(),
        })
        return state
    # ------------------------------------------------------------------
    def _detect_emergency(self, vehicles: dict):
        for vid, v in vehicles.items():
            if v.get("priority") == "emergency":
                ttc = time_to_intersection(v)
                if ttc < TTC_BRAKE * 3:
                    return v
        return None
    def _handle_emergency(self, emv: dict, vehicles: dict) -> dict:
        if not self.emergency_active:
            logger.log_info(f"SEMAFOR: urgenta detectata — {emv['id']} are prioritate")
        self.emergency_active = True
        self.emergency_id = emv["id"]
        self.light = "green"
        rec = f"URGENTA: drum liber pentru {emv['id']}"
        return {
            "light": "green",
            "phase": self.phase,
            "emergency": True,
            "emergency_vehicle": emv["id"],
            "recommendation": rec,
            "green_for": [emv["id"]],
            "red_for": [vid for vid in vehicles if vid not in (emv["id"], "INFRA")],
        }
    def _handle_normal(self, vehicles: dict) -> dict:
        # Ciclu semafor: verde → galben → rosu → verde
        self.timer += 1
        total = GREEN_TICKS + YELLOW_TICKS + RED_TICKS
        pos = self.timer % total
        if pos < GREEN_TICKS:
            self.light = "green"
        elif pos < GREEN_TICKS + YELLOW_TICKS:
            self.light = "yellow"
        else:
            self.light = "red"
        # Log la schimbare faza
        if self.light != self._last_light:
            logger.log_info(f"SEMAFOR: {self._last_light} → {self.light}")
            self._last_light = self.light
        green_for = []
        red_for = []
        for vid, v in vehicles.items():
            if vid == "INFRA":
                continue
            moving_ns = abs(v.get("vy", 0)) > abs(v.get("vx", 0))
            if (self.phase == "NS" and moving_ns) or (self.phase == "EW" and not moving_ns):
                green_for.append(vid)
            else:
                red_for.append(vid)
        return {
            "light": self.light,
            "phase": self.phase,
            "emergency": False,
            "emergency_vehicle": None,
            "recommendation": f"phase={self.phase}, light={self.light}",
            "green_for": green_for,
            "red_for": red_for,
        }
