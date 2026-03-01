"""
models/vehicle.py — Vehicul cu banda si intentie
Intersectie cu 4 directii: N, S, E, V
Fiecare directie are 2 benzi:
  - Banda dreapta (in):  vehicule care se apropie de intersectie
  - Banda stanga (out):  vehicule care pleaca din intersectie
Benzi (offset fata de centrul drumului, latimea benzii = 30px):
  N/S drum vertical (x=400): banda_in x=415, banda_out x=385
  E/V drum orizontal (y=400): banda_in y=415, banda_out y=385
Intent: 'straight' | 'left' | 'right'
"""
import time
import math
# Geometrie intersectie
INTERSECTION_X = 400
INTERSECTION_Y = 400
LANE_WIDTH     = 50   # px per banda
ROAD_WIDTH     = LANE_WIDTH * 2  # 2 benzi per directie = 100px
# Offset banda (fata de centrul drumului)
LANE_IN_OFFSET  = -25   # vehicule care vin spre intersectie (banda stanga)
LANE_OUT_OFFSET =  25   # vehicule care pleaca (banda dreapta)

# Zona de franare graduala inainte de linia de stop (px)
BRAKE_ZONE_DIST  = 90    # incepe sa franeze la 90px de linia de stop
FOLLOW_YIELD_DIST = 40    # px
MIN_SPEED_FACTOR = 0.3   # viteza minima (creeping)
MARGIN           = 50    # px in afara canvasului pana dispare
# Masina are ~18px jumatate de lungime. Oprim masina cu 20px inainte de linia alba:
# STOP_MARGIN = 8 (offset linie) + 20 (spatiu) = 28px fata de marginea drumului
STOP_MARGIN = 28
# Pozitii de start per directie (pe banda IN)
SPAWN = {
    'N': (INTERSECTION_X + LANE_IN_OFFSET, 50),    # vine din Nord, merge spre Sud
    'S': (INTERSECTION_X - LANE_IN_OFFSET, 750),   # vine din Sud, merge spre Nord
    'E': (750, INTERSECTION_Y + LANE_IN_OFFSET),   # vine din Est, merge spre Vest
    'V': (50,  INTERSECTION_Y - LANE_IN_OFFSET),   # vine din Vest, merge spre Est
}
# Viteza initiala per directie (px/tick)
VELOCITY = {
    'N': (0,  +3),   # spre Sud
    'S': (0,  -3),   # spre Nord
    'E': (-3, 0),    # spre Vest
    'V': (+3, 0),    # spre Est
}

# Directia de iesire dupa viraj: (entry_direction, intent) -> exit_direction
# Trafic pe STANGA (UK):
#   N (merge spre Sud↓): stanga=spre Est(V, x↑)  dreapta=spre Vest(E, x↓)
#   S (merge spre Nord↑): stanga=spre Vest(E, x↓) dreapta=spre Est(V, x↑)
#   E (merge spre Vest←): stanga=spre Sud(N, y↑)  dreapta=spre Nord(S, y↓)
#   V (merge spre Est→): stanga=spre Nord(S, y↓)  dreapta=spre Sud(N, y↑)
EXIT_DIRECTION = {
    ('N', 'straight'): 'N',
    ('N', 'left'):     'V',   # stanga din N → spre Est (V, vx>0)
    ('N', 'right'):    'E',   # dreapta din N → spre Vest (E, vx<0)
    ('S', 'straight'): 'S',
    ('S', 'left'):     'E',   # stanga din S → spre Vest (E, vx<0)
    ('S', 'right'):    'V',   # dreapta din S → spre Est (V, vx>0)
    ('E', 'straight'): 'E',
    ('E', 'left'):     'N',   # stanga din E → spre Sud (N, vy>0)
    ('E', 'right'):    'S',   # dreapta din E → spre Nord (S, vy<0)
    ('V', 'straight'): 'V',
    ('V', 'left'):     'S',   # stanga din V → spre Nord (S, vy<0)
    ('V', 'right'):    'N',   # dreapta din V → spre Sud (N, vy>0)
}

# Conversie km/h ↔ speed_multiplier
# 3 px/tick × 30 FPS = 90 px/s = viteza de baza
# Definim: speed_multiplier=1.0 ↔ 50 km/h
# => 1 km/h = speed_multiplier / 50
KMH_BASE = 50.0   # km/h la speed_multiplier=1.0

