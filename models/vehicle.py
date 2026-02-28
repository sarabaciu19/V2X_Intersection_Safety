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
        """Vehiculul a trecut complet de intersectie (a depasit centrul cu ROAD_WIDTH)."""
        margin = ROAD_WIDTH
        if self.direction == 'N':
            return self.y > INTERSECTION_Y + margin
        if self.direction == 'S':
            return self.y < INTERSECTION_Y - margin
        if self.direction == 'E':
            return self.x < INTERSECTION_X - margin
        if self.direction == 'V':
            return self.x > INTERSECTION_X + margin
        return False

    def is_off_screen(self) -> bool:
        """Vehiculul a iesit complet din canvas (800x800)."""
        margin = 40
        return (self.x < -margin or self.x > 800 + margin or
                self.y < -margin or self.y > 800 + margin)

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

        # 3. Miscare normala (moving) — opreste la linia de stop daca n-are clearance
        if self.state == 'moving':
            if self.is_at_wait_line() and not self.clearance:
                self.state = 'waiting'
                self.vx = 0
                self.vy = 0
                return
            self.vx = self._base_vx
            self.vy = self._base_vy
            self.x += self.vx
            self.y += self.vy

        # 4. Traversare (crossing)
        elif self.state == 'crossing':
            self.vx = self._base_vx
            self.vy = self._base_vy
            self.x += self.vx
            self.y += self.vy
            if self.is_past_intersection():
                self.state = 'done'

        # 5. Stare 'done' — vehiculul continua sa se miste pana iese din canvas
        elif self.state == 'done':
            self.x += self._base_vx
            self.y += self._base_vy
    def reset(self):
        self.x, self.y, self.vx, self.vy = self._init
        self._base_vx = self.vx
        self._base_vy = self.vy
        self.state     = 'moving'
        self.clearance = False
        self.wait_line = self._calc_wait_line()
    def to_dict(self) -> dict:
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
            'dist_to_intersection': round(self.dist_to_intersection(), 1),
            'timestamp':  time.time(),
        }
    def __repr__(self):
        return (f"Vehicle({self.id} dir={self.direction} intent={self.intent} "
                f"state={self.state} pos=({self.x:.0f},{self.y:.0f}))")
