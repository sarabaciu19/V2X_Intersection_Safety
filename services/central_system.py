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
        self._decisions = []
        self._crossing  = set()
        self._has_semaphore = True  # set by engine per scenario

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

        for v in vehicles:
            if not v.v2x_enabled and v.state not in ('done',):
                pass

        waiting  = [v for v in vehicles if v.state == 'waiting' and v.v2x_enabled]
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

        # ── Fara semafor: prioritate exclusiv prin TTC (viteza) ─────────
        if not self._has_semaphore:
            # Include moving + waiting; exclude cei deja in stare crossing/done/crashed
            active = [v for v in vehicles if v.v2x_enabled
                      and v.state not in ('crossing', 'done', 'crashed')]
            self._decide_by_ttc(active, crossing)
            return

        # ── Cu semafor: logica normala ───────────────────────────────────
        for v in normal:
            light = lights.get(v.direction, 'green')
            if light == 'red':
                if v.clearance:
                    v.clearance = False
                    self._log(v.id, 'STOP', reason=f'semafor rosu pentru directia {v.direction}')
            elif light == 'yellow':
                if not v.clearance:
                    self._log(v.id, 'HOLD', reason=f'semafor galben pentru directia {v.direction}')

        eligible = [v for v in normal if lights.get(v.direction, 'green') == 'green']
        if not eligible:
            return

        can_go = [v for v in eligible if not any(self._paths_conflict(v, c) for c in crossing)]
        if not can_go:
            return

        winner = self._pick_winner(can_go)
        if winner and not winner.clearance:
            winner.clearance = True
            self._log(winner.id, 'CLEARANCE', reason=f'prioritate acordata, semafor verde ({winner.direction})')

        for v in can_go:
            if v.clearance:
                continue
            already_going = [c for c in crossing] + [w for w in can_go if w.clearance]
            if not any(self._paths_conflict(v, g) for g in already_going):
                v.clearance = True
                self._log(v.id, 'CLEARANCE',
                          reason=f'semafor verde ({v.direction}), benzi paralele — traversare simultana permisa')

    def _decide_by_ttc(self, waiting, crossing):
        """
        Fara semafor — prioritate prin TTC (viteza).
        Vehiculul care ajunge primul primeste clearance.
        Daca vehiculul care cedeaza avea prioritate legala (regula dreptei),
        se logheaza YIELD_SPEED_OVERRIDE — regula incalcata prin viteza.
        """
        import math

        def get_ttc(v):
            dx = 400 - v.x
            dy = 400 - v.y
            dist = math.sqrt(dx * dx + dy * dy)
            spd = math.sqrt(v._base_vx ** 2 + v._base_vy ** 2)
            # Se indeparteaza deja de intersectie → nu e relevant
            if spd > 0.1:
                # dot product: daca vehiculul se indeparteaza, TTC e mare
                dot = dx * v._base_vx + dy * v._base_vy
                if dot <= 0 and dist < 60:
                    return 999.0  # deja trecut, nu mai e relevant
            return dist / spd if spd > 0.1 else 999.0

        def get_kmh(v):
            spd = math.sqrt(v._base_vx ** 2 + v._base_vy ** 2)
            return round(spd / 3.0 * 50, 0)

        def has_legal_right_over(v_yield, v_winner) -> bool:
            """True daca v_yield vine din DREAPTA lui v_winner → ar trebui sa aiba prioritate."""
            return v_yield.direction == RIGHT_OF.get(v_winner.direction)

        by_ttc = sorted(waiting, key=get_ttc)
        can_go = []
        for v in by_ttc:
            if not any(self._paths_conflict(v, g) for g in (crossing + can_go)):
                can_go.append(v)

        for v in waiting:
            if v in can_go:
                if not v.clearance:
                    v.clearance = True
                    ttc = round(get_ttc(v), 2)
                    kmh = get_kmh(v)
                    # Verifica daca exista un yielder cu prioritate legala
                    legal_yielders = [
                        w for w in waiting
                        if w not in can_go and has_legal_right_over(w, v)
                        and self._paths_conflict(v, w)
                    ]
                    if legal_yielders:
                        ids = ', '.join(w.id for w in legal_yielders)
                        self._log(v.id, 'CLEARANCE_SPEED',
                                  reason=(
                                      f'⚡ V2X: TTC={ttc}s, {kmh:.0f} km/h — prioritate ACORDATA prin viteza. '
                                      f'ATENTIE: {ids} are prioritate legala (regula dreptei) '
                                      f'dar cedeaza din cauza vitezei mari. '
                                      f'Fara V2X → coliziune garantata.'
                                  ))
                    else:
                        self._log(v.id, 'CLEARANCE',
                                  reason=f'V2V: TTC={ttc}s, {kmh:.0f} km/h — ajunge primul, trece')
            else:
                had = v.clearance
                v.clearance = False
                winner = can_go[0] if can_go else (crossing[0] if crossing else None)
                if had or not getattr(v, '_yielded_logged', False):
                    ttc = round(get_ttc(v), 2)
                    kmh = get_kmh(v)
                    if winner:
                        w_ttc = round(get_ttc(winner), 2) if winner in waiting else 0
                        w_kmh = get_kmh(winner)
                        if has_legal_right_over(v, winner):
                            self._log(v.id, 'YIELD_SPEED_OVERRIDE',
                                      reason=(
                                          f'⚠ V2X: {v.id} are prioritate LEGALA (vine din dreapta lui {winner.id}), '
                                          f'DAR {winner.id} vine cu {w_kmh:.0f} km/h (TTC={w_ttc}s) vs '
                                          f'{v.id} cu {kmh:.0f} km/h (TTC={ttc}s). '
                                          f'Sistemul V2X forteaza cedarea — regula dreptei INCALCATA prin viteza.'
                                      ))
                        else:
                            self._log(v.id, 'YIELD',
                                      reason=f'V2V: TTC={ttc}s ({kmh:.0f} km/h) > {winner.id} TTC={w_ttc}s ({w_kmh:.0f} km/h) — cedeaza')
                    else:
                        self._log(v.id, 'YIELD', reason=f'V2V: TTC={ttc}s — cedeaza')
                    v._yielded_logged = True
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
