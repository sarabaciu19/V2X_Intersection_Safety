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
LANE_WIDTH     = 30   # px per banda
ROAD_WIDTH     = LANE_WIDTH * 2  # 2 benzi per directie = 60px
# Offset banda (fata de centrul drumului)
LANE_IN_OFFSET  =  15   # vehicule care vin spre intersectie (banda dreapta)
LANE_OUT_OFFSET = -15   # vehicule care pleaca (banda stanga)
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
                 priority: str = 'normal', speed_multiplier: float = 1.0):
        """
        direction: 'N' | 'S' | 'E' | 'V'  (de unde vine)
        intent:    'straight' | 'left' | 'right'
        priority:  'normal' | 'emergency'
        """
        self.id        = id
        self.direction = direction
        self.intent    = intent
        self.priority  = priority
        self.state     = 'moving'   # moving | waiting | crossing | done
        sx, sy    = SPAWN[direction]
        vx0, vy0  = VELOCITY[direction]
        self.x    = float(sx)
        self.y    = float(sy)
        self.vx   = vx0 * speed_multiplier
        self.vy   = vy0 * speed_multiplier
        self._base_vx = self.vx
        self._base_vy = self.vy
        self._init    = (self.x, self.y, self.vx, self.vy)
        # Decizie sistem central
        self.clearance = False   # True = sistemul i-a dat voie sa treaca
        self.wait_line = self._calc_wait_line()
    def _calc_wait_line(self) -> float:
        """Distanta de la intersectie unde masina se opreste sa astepte."""
        if self.direction == 'N':
            return INTERSECTION_Y - ROAD_WIDTH / 2 - 10
        if self.direction == 'S':
            return INTERSECTION_Y + ROAD_WIDTH / 2 + 10
        if self.direction == 'E':
            return INTERSECTION_X + ROAD_WIDTH / 2 + 10
        if self.direction == 'V':
            return INTERSECTION_X - ROAD_WIDTH / 2 - 10
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
        """Vehiculul a depasit centrul intersectiei."""
        if self.direction == 'N':   return self.y > INTERSECTION_Y + ROAD_WIDTH // 2 + 5
        if self.direction == 'S':   return self.y < INTERSECTION_Y - ROAD_WIDTH // 2 - 5
        if self.direction == 'E':   return self.x < INTERSECTION_X - ROAD_WIDTH // 2 - 5
        if self.direction == 'V':   return self.x > INTERSECTION_X + ROAD_WIDTH // 2 + 5
        return False

    def is_off_screen(self) -> bool:
        """Vehiculul a iesit complet din canvas (dispare din peisaj)."""
        MARGIN = 50
        if self.direction == 'N':   return self.y > 800 + MARGIN
        if self.direction == 'S':   return self.y < -MARGIN
        if self.direction == 'E':   return self.x < -MARGIN
        if self.direction == 'V':   return self.x > 800 + MARGIN
        return False
    def update(self):
        """Misca vehiculul un tick in functie de stare si clearance."""

        # 1. Daca asteapta SI a primit clearance → incepe traversarea
        if self.state == 'waiting' and self.clearance:
            self.state = 'crossing'
            self.vx = self._base_vx
            self.vy = self._base_vy

        # 2. Daca asteapta fara clearance → sta pe loc
        if self.state == 'waiting':
            self.vx = 0
            self.vy = 0
            return

        # 3. Daca se misca si a ajuns la linia de stop fara clearance → opreste
        if self.state == 'moving' and self.is_at_wait_line() and not self.clearance:
            self.state = 'waiting'
            self.vx = 0
            self.vy = 0
            return

        # 4. Miscare normala (moving sau crossing)
        if self.state in ('moving', 'crossing'):
            self.vx = self._base_vx
            self.vy = self._base_vy
            self.x += self.vx
            self.y += self.vy
            # Trece la crossing dupa ce depaseste centrul intersectiei
            if self.state == 'moving' and self.is_past_intersection():
                self.state = 'crossing'
            # Done abia cand iese complet din canvas
            if self.is_off_screen():
                self.state = 'done'
    def reset(self):
        self.x, self.y, self.vx, self.vy = self._init
        self._base_vx = self.vx
        self._base_vy = self.vy
        self.state     = 'moving'
        self.clearance = False
        self.wait_line = self._calc_wait_line()
    def to_dict(self) -> dict:
        import math as _math
        speed_px_s = _math.sqrt(self.vx**2 + self.vy**2) * 30  # px/s
        speed_kmh  = round(speed_px_s / 90 * KMH_BASE)         # km/h
        return {
            'id':         self.id,
            'direction':  self.direction,
            'intent':     self.intent,
            'priority':   self.priority,
            'state':      self.state,
            'clearance':  self.clearance,
            'x':          round(self.x, 1),
            'y':          round(self.y, 1),
            'vx':         round(self.vx, 2),
            'vy':         round(self.vy, 2),
            'speed_kmh':  speed_kmh,
            'dist_to_intersection': round(self.dist_to_intersection(), 1),
            'timestamp':  time.time(),
        }
    def __repr__(self):
        return (f"Vehicle({self.id} dir={self.direction} intent={self.intent} "
                f"state={self.state} pos=({self.x:.0f},{self.y:.0f}))")
