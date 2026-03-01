"""
Scenariu — Multi-vehicul (4 directii)
Cate un vehicul din fiecare directie (N, S, E, V) merge drept.
V2X coordoneaza ordinea de trecere prin intersectie.
"""

NAME = "multi"
DESCRIPTION = "4 vehicule din toate directiile — V2X coordoneaza ordinea."
NO_SEMAPHORE = False

VEHICLES = [
    {'id': 'A', 'direction': 'N', 'intent': 'straight'},
    {'id': 'B', 'direction': 'V', 'intent': 'straight'},
    {'id': 'C', 'direction': 'S', 'intent': 'straight'},
    {'id': 'D', 'direction': 'E', 'intent': 'straight'},
]

