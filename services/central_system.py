"""
services/central_system.py — Sistemul central V2X
Reguli prioritate (Codul Rutier Romania):
  1. Vehicul de urgenta — prioritate absoluta
  2. Regula dreptei — vehiculul din dreapta are prioritate
  3. Viraj stanga cedeaza vehiculelor din fata si din dreapta
  4. Straight > right > left ca ordine generala
"""
import time

# Directia care vine din dreapta fata de fiecare directie
RIGHT_OF = {
    'N': 'V',   # N este la dreapta lui V? Nu — V vine din dreapta lui N
    'V': 'S',
    'S': 'E',
    'E': 'N',
}

class CentralSystem:
    def __init__(self):
        self._decisions = []
        self._crossing  = set()   # vehicule care traverseaza acum

    def decide(self, vehicles):
        """Acorda clearance respectand regulile de prioritate."""
        waiting  = [v for v in vehicles if v.state == 'waiting']
        crossing = [v for v in vehicles if v.state == 'crossing']

        self._crossing = {v.id for v in crossing}

        if not waiting:
            return

        # Sorteaza: urgenta primul, apoi cel care a asteptat mai mult
        urgency = [v for v in waiting if v.priority == 'emergency']
        normal  = [v for v in waiting if v.priority != 'emergency']

        if urgency:
            for v in urgency:
                if not v.clearance:
                    v.clearance = True
                    self._log(v.id, 'CLEARANCE', reason='urgenta — prioritate absoluta')
            # Ceilalti asteapta
            for v in normal:
                if v.clearance:
                    v.clearance = False
            return

        # Daca cineva traverseaza deja — ceilalti asteapta
        if crossing:
            return

        # Niciun vehicul nu traverseaza — acorda clearance urmatorului
        # Gaseste vehiculul cu cea mai mare prioritate
        winner = self._pick_winner(normal)
        if winner and not winner.clearance:
            winner.clearance = True
            self._log(winner.id, 'CLEARANCE', reason=f'prioritate acordata')

    def _pick_winner(self, waiting):
        """Alege vehiculul care are prioritate conform regulilor."""
        if not waiting:
            return None
        if len(waiting) == 1:
            return waiting[0]

        # Verifica regula dreptei
        dirs = {v.direction: v for v in waiting}

        for v in waiting:
            right_dir = RIGHT_OF.get(v.direction)
            right_vehicle = dirs.get(right_dir)
            if right_vehicle:
                # v trebuie sa cedeze lui right_vehicle
                continue
            # v nu are nimeni la dreapta sa din cei care asteapta
            # Verifica si virajul stanga
            if v.intent == 'left':
                # Virajul stanga cedeaza tuturor
                others = [o for o in waiting if o.id != v.id and o.intent != 'left']
                if others:
                    continue
            return v

        # Daca toti se blocheaza reciproc, primul din lista
        return waiting[0]

    def _log(self, vehicle_id, action, reason=''):
        entry = {
            'time':    time.strftime('%H:%M:%S'),
            'agent':   vehicle_id,
            'action':  action,
            'reason':  reason,
            'ttc':     0.0,
        }
        self._decisions.append(entry)

    def reset(self):
        self._decisions = []
        self._crossing  = set()

    def get_decisions(self):
        return list(self._decisions)

    def grant_manual_clearance(self, vehicle_id, vehicles):
        for v in vehicles:
            if v.id == vehicle_id and v.state == 'waiting':
                v.clearance = True
                self._log(vehicle_id, 'CLEARANCE', reason='clearance manual acordat de utilizator')
                return {'ok': True, 'vehicle_id': vehicle_id}
        return {'ok': False, 'reason': f'{vehicle_id} negasit sau nu asteapta'}
