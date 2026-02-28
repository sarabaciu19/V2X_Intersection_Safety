"""
services/infrastructure.py — Agentul semafor inteligent V2I
"""
import math
import time as _time
from services import v2x_bus as _bus
from utils import logger
GREEN_TICKS  = 150   # 5s la 30 FPS
YELLOW_TICKS = 30    # 1s
RED_TICKS    = 150   # 5s
class InfrastructureAgent:
    def __init__(self, intersection_x=400, intersection_y=400):
        self.intersection_x   = intersection_x
        self.intersection_y   = intersection_y
        self.light            = "green"
        self.timer            = 0
        self.emergency_active = False
        self.emergency_id     = None
        self._last_light      = ""
    # ------------------------------------------------------------------
    # Apelat de engine la fiecare tick (fara argumente)
    # ------------------------------------------------------------------
    def update(self) -> dict:
        vehicles = {
            k: v for k, v in _bus.get_all().items()
            if k != "INFRA" and isinstance(v, dict) and "x" in v
        }
        emergency = self._detect_emergency(vehicles)
        if emergency:
            self.light            = "green"
            self.emergency_active = True
            self.emergency_id     = emergency["id"]
            self.timer            = 0
        else:
            self.emergency_active = False
            self.emergency_id     = None
            self._tick_cycle()
        approaching = self._detect_approaching(vehicles)
        state = {
            "light":             self.light,
            "emergency":         self.emergency_active,
            "emergency_vehicle": self.emergency_id,
            "approaching":       approaching,
            "risk_alert":        len(approaching) >= 2,
            "recommendation":    f"light={self.light}",
            "green_for":         [],
            "red_for":           [],
        }
        _bus.publish("INFRA", {
            "id": "INFRA",
            **state,
            "x": self.intersection_x,
            "y": self.intersection_y,
            "vx": 0, "vy": 0,
            "state": "normal",
            "priority": "infrastructure",
            "timestamp": _time.time(),
        })
        return state
    # ------------------------------------------------------------------
    def _tick_cycle(self):
        self.timer += 1
        total = GREEN_TICKS + YELLOW_TICKS + RED_TICKS
        pos   = self.timer % total
        if pos < GREEN_TICKS:
            self.light = "green"
        elif pos < GREEN_TICKS + YELLOW_TICKS:
            self.light = "yellow"
        else:
            self.light = "red"
        if self.light != self._last_light:
            logger.log_info(f"SEMAFOR: {self._last_light or '?'} → {self.light}")
            self._last_light = self.light
    def _detect_emergency(self, vehicles: dict):
        for vid, v in vehicles.items():
            if v.get("priority") == "emergency":
                dist = self._dist(v)
                if dist < 250:
                    return v
        return None
    def _detect_approaching(self, vehicles: dict) -> list:
        out = []
        for vid, v in vehicles.items():
            dist = self._dist(v)
            if dist < 300:
                dx  = v["x"] - self.intersection_x
                dy  = v["y"] - self.intersection_y
                dot = dx * v.get("vx", 0) + dy * v.get("vy", 0)
                if dot < 0:
                    out.append({"id": vid, "distance": round(dist, 1)})
        return out
    def _dist(self, v: dict) -> float:
        dx = v["x"] - self.intersection_x
        dy = v["y"] - self.intersection_y
        return math.sqrt(dx**2 + dy**2)
    def get_state(self) -> dict:
        return {
            "light":             self.light,
            "timer":             self.timer,
            "emergency_active":  self.emergency_active,
            "emergency_id":      self.emergency_id,
        }
