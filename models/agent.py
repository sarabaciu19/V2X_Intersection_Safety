"""
models/agent.py — Logica de decizie V2V + V2I
Filtrare stricta: deciziile sunt bazate DOAR pe vehicule care:
  1. Se afla la aceeasi intersectie
  2. Se apropie de intersectie (dist < APPROACH_DIST)
  3. Sunt in conflict real (perpendiculare sau viraj stanga)
  Nu se iau in calcul vehiculele din spate sau de pe alte drumuri.
"""
import math
from collections import deque
from services import v2x_bus
from services.collision import time_to_intersection, TTC_BRAKE, TTC_YIELD, is_right_of
from utils import logger

BRAKE_FACTOR  = 0.85
MEMORY_SIZE   = 10
APPROACH_DIST = 150.0   # px — distanta maxima de la intersectie pentru a fi "relevant"

# Axele de conflict: vehicule pe axe perpendiculare se pot ciocni in intersectie
AXIS = {
    'N': 'vertical', 'S': 'vertical',
    'E': 'horizontal', 'V': 'horizontal',
}


def _get_my_light(vehicle) -> str:
    """Citeste culoarea semaforului pentru vehiculul dat, la intersectia sa."""
    ikey      = getattr(vehicle, 'intersection_key', 'NV')
    direction = vehicle.direction
    # Incearca INFRA_{key}
    infra = v2x_bus.get_all().get(f"INFRA_{ikey}", {})
    if infra:
        return infra.get("lights", {}).get(direction, "green")
    # Fallback INFRA global
    infra_g = v2x_bus.get_all().get("INFRA", {})
    all_l   = infra_g.get("all_lights", {})
    if ikey in all_l:
        return all_l[ikey].get(direction, "green")
    return infra_g.get("lights", {}).get(direction, "green")


def _are_conflicting(dir1: str, intent1: str, dir2: str, intent2: str) -> bool:
    """
    True daca doua vehicule cu directiile/intentiile date pot intra in conflict
    in intersectie. Vehiculele pe aceeasi axa (N-S sau E-V) nu se ciocnesc
    daca merg drept (sunt pe benzi separate). Conflicte reale:
      - axe perpendiculare (N vs V, N vs E, S vs V, S vs E)
      - viraj stanga vs oricare alt vehicul perpendicular
    """
    same_axis = AXIS.get(dir1) == AXIS.get(dir2)
    if same_axis:
        # Aceeasi axa: conflict doar daca un vehicul vireaza stanga spre celalalt
        if intent1 == 'left' or intent2 == 'left':
            return True
        return False
    # Axe diferite: conflict intotdeauna (daca amandoi se apropie)
    return True


def _is_ahead_on_same_lane(me: dict, other: dict) -> bool:
    """True daca 'other' e IN FATA lui 'me' pe aceeasi banda (acelasi drum, aceeasi directie)."""
    if me.get('direction') != other.get('direction'):
        return False
    d = me.get('direction', '')
    if d == 'N':   return other['y'] > me['y']   # merge Sud, fata = y mai mare
    if d == 'S':   return other['y'] < me['y']   # merge Nord, fata = y mai mic
    if d == 'E':   return other['x'] < me['x']   # merge Vest, fata = x mai mic
    if d == 'V':   return other['x'] > me['x']   # merge Est,  fata = x mai mare
    return False


