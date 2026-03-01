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
        # Aceeasi directie — in coloana, fara conflict de traiectorie
        if v1.direction == v2.direction:
            return False
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
        # Doar vehiculele crossing care sunt INCA in cutia intersectiei blocheaza altii
        # Odata ce au iesit fizic din intersectie, nu mai blocheaza clearance-ul
        crossing = [v for v in vehicles if v.state == 'crossing' and v._is_inside_intersection()]
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

        # ── Fara semafor: prioritate exclusiv prin regula dreptei + TTC ──
        if not self._has_semaphore:
            # Lucreaza DOAR cu vehiculele care s-au oprit la linia de stop (state='waiting')
            # Vehiculele moving/no_stop nu se opresc si nu au nevoie de clearance
            waiting_at_line = [v for v in vehicles if v.v2x_enabled
                               and v.state == 'waiting']
            self._decide_by_ttc(waiting_at_line, crossing)
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

        # ── Alege winner-ul prin regula dreptei ──────────────────────────
        winner = self._pick_winner(can_go)
        if not winner:
            return

        # Acorda clearance winner-ului
        if not winner.clearance:
            right_dir = RIGHT_OF.get(winner.direction)
            has_right_blocker = any(
                v.direction == right_dir and self._paths_conflict(winner, v)
                for v in can_go if v.id != winner.id
            )
            if has_right_blocker:
                reason = f'prioritate acordata: nimeni din dreapta ({winner.direction}), semafor verde'
            else:
                reason = f'regula dreptei — fara vehicul din dreapta, semafor verde ({winner.direction})'
            winner.clearance = True
            self._log(winner.id, 'CLEARANCE', reason=reason)

        # Revoca clearance celor care trebuie sa cedeze winner-ului
        for v in can_go:
            if v.id == winner.id:
                continue
            if self._paths_conflict(v, winner):
                # Conflicteaza cu winner-ul care e deja in miscare/waiting → asteapta
                if v.clearance:
                    v.clearance = False
                    self._log(v.id, 'YIELD',
                              reason=f'cedeaza dreptei — {winner.id} are prioritate')

        # Acorda clearance si celorlalti care au traiectorii paralele (fara conflict cu nimeni aprobat)
        already_going = [c for c in crossing] + [v for v in can_go if v.clearance]
        for v in can_go:
            if v.clearance:
                continue
            if not any(self._paths_conflict(v, g) for g in already_going):
                v.clearance = True
                self._log(v.id, 'CLEARANCE',
                          reason=f'semafor verde ({v.direction}), benzi paralele — traversare simultana permisa')
                already_going.append(v)



    def _decide_by_ttc(self, waiting, crossing):
        """
        Fara semafor — prioritate prin regula dreptei + TTC.
        Reguli aplicate in ordine:
          1. Urgenta → prioritate absoluta (deja tratata in decide())
          2. Regula dreptei → daca vehiculul din dreapta are TTC comparabil (diferenta < TTC_OVERRIDE_DELTA),
             cel din stanga CEDEAZA indiferent de viteza
          3. TTC override → daca diferenta de TTC e mare (>= TTC_OVERRIDE_DELTA), cel mai rapid trece
             (se logheaza YIELD_SPEED_OVERRIDE daca incalca regula dreptei)
        """
        import math

        TTC_OVERRIDE_DELTA = 2.0   # sec — diferenta minima de TTC ca viteza sa bata regula dreptei

        def get_ttc(v):
            dx = 400 - v.x
            dy = 400 - v.y
            dist = math.sqrt(dx * dx + dy * dy)
            # Folosim viteza de BAZA (nu cea curenta care poate fi 0 daca stau la stop)
            spd  = math.sqrt(v._base_vx ** 2 + v._base_vy ** 2)
            if spd > 0.1:
                dot = dx * v._base_vx + dy * v._base_vy
                if dot <= 0 and dist < 60:
                    return 999.0   # deja trecut intersectia
            return dist / spd if spd > 0.1 else 999.0

        def get_kmh(v):
            spd = math.sqrt(v._base_vx ** 2 + v._base_vy ** 2)
            return round(spd / 3.0 * 50, 0)

        def comes_from_right_of(other, v) -> bool:
            """True daca `other` vine din DREAPTA lui `v` → `other` are prioritate."""
            return other.direction == RIGHT_OF.get(v.direction)

        # ── Pasul 1: determina cine trebuie sa cedeze fata de cine ───────
        # Pentru fiecare vehicul, calculeaza daca trebuie sa cedeze cuiva.
        ttc_map = {v.id: get_ttc(v) for v in waiting}

        # yielders = set de id-uri care trebuie sa cedeze
        yielders = set()

        for v in waiting:
            my_ttc = ttc_map[v.id]
            if my_ttc >= 900:
                continue   # deja trecut sau stationat — nu e relevant

            for other in waiting:
                if other.id == v.id:
                    continue
                if not self._paths_conflict(v, other):
                    continue   # benzi paralele — nu se ciocnesc
                other_ttc = ttc_map[other.id]
                if other_ttc >= 900:
                    continue

                # Regula dreptei: daca `other` vine din dreapta lui `v`
                if comes_from_right_of(other, v):
                    ttc_diff = my_ttc - other_ttc
                    if ttc_diff >= -TTC_OVERRIDE_DELTA:
                        # `other` ajunge primul SAU la timp comparabil → `v` cedeaza (regula dreptei)
                        yielders.add(v.id)
                    # else: `v` vine cu MULT mai repede (>2s avans) → TTC override, `v` nu cedeaza

        # ── Pasul 2: acorda clearance ────────────────────────────────────
        can_go  = [v for v in waiting if v.id not in yielders]
        must_yield = [v for v in waiting if v.id in yielders]

        # Filtreaza can_go: nu acorda clearance daca cineva din crossing conflictueaza
        can_go = [v for v in can_go
                  if not any(self._paths_conflict(v, c) for c in crossing)]

        # Chiar din can_go, trebuie sa treaca doar UNUL (cel mai rapid / cel ales), 
        # si ceilalti doar daca au traiectorii paralele neconflictuale cu el.
        can_go_final = []
        for v in can_go:
            if not any(self._paths_conflict(v, g) for g in can_go_final):
                can_go_final.append(v)
        
        # Cei care au fost scosi din can_go din cauza conflictelor intamplatoare devin yielders temporari
        for v in can_go:
            if v not in can_go_final:
                must_yield.append(v)

        for v in can_go_final:
            if not v.clearance:
                v.clearance = True
                ttc  = round(ttc_map[v.id], 2)
                kmh  = get_kmh(v)
                # Verifica daca exista un yielder care ar fi avut prioritate legala
                # dar cedeaza din cauza TTC override
                legal_yielders_overridden = [
                    w for w in must_yield
                    if comes_from_right_of(w, v)
                    and self._paths_conflict(v, w)
                    and ttc_map[v.id] < ttc_map[w.id] - TTC_OVERRIDE_DELTA
                ]
                if legal_yielders_overridden:
                    ids = ', '.join(w.id for w in legal_yielders_overridden)
                    self._log(v.id, 'CLEARANCE_SPEED',
                              reason=(
                                  f'⚡ V2X: TTC={ttc}s, {kmh:.0f} km/h — prioritate ACORDATA prin viteza. '
                                  f'ATENTIE: {ids} are prioritate legala (regula dreptei) '
                                  f'dar cedeaza din cauza vitezei mari. '
                                  f'Fara V2X → coliziune garantata.'
                              ))
                else:
                    self._log(v.id, 'CLEARANCE',
                              reason=f'V2V: TTC={ttc}s, {kmh:.0f} km/h — ajunge primul / prioritate dreapta, trece')
            v._yielded_logged = False

        for v in must_yield:
            had = v.clearance
            v.clearance = False
            if had or not getattr(v, '_yielded_logged', False):
                ttc  = round(ttc_map[v.id], 2)
                kmh  = get_kmh(v)
                # Gaseste vehiculul fata de care cedeaza
                blocker = next(
                    (o for o in can_go if self._paths_conflict(v, o)),
                    can_go[0] if can_go else (crossing[0] if crossing else None)
                )
                if blocker:
                    b_ttc = round(ttc_map.get(blocker.id, get_ttc(blocker)), 2)
                    b_kmh = get_kmh(blocker)
                    if comes_from_right_of(v, blocker):
                        # v vine din dreapta lui blocker → blocker l-a depasit prin viteza
                        self._log(v.id, 'YIELD_SPEED_OVERRIDE',
                                  reason=(
                                      f'⚠ V2X: {v.id} are prioritate LEGALA (vine din dreapta lui {blocker.id}), '
                                      f'DAR {blocker.id} vine cu {b_kmh:.0f} km/h (TTC={b_ttc}s) vs '
                                      f'{v.id} cu {kmh:.0f} km/h (TTC={ttc}s). '
                                      f'Sistemul V2X forteaza cedarea — regula dreptei INCALCATA prin viteza.'
                                  ))
                    else:
                        self._log(v.id, 'YIELD',
                                  reason=(
                                      f'V2V: cedeaza dreptei — {blocker.id} vine din dreapta '
                                      f'(TTC={b_ttc}s, {b_kmh:.0f} km/h)'
                                  ))
                else:
                    self._log(v.id, 'YIELD', reason=f'V2V: TTC={ttc}s — cedeaza')
                v._yielded_logged = True

    def _pick_winner(self, waiting):
        """
        Alege vehiculul cu cel mai mare drept de trecere respectând:
        1. Regula dreptei — vehiculul din dreapta are prioritate
        2. Viraj stânga cedează față de cei care merg drept/dreapta
        Returnează vehiculul care nu are pe nimeni la dreapta lui (cu conflict activ).
        """
        if not waiting:
            return None
        if len(waiting) == 1:
            return waiting[0]

        dirs = {v.direction: v for v in waiting}

        for v in waiting:
            # Verifică dacă există un vehicul la dreapta lui v care îi conflictează traiectoria
            right_dir = RIGHT_OF.get(v.direction)
            right_vehicle = dirs.get(right_dir)
            if right_vehicle and self._paths_conflict(v, right_vehicle):
                continue  # cineva din dreapta are prioritate față de v

            # Verifică viraj stânga: cedează față de cei care merg drept sau la dreapta
            if v.intent == 'left':
                others_straight = [o for o in waiting if o.id != v.id
                                   and o.intent != 'left'
                                   and self._paths_conflict(v, o)]
                if others_straight:
                    continue

            return v

        # Dacă toți sunt în cerc (blocaj circular rar) → alege primul ca tiebreak
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
