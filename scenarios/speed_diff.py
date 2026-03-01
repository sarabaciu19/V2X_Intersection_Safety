"""
Scenariu 3 — Viteze diferite
A vine din Nord cu viteza mare (speed_multiplier=2.0)
B vine din Vest cu viteza mica (speed_multiplier=0.5).
V2X calculeaza TTC si acorda prioritate celui mai rapid.
"""

NAME = "speed_diff"
DESCRIPTION = "Viteze diferite — TTC-urile sunt foarte diferite. V2X prioritizeaza cel mai rapid."
NO_SEMAPHORE = False

VEHICLES = [
    {'id': 'A', 'direction': 'N', 'intent': 'straight', 'speed_multiplier': 2.0},
    {'id': 'B', 'direction': 'V', 'intent': 'straight', 'speed_multiplier': 0.5},
]
