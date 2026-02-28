"""
services/central_system.py — Sistem central de negociere a prioritatii (V2X)

Logica:
  - Vehiculul de urgenta are prioritate maxima.
  - Regula prioritatii la dreapta (conform Codului Rutier).
  - Semaforizare simulata: vehiculele vin pe rand la intersectie,
    cel mai apropiat (TTC minim) primeste clearance-ul.
  - La fiecare tick, cel mult un vehicul poate fi in starea 'crossing'.

Stari vehicul gestionate:
  moving   → vehiculul se deplaseaza normal
  waiting  → vehiculul asteapta clearance la linia de oprire
  crossing → vehiculul a primit clearance si traverseaza
  done     → vehiculul a iesit din intersectie
"""
import time
import math
from typing import List, Any

INTERSECTION_X = 400
INTERSECTION_Y = 400


def _dist(v) -> float:
    dx = INTERSECTION_X - v.x
    dy = INTERSECTION_Y - v.y
    return math.sqrt(dx * dx + dy * dy)


class CentralSystem:
    """Agent central care coordoneaza trecerea vehiculelor prin intersectie."""

    def __init__(self):
        self._decisions: list = []

    def reset(self):
        self._decisions = []

    # ------------------------------------------------------------------
    # Decizie principala — apelata la fiecare tick de SimulationEngine
    # ------------------------------------------------------------------
    def decide(self, vehicles: List[Any]) -> None:
        """
        Acorda clearance vehiculelor care asteapta, respectand prioritatile.
        Permite cel mult UN vehicul simultan in zona de intersectie (crossing).
        Vehiculul de urgenta primeste intotdeauna prioritate.
        """
        if not vehicles:
            return

        # Grupeaza vehiculele pe stari
        crossing  = [v for v in vehicles if v.state == 'crossing']
        waiting   = [v for v in vehicles if v.state == 'waiting']
        moving    = [v for v in vehicles if v.state == 'moving']

        # Vehiculele in miscare care au ajuns la linia de asteptare trec in 'waiting'
        for v in moving:
            if v.is_at_wait_line():
                v.state = 'waiting'
                v.vx = 0.0
                v.vy = 0.0
                waiting.append(v)
                self._log(v.id, 'WAIT', reason='A ajuns la linia de oprire')

        # Daca nimeni nu traverseaza acum, acordam clearance urmatorului
        if not crossing and waiting:
            chosen = self._pick_next(waiting)
            if chosen:
                chosen.clearance = True
                chosen.state = 'crossing'
                chosen.vx = chosen._base_vx
                chosen.vy = chosen._base_vy
                reason = self._reason(chosen, waiting)
                self._log(chosen.id, 'CLEARANCE', reason=reason)

    # ------------------------------------------------------------------
    # Selectia vehiculului prioritar
    # ------------------------------------------------------------------
    def _pick_next(self, waiting: list):
        """Alege vehiculul cu cea mai mare prioritate."""
        # 1. Urgenta
        for v in waiting:
            if v.priority == 'emergency':
                return v

        # 2. Cel mai aproape de intersectie (TTC implicit prin distanta)
        return min(waiting, key=lambda v: _dist(v))

    def _reason(self, chosen, waiting: list) -> str:
        if chosen.priority == 'emergency':
            return 'Vehicul de urgenta — prioritate maxima'
        others = [v for v in waiting if v.id != chosen.id]
        if not others:
            return 'Singurul vehicul la intersectie'
        # Verifica regula dreapta
        return 'Cel mai apropiat de intersectie / regula prioritatii'

    # ------------------------------------------------------------------
    # Logging intern
    # ------------------------------------------------------------------
    def _log(self, vehicle_id: str, action: str, reason: str = '') -> None:
        entry = {
            'timestamp': time.time(),
            'vehicle_id': vehicle_id,
            'action': action,
            'reason': reason,
        }
        self._decisions.append(entry)
        if len(self._decisions) > 500:
            self._decisions = self._decisions[-500:]

    def get_decisions(self) -> list:
        return list(self._decisions)

