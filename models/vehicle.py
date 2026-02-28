"""
models/vehicle.py — Clasa Vehicle
state: 'normal' | 'braking' | 'yielding'
Intersecție la (400, 400) px
"""

import time


class Vehicle:
    def __init__(self, id: str, x: float, y: float, vx: float, vy: float,
                 priority: str = "normal"):
        self.id = id
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.priority = priority          # "normal" | "emergency"
        self.state: str = "normal"        # "normal" | "braking" | "yielding"

        # stare inițială pentru reset()
        self._init = (x, y, vx, vy)

    def update(self) -> None:
        """Mișcă vehiculul un tick."""
        self.x += self.vx
        self.y += self.vy

    def reset(self) -> None:
        """Resetează la poziția inițială."""
        self.x, self.y, self.vx, self.vy = self._init
        self.state = "normal"

    def to_dict(self) -> dict:
        """Serializare pentru V2X Bus și frontend."""
        return {
            "id": self.id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "vx": round(self.vx, 3),
            "vy": round(self.vy, 3),
            "state": self.state,
            "priority": self.priority,
            "timestamp": time.time(),
        }

    def __repr__(self) -> str:
        return (f"Vehicle(id={self.id!r}, x={self.x:.1f}, y={self.y:.1f}, "
                f"vx={self.vx:.2f}, vy={self.vy:.2f}, state={self.state!r})")
