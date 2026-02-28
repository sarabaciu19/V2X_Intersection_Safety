"""
services/central_system.py — Sistemul central V2X
Reguli prioritate (Codul Rutier Romania):
  1. Semafor rosu — vehiculul NU primeste clearance (obligatoriu)
  2. Vehicul de urgenta — prioritate absoluta (trece si pe rosu)
  3. Regula dreptei — vehiculul din dreapta are prioritate
  4. Viraj stanga cedeaza vehiculelor din fata si din dreapta
"""
import time
from services import v2x_bus as _bus

# Directia care vine din dreapta fata de fiecare directie
RIGHT_OF = {
    'N': 'V',
    'V': 'S',
    'S': 'E',
    'E': 'N',
}


def _get_semaphore_lights() -> dict:
    """Citeste starea semaforului din V2X Bus. Returneaza dict {directie: culoare}."""
    infra = _bus.get_all().get("INFRA", {})
    return infra.get("lights", {})


class CentralSystem:
    def __init__(self):
        self._decisions = []
        self._crossing  = set()

    def decide(self, vehicles):
        """Acorda clearance respectand regulile de prioritate si semaforul."""
        lights = _get_semaphore_lights()

        waiting  = [v for v in vehicles if v.state == 'waiting']
        crossing = [v for v in vehicles if v.state == 'crossing']

        self._crossing = {v.id for v in crossing}

        if not waiting:
            return

        urgency = [v for v in waiting if v.priority == 'emergency']
        normal  = [v for v in waiting if v.priority != 'emergency']

        if urgency:
            for v in urgency:
                if not v.clearance:
                    v.clearance = True
                    self._log(v.id, 'CLEARANCE', reason='urgenta — prioritate absoluta (ignora semafor)')
            for v in normal:
                if v.clearance:
                    v.clearance = False
            return

        # Blocheaza vehiculele pe rosu (retrage clearance daca a schimbat)
        for v in normal:
            light = lights.get(v.direction, 'green')
            if light == 'red':
                if v.clearance:
                    v.clearance = False
                    self._log(v.id, 'STOP', reason=f'semafor rosu pentru directia {v.direction}')
            elif light == 'yellow':
                # Pe galben: daca nu a primit deja clearance, nu i-l dam
                if not v.clearance:
                    self._log(v.id, 'HOLD', reason=f'semafor galben pentru directia {v.direction}')

        # Vehicule eligibile = verde + nu traverseaza altcineva
        eligible = [
            v for v in normal
            if lights.get(v.direction, 'green') == 'green'
        ]

        if not eligible:
            return

        if crossing:
            return

        winner = self._pick_winner(eligible)
        if winner and not winner.clearance:
            winner.clearance = True
            light_reason = f'semafor verde ({winner.direction})'
            self._log(winner.id, 'CLEARANCE', reason=f'prioritate acordata, {light_reason}')

    def _pick_winner(self, waiting):
        if not waiting:
            return None
        if len(waiting) == 1:
            return waiting[0]

        dirs = {v.direction: v for v in waiting}

        for v in waiting:
            right_dir = RIGHT_OF.get(v.direction)
            right_vehicle = dirs.get(right_dir)
            if right_vehicle:
                continue
            if v.intent == 'left':
                others = [o for o in waiting if o.id != v.id and o.intent != 'left']
                if others:
                    continue
            return v

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
