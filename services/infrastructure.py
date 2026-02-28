"""
services/infrastructure.py - Agentul semafor inteligent V2I
Semafoare per directie:
  Faza A (green): N si S au verde, E si V au rosu
  Faza B (green): E si V au verde, N si S au rosu
  Intre faze: yellow pentru directia care tocmai a avut verde
"""
import math
import time as _time
from services import v2x_bus as _bus
from utils import logger

GREEN_TICKS  = 150   # 5s la 30 FPS
YELLOW_TICKS = 30    # 1s

# Grupuri de directii
PHASE_A_DIRS = ("N", "S")
PHASE_B_DIRS = ("E", "V")

# Ciclu complet: [A_green, A_yellow, B_green, B_yellow]
CYCLE = [
    ("A_green",  GREEN_TICKS),
    ("A_yellow", YELLOW_TICKS),
    ("B_green",  GREEN_TICKS),
    ("B_yellow", YELLOW_TICKS),
]
CYCLE_TOTAL = sum(d for _, d in CYCLE)


def _phase_at(tick: int) -> str:
    pos = tick % CYCLE_TOTAL
    acc = 0
    for name, dur in CYCLE:
        acc += dur
        if pos < acc:
            return name
    return CYCLE[-1][0]


def light_for_direction(phase: str, direction: str) -> str:
    if direction in PHASE_A_DIRS:
        if phase == "A_green":   return "green"
        if phase == "A_yellow":  return "yellow"
        return "red"
    else:
        if phase == "B_green":   return "green"
        if phase == "B_yellow":  return "yellow"
        return "red"


class InfrastructureAgent:
    def __init__(self, intersection_x=400, intersection_y=400):
        self.intersection_x   = intersection_x
        self.intersection_y   = intersection_y
        self.timer            = 0
        self.emergency_active = False
        self.emergency_id     = None
        self._last_phase      = ""
        self.light            = "green"
        self.lights: dict     = {d: "red" for d in ("N", "S", "E", "V")}
        self._update_lights_from_phase(_phase_at(0))

    def _update_lights_from_phase(self, phase: str):
        for d in ("N", "S", "E", "V"):
            self.lights[d] = light_for_direction(phase, d)
        if "green" in self.lights.values():
            self.light = "green"
        elif "yellow" in self.lights.values():
            self.light = "yellow"
        else:
            self.light = "red"

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
            emerg_dir = emergency.get("direction", "N")
            for d in ("N", "S", "E", "V"):
                self.lights[d] = "green" if d == emerg_dir else "red"
            self.light            = "green"
            self.emergency_active = True
            self.emergency_id     = emergency["id"]
        else:
            self.emergency_active = False
            self.emergency_id     = None
            self._tick_cycle()

        green_for = [d for d, l in self.lights.items() if l == "green"]
        red_for   = [d for d, l in self.lights.items() if l == "red"]

        approaching = self._detect_approaching(vehicles)
        state = {
            "light":             self.light,
            "lights":            dict(self.lights),
            "emergency":         self.emergency_active,
            "emergency_vehicle": self.emergency_id,
            "approaching":       approaching,
            "risk_alert":        len(approaching) >= 2,
            "recommendation":    f"light={self.light}",
            "green_for":         green_for,
            "red_for":           red_for,
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
        phase = _phase_at(self.timer)
        self._update_lights_from_phase(phase)
        if phase != self._last_phase:
            green_dirs = [d for d, l in self.lights.items() if l == "green"]
            logger.log_info(
                f"SEMAFOR: faza {self._last_phase or '?'} -> {phase} | verde: {green_dirs}"
            )
            self._last_phase = phase

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
            "light":            self.light,
            "lights":           dict(self.lights),
            "timer":            self.timer,
            "emergency_active": self.emergency_active,
            "emergency_id":     self.emergency_id,
        }
