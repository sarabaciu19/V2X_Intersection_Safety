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
from utils import logger

# Directia care vine din dreapta fata de fiecare directie
RIGHT_OF = {
    'N': 'V',
    'V': 'S',
    'S': 'E',
    'E': 'N',
}

# Perechi de directii pe aceeasi strada (sens opus).
# Vehiculele din pereche folosesc benzi separate si pot traversa simultan
# (N↔S = strada verticala, E↔V = strada orizontala).
SAME_ROAD = {frozenset({'N', 'S'}), frozenset({'E', 'V'})}


def _get_semaphore_lights() -> dict:
    """Citeste starea semaforului din V2X Bus. Returneaza dict {directie: culoare}."""
    infra = _bus.get_all().get("INFRA", {})
    return infra.get("lights", {})


class CentralSystem:
    def __init__(self):
        self._decisions   = []
        self._crossing    = set()
        self._has_semaphore = True   # set by engine per scenario

    def set_semaphore_state(self, has_semaphore: bool):
        self._has_semaphore = has_semaphore

    def _paths_conflict(self, v1, v2) -> bool:
        """
        True daca traiectoriile v1 si v2 se pot intersecta fizic in cutia intersectiei.
        Vehiculele pe aceeasi strada (N↔S sau E↔V), mergand drept in sensuri opuse,
        folosesc benzi paralele separate → fara conflict.
        Orice alta combinatie (strazi diferite) → conflict potential.
        """
        dirs = frozenset({v1.direction, v2.direction})
        if dirs in SAME_ROAD:
            # Aceeasi strada, benzi opuse — pot trece simultan
            return False
        # Strazi diferite — traiectoriile se intersecteaza in centrul intersectiei
        return True

    def decide(self, vehicles):
        """Acorda clearance respectand regulile de prioritate si semaforul."""
        lights = _get_semaphore_lights()

        waiting  = [v for v in vehicles if v.state == 'waiting']
        crossing = [v for v in vehicles if v.state == 'crossing']
        self._crossing = {v.id for v in crossing}

        # Urgenta — prioritate absoluta indiferent de semafor
        urgency = [v for v in vehicles if v.priority == 'emergency' and v.state not in ('done',)]
        normal  = [v for v in vehicles if v.priority != 'emergency' and v.state not in ('done',)]

        if urgency:
            for v in urgency:
                if not v.clearance:
                    v.clearance = True
                    self._log(v.id, 'CLEARANCE', reason='urgenta — prioritate absoluta')
            for v in normal:
                v.clearance = False
            return

        # ── Fara semafor: prioritate exclusiv prin TTC ─────────────
        if not self._has_semaphore:
            # Evalueaza toate vehiculele active (moving + braking + waiting)
            # Nu doar pe cele in waiting — asa cel mai rapid primeste clearance devreme
            active = [v for v in normal if v.state not in ('crossing', 'done')]
            self._decide_by_ttc(active, crossing)
            return

        # ── Cu semafor: logica normala (doar waiting) ───────────────
        if not waiting:
            return
        normal_waiting = [v for v in waiting if v.priority != 'emergency']
        lights = _get_semaphore_lights()
        for v in normal_waiting:
            light = lights.get(v.direction, 'green')
            if light == 'red':
                if v.clearance:
                    v.clearance = False
                    self._log(v.id, 'STOP', reason=f'semafor rosu pentru directia {v.direction}')
            elif light == 'yellow':
                if not v.clearance:
                    self._log(v.id, 'HOLD', reason=f'semafor galben pentru directia {v.direction}')

        eligible = [v for v in normal_waiting if lights.get(v.direction, 'green') == 'green']
        if not eligible:
            return

        can_go = [v for v in eligible if not any(self._paths_conflict(v, c) for c in crossing)]
        if not can_go:
            return

        winner = self._pick_winner(can_go)
        if winner and not winner.clearance:
            winner.clearance = True
            self._log(winner.id, 'CLEARANCE',
                      reason=f'prioritate acordata, semafor verde ({winner.direction})')

        for v in can_go:
            if v.clearance:
                continue
            already_going = crossing + [w for w in can_go if w.clearance]
            if not any(self._paths_conflict(v, g) for g in already_going):
                v.clearance = True
                self._log(v.id, 'CLEARANCE',
                          reason=f'semafor verde ({v.direction}), benzi paralele')

    def _decide_by_ttc(self, waiting, crossing):
        """
        Fara semafor — prioritate prin TTC (viteza).
        Vehiculul care ajunge primul (TTC minim) primeste clearance.
        Ceilalti in conflict cu el cedeaza.
        """
        import math

        def get_ttc(v):
            dx = 400 - v.x
            dy = 400 - v.y
            dist = math.sqrt(dx*dx + dy*dy)
            # Folosim viteza de baza (nu viteza curenta) pt TTC real
            spd = math.sqrt(v._base_vx**2 + v._base_vy**2)
            return dist / spd if spd > 0.1 else 999.0

        # Sorteaza dupa TTC (cel mai mic = ajunge primul)
        by_ttc = sorted(waiting, key=get_ttc)

        can_go = []
        for v in by_ttc:
            in_conflict = any(self._paths_conflict(v, g) for g in (crossing + can_go))
            if not in_conflict:
                can_go.append(v)

        for v in waiting:
            if v in can_go:
                if not v.clearance:
                    v.clearance = True
                    ttc = round(get_ttc(v), 2)
                    self._log(v.id, 'CLEARANCE',
                              reason=f'V2V: TTC={ttc}s — viteza mare, trece primul (prioritate prin viteza)')
            else:
                # Retrage clearance daca il avea, si logheza o singura data
                had_clearance = v.clearance
                v.clearance = False
                if had_clearance or not getattr(v, '_yielded_logged', False):
                    ttc = round(get_ttc(v), 2)
                    winner_id = can_go[0].id if can_go else (crossing[0].id if crossing else '?')
                    w_ttc = round(get_ttc(can_go[0]), 2) if can_go else 0
                    self._log(v.id, 'YIELD',
                              reason=f'V2V: TTC={ttc}s > {winner_id} TTC={w_ttc}s — cedeaza (viteza mica, ignorata regula dreptei)')
                    v._yielded_logged = True
            # Reseteaza flag cand primeste clearance
            if v.clearance:
                v._yielded_logged = False

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
            'time':   time.strftime('%H:%M:%S'),
            'agent':  vehicle_id,
            'action': action,
            'reason': reason,
            'ttc':    0.0,
        }
        self._decisions.append(entry)
        # Scrie si in buffer-ul logger — vizibil in EventLog frontend
        logger.log_decision(vehicle_id, action, 0.0, reason)

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
