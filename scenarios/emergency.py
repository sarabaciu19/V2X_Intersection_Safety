"""
Scenariu — Vehicul de urgenta
AMB (ambulanta/urgenta) vine din Nord cu viteza mare.
B vine din Vest, C vine din Est — ambele cedeaza vehiculului de urgenta.
Cu V2X: traficul normal cedeaza automat la detectia prioritatii de urgenta.
"""

NAME = "emergency"
DESCRIPTION = "Vehicul de urgenta — traficul normal cedeaza automat cu V2X."
NO_SEMAPHORE = False

VEHICLES = [
    {'id': 'AMB', 'direction': 'N', 'intent': 'straight', 'priority': 'emergency', 'speed_multiplier': 1.5},
    {'id': 'B',   'direction': 'V', 'intent': 'straight'},
    {'id': 'C',   'direction': 'E', 'intent': 'straight'},
]
