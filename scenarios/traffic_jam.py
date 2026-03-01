"""
Scenariu — Ambuteiaj (traffic jam)
6 vehicule inclusiv o ambulanta de urgenta.
Intersectia este aglomerata — V2X trebuie sa deschida culoar pentru urgenta.
"""

NAME = "traffic_jam"
DESCRIPTION = "Ambuteiaj cu urgenta — V2X deschide culoar pentru ambulanta."
NO_SEMAPHORE = False

VEHICLES = [
    {'id': 'A',   'direction': 'N', 'intent': 'straight'},
    {'id': 'B',   'direction': 'V', 'intent': 'straight'},
    {'id': 'C',   'direction': 'S', 'intent': 'left'},
    {'id': 'D',   'direction': 'E', 'intent': 'right'},
    {'id': 'E',   'direction': 'N', 'intent': 'right', 'speed_multiplier': 0.7},
    {'id': 'AMB', 'direction': 'S', 'intent': 'straight', 'priority': 'emergency', 'speed_multiplier': 1.4, 'no_stop': True},
]

