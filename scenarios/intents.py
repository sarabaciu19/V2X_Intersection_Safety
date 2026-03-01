"""
Scenariu — Intentii mixte (drept, stanga, dreapta)
A vine din Nord si merge drept.
B vine din Vest si vireaza la stanga.
C vine din Sud si vireaza la dreapta.
V2X tine cont de intentii la calculul TTC si prioritatilor.
"""

NAME = "intents"
DESCRIPTION = "Intentii mixte — drept, stanga, dreapta. V2X tine cont de traiectorii."
NO_SEMAPHORE = False

VEHICLES = [
    {'id': 'A', 'direction': 'N', 'intent': 'straight'},
    {'id': 'B', 'direction': 'V', 'intent': 'left'},
    {'id': 'C', 'direction': 'S', 'intent': 'right'},
]

