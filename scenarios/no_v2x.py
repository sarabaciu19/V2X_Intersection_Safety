"""
Scenariu — Fara V2X
A (50 km/h, N→drept, no_stop) si B (50 km/h, V→drept, no_stop, FARA V2X).
spawn_x_offset=-50 pe B => distanta identica pana la punctul de intersectie
→ ajung simultan → coliziune garantata.
B nu are V2X: nu primeste mesajul "cedeaza prioritate" trimis de sistemul V2X.
Fara V2X + cladire in colt = B nu vede A, nu primeste semnal → ACCIDENT.
AEB_DISABLED = True: niciun fallback radar — coliziunea se produce inevitabil.
"""

NAME = "no_v2x"
DESCRIPTION = "Fără V2X — fără AEB — coliziune garantată."
NO_SEMAPHORE = True
AEB_DISABLED = True   # Dezactivează fallback-ul AEB pentru acest scenariu

VEHICLES = [
    {'id': 'A', 'direction': 'N', 'intent': 'straight', 'speed_multiplier': 1.0, 'no_stop': True},
    {'id': 'B', 'direction': 'V', 'intent': 'straight', 'speed_multiplier': 1.0, 'no_stop': True, 'v2x_enabled': False, 'spawn_x_offset': -50},
]