def kmh_to_multiplier(kmh: float) -> float:
    return round(max(0.1, kmh / KMH_BASE), 3)

def multiplier_to_kmh(mult: float) -> int:
    return max(1, round(mult * KMH_BASE))

class Vehicle:
    def __init__(self, id: str, direction: str, intent: str = 'straight',
                 priority: str = 'normal', speed_multiplier: float = 1.0,
                 v2x_enabled: bool = True, spawn_tick: int = 0,
                 no_stop: bool = False):
        """
        no_stop: True = vehiculul NU se opreste la linia de stop (merge cu viteza constant).
                 Folosit pentru vehicule cu viteza mare care au prioritate prin TTC.
        """
        self.id        = id
        self.direction = direction
        self.intent    = intent
        self.priority  = priority
        self.v2x_enabled = v2x_enabled
        self.spawn_tick = spawn_tick
        self.no_stop   = no_stop
        self.agent_yield = False   # setat de agentul LLM — opreste vehiculul inainte de intersectie
        self.state     = 'moving'   # moving | waiting | crossing | crashed | done
        sx, sy    = SPAWN[direction]
        vx0, vy0  = VELOCITY[direction]
        self.speed_multiplier = speed_multiplier
        self.x    = float(sx)
        self.y    = float(sy)
        self.vx   = vx0 * speed_multiplier
        self.vy   = vy0 * speed_multiplier
        self._base_vx = self.vx
        self._base_vy = self.vy
        self._init    = (self.x, self.y, self.vx, self.vy)
        # Directia de iesire (poate diferi de direction dupa viraj)
        self._exit_dir: str = EXIT_DIRECTION.get((direction, intent), direction)
        self._turned: bool = False   # a efectuat deja virajul in intersectie?
        # Decizie sistem central
        self.clearance = False   # True = sistemul i-a dat voie sa treaca
        self.wait_line = self._calc_wait_line()

    def _calc_wait_line(self) -> float:
        """Pozitia unde masina se opreste — cu STOP_MARGIN px inainte de linia alba."""
        if self.direction == 'N':
            return INTERSECTION_Y - ROAD_WIDTH / 2 - STOP_MARGIN
        if self.direction == 'S':
            return INTERSECTION_Y + ROAD_WIDTH / 2 + STOP_MARGIN
        if self.direction == 'E':
            return INTERSECTION_X + ROAD_WIDTH / 2 + STOP_MARGIN
        if self.direction == 'V':
            return INTERSECTION_X - ROAD_WIDTH / 2 - STOP_MARGIN

    def _is_inside_intersection(self) -> bool:
        """Vehiculul se afla in cutia intersectiei."""
        return (abs(self.x - INTERSECTION_X) <= ROAD_WIDTH / 2 + 5 and
                abs(self.y - INTERSECTION_Y) <= ROAD_WIDTH / 2 + 5)

    def _is_beyond_intersection(self) -> bool:
        """Vehiculul a depasit centrul intersectiei pe directia sa."""
        if self.direction == 'N': return self.y > INTERSECTION_Y + 20
        if self.direction == 'S': return self.y < INTERSECTION_Y - 20
        if self.direction == 'E': return self.x < INTERSECTION_X - 20
        if self.direction == 'V': return self.x > INTERSECTION_X + 20
        return False

    def _has_reached_turn_point(self) -> bool:
        """
        Vehiculul a ajuns in centrul intersectiei pe axa sa de intrare —
        momentul optim pentru a aplica virajul.
        """
        if self.direction == 'N':   # merge spre Sud (y creste)
            return self.y >= INTERSECTION_Y - 5
        if self.direction == 'S':   # merge spre Nord (y scade)
            return self.y <= INTERSECTION_Y + 5
        if self.direction == 'E':   # merge spre Vest (x scade)
            return self.x <= INTERSECTION_X + 5
        if self.direction == 'V':   # merge spre Est (x creste)
            return self.x >= INTERSECTION_X - 5
        return False

    def _apply_turn(self) -> None:
        """Aplica noul vector viteza si snapuieste vehiculul pe banda corecta de iesire."""
        speed = math.sqrt(self._base_vx**2 + self._base_vy**2)
        vx_new, vy_new = VELOCITY[self._exit_dir]
        self._base_vx = vx_new / 3.0 * speed
        self._base_vy = vy_new / 3.0 * speed
        # Snap pe axa perpendiculara sensului de iesire, pe banda IN a directiei de iesire
        # Spawn[exit_dir] ne da pozitia corecta pe banda
        sx, sy = SPAWN[self._exit_dir]
        if self._exit_dir in ('V', 'E'):   # iesire orizontala → fixam y
            self.y = float(sy)
        else:                               # iesire verticala → fixam x
            self.x = float(sx)
        self._turned = True

    def dist_to_intersection(self) -> float:
        dx = INTERSECTION_X - self.x
        dy = INTERSECTION_Y - self.y
        return math.sqrt(dx*dx + dy*dy)

    def is_at_wait_line(self) -> bool:
        """Vehiculul a ajuns la linia de asteptare."""
        if self.direction == 'N':
            return self.y >= self.wait_line
        if self.direction == 'S':
            return self.y <= self.wait_line
        if self.direction == 'E':
            return self.x <= self.wait_line
        if self.direction == 'V':
            return self.x >= self.wait_line

    def is_past_intersection(self) -> bool:
        """Vehiculul a depasit centrul intersectiei (folosind directia de iesire)."""
        d = self._exit_dir
        if d == 'N':   return self.y > INTERSECTION_Y + ROAD_WIDTH // 2 + 5
        if d == 'S':   return self.y < INTERSECTION_Y - ROAD_WIDTH // 2 - 5
        if d == 'E':   return self.x < INTERSECTION_X - ROAD_WIDTH // 2 - 5
        if d == 'V':   return self.x > INTERSECTION_X + ROAD_WIDTH // 2 + 5
        return False

    def is_off_screen(self) -> bool:
        """Vehiculul a iesit complet din canvas (folosind directia de iesire)."""
        d = self._exit_dir
        if d == 'N':   return self.y > 800 + MARGIN
        if d == 'S':   return self.y < -MARGIN
        if d == 'E':   return self.x < -MARGIN
        if d == 'V':   return self.x > 800 + MARGIN
        return False

    def heading_angle(self) -> float:
        """Unghi de orientare (radiani) bazat pe viteza curenta, pentru randare."""
        if self._base_vx == 0 and self._base_vy == 0:
            # Stationat — pastreaza directia de intrare
            import math as _m
            vx0, vy0 = VELOCITY[self.direction]
            return _m.atan2(vx0, -vy0)
        return math.atan2(self._base_vx, -self._base_vy)

    def _dist_to_wait_line(self) -> float:
        """Distanta ramasa pana la linia de stop (pozitiva = inca n-a ajuns)."""
        if self.direction == 'N':   return self.wait_line - self.y
        if self.direction == 'S':   return self.y - self.wait_line
        if self.direction == 'E':   return self.x - self.wait_line
        if self.direction == 'V':   return self.wait_line - self.x
        return 999.0

    # ── Following distance ───────────────────────────────────────────
    FOLLOW_MIN_DIST   = 55   # opreste complet daca e mai aproape de atat (px)
    FOLLOW_BRAKE_DIST = 180  # incepe franarea de la aceasta distanta (px)

    def dist_ahead(self, other) -> float:
        """
        Distanta fata de un alt vehicul care e IN FATA pe aceeasi directie.
        Returneaza float mare daca e in spate sau pe alta directie.
        """
        if other.direction != self.direction:
            return 9999.0
        if self.direction == 'N':
            d = other.y - self.y
        elif self.direction == 'S':
            d = self.y - other.y
        elif self.direction == 'E':
            d = self.x - other.x
        else:  # V
            d = other.x - self.x
        return d if d > 0 else 9999.0

    def _desired_speed_factor(self, vehicles_same_dir: list, all_vehicles: list = None) -> float:
        """
        Calculeaza factorul de viteza dorit (0..1) tinand cont de:
        - distanta fata de vehiculul din fata (following)
        - distanta fata de linia de stop (daca nu are clearance)
        Vehiculele FARA V2X respecta semaforul si following-ul,
        dar nu primesc clearance de la sistemul central.
        """
        # Decizia LLM: agentul a decis YIELD — opreste inainte de intersectie
        if self.agent_yield and not self._is_inside_intersection():
            return 0.0

        factor = 1.0

        # Following: cauta cel mai aproape vehicul din fata
        closest_dist = 9999.0
        closest_v = None
        for other in vehicles_same_dir:
            if other.id == self.id:
                continue
            # Ignora vehiculele care au virat deja — nu mai sunt pe acelasi traseu
            if getattr(other, '_turned', False):
                continue
            # Ignora vehiculele crashed/done — nu mai sunt obstacol
            if other.state in ('done', 'crashed'):
                continue
            d = self.dist_ahead(other)
            if d < closest_dist:
                closest_dist = d
                closest_v = other

        if closest_v:
            if closest_dist <= self.FOLLOW_MIN_DIST:
                return 0.0  # opreste complet
            elif closest_dist <= self.FOLLOW_BRAKE_DIST:
                # factor bazat pe distanta
                t = (closest_dist - self.FOLLOW_MIN_DIST) / (self.FOLLOW_BRAKE_DIST - self.FOLLOW_MIN_DIST)
                d_factor = MIN_SPEED_FACTOR + (1.0 - MIN_SPEED_FACTOR) * t
                
                # factor bazat pe viteza masinii din fata ("eyes on")
                v_front = math.hypot(closest_v.vx, closest_v.vy)
                v_ego_base = math.hypot(self._base_vx, self._base_vy)
                
                # v_factor: incearca sa se potriveasca cu viteza celui din fata
                # dar nu mai jos de MIN_SPEED_FACTOR daca distanta permite
                v_factor = (v_front / v_ego_base) if v_ego_base > 0 else 1.0
                
                # Alege factorul care asigura siguranta:
                # - d_factor ne opreste pe masura ce ne apropiem de MIN_DIST
                # - v_factor ne ajuta sa nu "pompa m" frana daca cel din fata e constant mai lent
                factor = min(factor, d_factor)
                if v_front > 0.1: # Doar daca cel din fata se misca, incercam speed matching
                    factor = min(factor, max(MIN_SPEED_FACTOR, v_factor))

        # Senzor intersectie: daca cineva e deja in mijloc, incetineste inainte sa intre
        # NUMAI pentru vehicule cu V2X — cele fara V2X nu au senzori
        if all_vehicles and not self._is_inside_intersection() and self.v2x_enabled:
            for other in all_vehicles:
                if other.id == self.id: continue
                if other.state != 'done' and other._is_inside_intersection():
                    d_wait = self._dist_to_wait_line()
                    # Dacă e aproape de intrare și cineva e deja în careu, frânează sau oprește
                    if 0 < d_wait < 150:
                        t = d_wait / 150
                        # Opreste la linie daca distanta e mica
                        f_inter = MIN_SPEED_FACTOR + (1.0 - MIN_SPEED_FACTOR) * t
                        factor = min(factor, f_inter)
                        break # Opreste cautarea, e deja ocupata intersecția

        # Stop la linia de semafoare (numai daca nu are clearance si nu e no_stop)
        # Semaforul conteaza DOAR cand masina e inainte de linia de stop
        # Odata ce a trecut de linie sau e in intersectie, nu mai tine cont de semafor
        if not self.clearance and not self.no_stop:
            dist_stop = self._dist_to_wait_line()
            if dist_stop > 0:
                # Inca nu a ajuns la linia de stop — franezi/opreste
                if dist_stop <= BRAKE_ZONE_DIST:
                    t = dist_stop / BRAKE_ZONE_DIST
                    factor = min(factor, MIN_SPEED_FACTOR + (1.0 - MIN_SPEED_FACTOR) * t)
                if dist_stop <= 1.0:
                    return 0.0  # exact la linia de stop — opreste
            # dist_stop <= 0 inseamna ca a trecut deja de linie — NU mai opri

        return factor

    def update(self, vehicles_same_dir: list = None, **kwargs):
        """
        Misca vehiculul un tick.
        vehicles_same_dir: lista cu celelalte vehicule pe aceeasi directie (pentru following).
        """
        if self.state in ('done', 'crashed'):
            return

        # Daca nu a venit inca timpul de spawn, nu se misca
        if getattr(self, 'spawn_tick', 0) > 0 and kwargs.get('current_tick', 0) < self.spawn_tick:
            self.vx = 0.0
            self.vy = 0.0
            return

        # Vehicul fara V2X: se auto-acorda/revoca clearance (vede semaforul)
        # Verifica semaforul DOAR cand e aproape de linia de stop (nu dupa ce a trecut)
        if not self.v2x_enabled:
            dist_to_stop = self._dist_to_wait_line()
            # Doar daca e inainte de linia de stop (dist > 0) verifica semaforul
            if dist_to_stop > 0:
                from services import v2x_bus as _bus
                infra = _bus.get_all().get('INFRA', {})
                lights = infra.get('lights', {})
                my_light = lights.get(self.direction, 'green')
                if my_light == 'green':
                    self.clearance = True
                elif my_light in ('red', 'yellow'):
                    self.clearance = False
            else:
                # A trecut deja de linia de stop — nu mai verifica semaforul, merge
                self.clearance = True

        # Primeste clearance → incepe traversarea
        if self.state == 'waiting' and self.clearance:
            self.state = 'crossing'

        # Asteapta fara clearance → sta pe loc (doar daca nu e no_stop)
        if self.state == 'waiting' and not self.no_stop:
            self.vx = 0.0
            self.vy = 0.0
            return

        # Calculam viteza dorita (following logic + cross-traffic check)
        # Factor se aplica pentru moving, braking SI crossing
        factor = self._desired_speed_factor(vehicles_same_dir or [], all_vehicles=kwargs.get('active_vehicles'))

        # Daca traversam si trebuie sa viram
        if self.state == 'crossing' and not self._turned and self.intent != 'straight' and self._has_reached_turn_point():
            self._apply_turn()

        if factor <= 0.0:
            # Trebuie sa se opreasca
            self.vx = 0.0
            self.vy = 0.0
            if self.state != 'crossing' and not self.no_stop:
                # Daca e fix la linia de stop si n-are clearance → waiting
                if not self.clearance and self._dist_to_wait_line() <= 1.0:
                    self.state = 'waiting'
                else:
                    self.state = 'braking'
            elif self.no_stop:
                # Vehicul no_stop nu intra niciodata in waiting — ramane moving/crossing
                if self.state not in ('crossing',):
                    self.state = 'moving'
        else:
            self.vx = self._base_vx * factor
            self.vy = self._base_vy * factor
            if self.state != 'crossing':
                self.state = 'moving'

        # Update pozitie
        self.x += self.vx
        self.y += self.vy

        # Trece la crossing odata ce a depasit intersectia
        if self.is_past_intersection():
            self.state = 'crossing'
        if self.is_off_screen():
            self.state = 'done'

    def reset(self):
        self.x, self.y, self.vx, self.vy = self._init
        self._base_vx = self.vx
        self._base_vy = self.vy
        self.state     = 'moving'
        self.clearance = False
        self.agent_yield = False
        self.wait_line = self._calc_wait_line()
        self._exit_dir = EXIT_DIRECTION.get((self.direction, self.intent), self.direction)
        self._turned   = False
        # v2x_enabled, no_stop raman nemodificate la reset

    def to_dict(self) -> dict:
        import math as _math
        speed_px_s = _math.sqrt(self.vx**2 + self.vy**2) * 30  # px/s
        speed_kmh  = round(speed_px_s / 90 * KMH_BASE)         # km/h
        return {
            'id':         self.id,
            'direction':  self.direction,
            'intent':     self.intent,
            'priority':   self.priority,
            'v2x_enabled': self.v2x_enabled,
            'no_stop':    self.no_stop,
            'state':      self.state,
            'clearance':  self.clearance,
            'x':          round(self.x, 1),
            'y':          round(self.y, 1),
            'vx':         round(self.vx, 2),
            'vy':         round(self.vy, 2),
            'speed_kmh':  speed_kmh,
            'heading':    round(self.heading_angle(), 4),
            'dist_to_intersection': round(self.dist_to_intersection(), 1),
            'timestamp':  time.time(),
        }

    def __repr__(self):
        return (f"Vehicle({self.id} dir={self.direction} intent={self.intent} "
                f"state={self.state} pos=({self.x:.0f},{self.y:.0f}))")
