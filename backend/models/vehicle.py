"""
vehicle.py — Clasa Vehicle pentru simulatorul V2X
Format mesaj V2X agreat cu echipa:
{
  "id": "A",
  "x": 10, "y": -150,
  "vx": 0, "vy": 5,
  "intent": "straight",
  "timestamp": 1234567890
}
"""

import time


class Vehicle:
    """
    Reprezintă un vehicul V2X în simulare.

    Sistem de coordonate (agreat cu echipa):
      - Intersecția se află la origine (0, 0)
      - Vehiculele pornesc din ±200 unități față de intersecție
      - Axa X: stânga (−) → dreapta (+)
      - Axa Y: sus (−) → jos (+)

    Unități: poziție în metri (fictivi), viteză în m/tick (1 tick = 100 ms)
    """

    def __init__(
        self,
        vehicle_id: str,
        x: float,
        y: float,
        vx: float,
        vy: float,
        intent: str = "straight",
        priority: str = "normal",
    ):
        self.id = vehicle_id
        self.x = x
        self.y = y
        self.vx = vx          # viteză pe axa X (unități/tick)
        self.vy = vy          # viteză pe axa Y (unități/tick)
        self.intent = intent  # "straight" | "turn_left" | "turn_right"
        self.priority = priority  # "normal" | "emergency"
        self.braking = False  # True când agentul decide să frâneze

    # ------------------------------------------------------------------
    # Mișcare
    # ------------------------------------------------------------------

    def update_position(self) -> None:
        """Avansează vehiculul cu un tick (100 ms)."""
        self.x += self.vx
        self.y += self.vy

    def apply_braking(self, factor: float = 0.5) -> None:
        """Reduce viteza (frânare parțială)."""
        self.vx *= factor
        self.vy *= factor
        self.braking = True

    def stop(self) -> None:
        """Stop complet."""
        self.vx = 0.0
        self.vy = 0.0
        self.braking = True

    # ------------------------------------------------------------------
    # Format V2X
    # ------------------------------------------------------------------

    def to_v2x_message(self) -> dict:
        """
        Returnează mesajul V2X conform formatului agreat cu echipa.
        Se trimite prin Message Bus la fiecare tick.
        """
        return {
            "id": self.id,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "vx": round(self.vx, 3),
            "vy": round(self.vy, 3),
            "intent": self.intent,
            "priority": self.priority,
            "braking": self.braking,
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # Reprezentare
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Vehicle(id={self.id!r}, x={self.x:.1f}, y={self.y:.1f}, "
            f"vx={self.vx:.2f}, vy={self.vy:.2f}, intent={self.intent!r}, "
            f"priority={self.priority!r}, braking={self.braking})"
        )
