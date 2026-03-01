"""
Scenariu 1 — Unghi mort (Perpendicular)
A (90 km/h, N→drept, no_stop) vs B (50 km/h, V→drept).
B vine din DREAPTA lui A → prioritate legala prin regula dreptei.
V2X calculeaza TTC: A vine cu viteza mare → ajunge primul → B cedeaza.
Fara V2X: A nu vede B (cladire in colt) → coliziune garantata.
"""

NAME = "perpendicular"
DESCRIPTION = "Unghi mort — A nu vede B. Fara V2X → coliziune. Cu V2X → B cedeaza."
NO_SEMAPHORE = True

VEHICLES = [
    {'id': 'A', 'direction': 'N', 'intent': 'straight', 'speed_multiplier': 1.8, 'no_stop': True},
    {'id': 'B', 'direction': 'V', 'intent': 'straight', 'speed_multiplier': 1.0},
]
