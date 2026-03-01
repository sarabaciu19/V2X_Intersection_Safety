"""
Scenariu — Fara V2X
A (50 km/h, N→drept, no_stop) si B (50 km/h, V→drept, no_stop, FARA V2X).
spawn_x_offset=-50 pe B => distanta identica pana la punctul de intersectie
→ ajung simultan → risc de coliziune ridicat.
B nu are V2X: nu primeste mesajul "cedeaza prioritate" trimis de sistemul V2X.
Fara V2X + cladire in colt = B nu vede A, nu primeste semnal.
AEB Fallback: B are camera/radar local (raza 60px ≈ 10m).
  → Cand A intra in raza senzorului local, AEB se activeaza — frana VIOLENTA si TARZIE.
  → Comparatie cu V2X (perpendicular): V2X "vede" de la 200-300px → reactie lina, sigura.
  → AEB: reactia e brusca, intarziata, dar evita impactul fatal.
"""

NAME = "no_v2x"
DESCRIPTION = "Fără V2X — B frânează AEB (radar local, târziu) vs. V2X care evită preventiv."
NO_SEMAPHORE = True

VEHICLES = [
    {'id': 'A', 'direction': 'N', 'intent': 'straight', 'speed_multiplier': 1.0, 'no_stop': True},
    {'id': 'B', 'direction': 'V', 'intent': 'straight', 'speed_multiplier': 1.0, 'no_stop': True, 'v2x_enabled': False, 'spawn_x_offset': -50},
]