class Agent:
    def __init__(self, vehicle, cooperation: bool = True):
        self.vehicle          = vehicle
        self.cooperation      = cooperation
        self.last_action: str = "go"
        self.memory: deque    = deque(maxlen=MEMORY_SIZE)
        self._last_state: str = ""   # ultima stare inregistrata (pentru deduplicare)

    @property
    def vehicle_id(self) -> str:
        return self.vehicle.id

    def get_memory(self) -> list:
        return list(self.memory)

    def _record(self, action: str, ttc: float, reason: str, target_id: str = None) -> None:
        import time as _t
        entry = {
            "tick_time": _t.strftime("%H:%M:%S"),
            "action":    action,
            "ttc":       round(ttc, 3),
            "reason":    reason,
        }
        if target_id:
            entry["target_id"] = target_id
        self.memory.append(entry)

    def _record_if_new(self, action: str, ttc: float, reason: str, target_id: str = None) -> None:
        """Inregistreaza in memorie doar daca starea s-a schimbat fata de ultima inregistrare."""
        key = f"{action}|{reason}"
        if key == self._last_state:
            return
        self._last_state = key
        self._record(action, ttc, reason, target_id)

    def decide(self) -> str:
        v = self.vehicle

        # Vehicul FARA V2X → merge fara restrictii, ignora TOATE semnalele
        if not v.v2x_enabled:
            self._record_if_new("GO", 999, "⛔ vehicul FĂRĂ V2X — nu poate citi semnale, ignoră intersecția")
            self.last_action = "go"
            return "go"

        # Fara cooperare → merge fara restrictii
        if not self.cooperation:
            self.last_action = "go"
            return "go"

        my_data = v.to_dict()
        my_ttc  = time_to_intersection(my_data)

        # ── Inregistreaza starea curenta a vehiculului ──────────────────
        if v.state == "done":
            self._record_if_new("GO", my_ttc, "vehicul iesit din intersectie")
            return "go"

        if v.state == "crossing":
            self._record_if_new("GO", my_ttc, "traverseaza — clearance primit")
            return "go"

        if v.state == "waiting":
            if v.clearance:
                self._record_if_new("GO", my_ttc, "clearance primit — porneste")
            else:
                self._record_if_new("WAIT", my_ttc, "asteapta clearance de la sistemul central")
            self.last_action = "go" if v.clearance else "yield"
            return self.last_action

        # ── Negociere V2V — vehicule in conflict la aceeasi intersectie ──
        my_dist = v.dist_to_intersection()
        if my_dist >= APPROACH_DIST:
            self._record_if_new("GO", my_ttc, "in tranzit — departe de intersectie")
            self.last_action = "go"
            return "go"

        all_bus = v2x_bus.get_all()
        ikey    = getattr(v, 'intersection_key', 'NV')

        relevant = {}
        for k, val in all_bus.items():
            if k == v.id or k.startswith("INFRA"):
                continue
            if val.get("state") in ("done", "crossing", None):
                continue
            if val.get("intersection_key", ikey) != ikey:
                continue
            other_dist = val.get("dist_to_intersection", 9999)
            if other_dist > APPROACH_DIST:
                continue
            # Exclude vehiculele de pe aceeasi banda (in fata sau in spate)
            if val.get("direction") == v.direction:
                continue
            # Conflict real (axe perpendiculare sau viraj stanga)
            if not _are_conflicting(v.direction, v.intent,
                                    val.get("direction", ""),
                                    val.get("intent", "straight")):
                continue
            relevant[k] = val

        if not relevant:
            self.last_action = "go"
            self._record_if_new("GO", my_ttc, "aproape de intersectie — niciun conflict V2V")
            return "go"

        action = self._evaluate(my_data, my_ttc, relevant)
        self.last_action = action
        target_ids = list(relevant.keys())
        reason = f"conflict V2V cu [{','.join(target_ids)}]"
        # _evaluate poate fi deja inregistrat cu detalii specifice (YIELD_SPEED_OVERRIDE)
        # Inregistram generic doar daca nu a fost deja inregistrat
        if action == 'go':
            self._record_if_new(action.upper(), my_ttc, reason,
                                target_id=target_ids[0] if target_ids else None)
        elif action != 'go' and self._last_state.startswith(action.upper()):
            pass  # deja inregistrat de _evaluate cu detalii complete
        else:
            self._record_if_new(action.upper(), my_ttc, reason,
                                target_id=target_ids[0] if target_ids else None)
        if action != "go":
            logger.log_decision(v.id, action.upper(), my_ttc,
                                f"conflict cu {list(relevant.keys())}")
        return action

    def _evaluate(self, my_data: dict, my_ttc: float, others: dict) -> str:
        v = self.vehicle
        for other_id, other_data in others.items():
            other_ttc = time_to_intersection(other_data)
            # Celelalalt nu e aproape → ignora
            if other_ttc >= TTC_BRAKE * 2:
                continue
            # Urgenta are prioritate absoluta
            if other_data.get("priority") == "emergency" and v.priority != "emergency":
                self._record_if_new(
                    "YIELD", my_ttc,
                    f"vehicul de urgenta {other_id} — prioritate absoluta",
                    target_id=other_id,
                )
                return "yield"
            if v.priority == "emergency":
                return "go"
            # Regula dreptei
            if is_right_of(my_data, other_data):
                # Celalalt vine din dreapta mea — normal ar trebui sa cedez
                # Dar verifica daca celalalt vine cu viteza mult mai mare (speed override)
                other_kmh = other_data.get("speed_multiplier", 1.0) * 50
                my_kmh    = my_data.get("speed_multiplier", 1.0) * 50
                speed_override = (other_ttc < my_ttc - 0.3) and (other_kmh > my_kmh * 1.3)
                if speed_override:
                    self._record_if_new(
                        "YIELD_SPEED_OVERRIDE", my_ttc,
                        (
                            f"⚠ {other_id} vine cu {other_kmh:.0f} km/h (TTC={other_ttc:.1f}s) — "
                            f"EU ({v.id}) am prioritate legala (regula dreptei), "
                            f"DAR V2X forteaza cedarea: viteza excesiva = risc coliziune. "
                            f"Fara V2X → accident garantat."
                        ),
                        target_id=other_id,
                    )
                return "yield"
            # Daca celalalt ajunge mult mai repede → cedeaza
            if other_ttc < my_ttc - 0.5:
                other_kmh = other_data.get("speed_multiplier", 1.0) * 50
                my_kmh    = my_data.get("speed_multiplier", 1.0) * 50
                self._record_if_new(
                    "YIELD", my_ttc,
                    f"{other_id} TTC={other_ttc:.1f}s ({other_kmh:.0f} km/h) < meu TTC={my_ttc:.1f}s — cedeaza",
                    target_id=other_id,
                )
                return "yield"
        return "go"

    def _apply(self, action: str, ttc: float, reason: str = None) -> None:
        v    = self.vehicle
        prev = self.last_action

        if action == "brake":
            v.vx   *= BRAKE_FACTOR; v.vy *= BRAKE_FACTOR
            if v.state not in ("waiting", "crossing"):
                v.state = "braking"
        elif action in ("yield", "stop"):
            # Nu suprascrie waiting sau crossing
            if v.state not in ("waiting", "crossing"):
                v.vx = 0.0; v.vy = 0.0
                v.state = "braking"   # braking vizual, oprire fizica
        else:  # go
            if v.state == "braking":
                v.vx = v._base_vx; v.vy = v._base_vy
                v.state = "moving"

        self.last_action = action
        self._record(action.upper(), ttc, reason or f"TTC={ttc:.2f}s")
        if action != prev and action not in ("go",):
            logger.log_decision(v.id, action.upper(), ttc, reason or "")
