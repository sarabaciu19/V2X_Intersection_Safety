"""
models/agent.py — Agent autonom V2X cu decizie LLM (Ollama)
Fiecare agent:
  - percepe mediul prin V2X Bus (mesaje de la celelalte vehicule)
  - are memorie proprie (ultimele MEMORY_SIZE decizii)
  - trimite context complet catre LLM (Ollama) pentru decizie
  - fallback determinist cand Ollama nu e disponibil
"""
import math
from collections import deque
from services import v2x_bus
from services.collision import time_to_intersection, TTC_BRAKE, TTC_YIELD, is_right_of
from services.llm_client import request_llm_decision
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

        # Vehicul FARA V2X
        if not v.v2x_enabled:
            # AEB Fallback: radar local a detectat obstacol → înregistrăm în memorie
            if getattr(v, 'aeb_active', False):
                self._record_if_new("AEB_ACTIVAT", 0.0,
                    "🛑 radar local <60px — frânare urgență (TARDIVĂ vs. V2X preventiv)")
                self.last_action = "go"
                return "go"
            if v.state == "waiting":
                self._record_if_new("WAIT", 999, "⛔ fără V2X — așteaptă semafor (fără negociere V2V)")
            elif v.state == "crossing":
                self._record_if_new("GO", 999, "⛔ fără V2X — traversează fără comunicare V2V")
            else:
                self._record_if_new("GO", 999, "⛔ fără V2X — conduce normal, fără negociere")
            self.last_action = "go"
            return "go"

        # Fara cooperare → merge fara restrictii
        if not self.cooperation:
            self.last_action = "go"
            return "go"

        my_data = v.to_dict()
        my_ttc  = time_to_intersection(my_data)

        if v.state == "crashed":
            self._record_if_new("CRASH", 0, "💥 vehicul avariat — oprit")
            return "go"

        if v.state == "done":
            self._record_if_new("GO", my_ttc, "vehicul iesit din intersectie")
            return "go"

        if v.state == "crossing":
            self._record_if_new("GO", my_ttc, "traverseaza — clearance primit")
            return "go"

        # Vehicul no_stop: inregistreaza GO dar lasa central_system sa logheze CLEARANCE_SPEED
        if getattr(v, 'no_stop', False):
            self._record_if_new("GO", my_ttc,
                                f"⚡ viteza mare ({v.speed_multiplier*50:.0f} km/h) — nu se opreste la intersectie")
            self.last_action = "go"
            return "go"

        if v.state == "waiting":
            if v.clearance:
                self._record_if_new("GO", my_ttc, "clearance primit — porneste")
            else:
                self._record_if_new("WAIT", my_ttc, "asteapta clearance de la sistemul central")
            self.last_action = "go" if v.clearance else "yield"
            return self.last_action

        # ── Negociere V2V ──
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
            if val.get("direction") == v.direction:
                continue
            if not _are_conflicting(v.direction, v.intent,
                                    val.get("direction", ""),
                                    val.get("intent", "straight")):
                continue
            relevant[k] = val

        if not relevant:
            self.last_action = "go"
            self._record_if_new("GO", my_ttc, "aproape de intersectie — niciun conflict V2V")
            return "go"

        # ── Decizie LLM (Ollama) — motorul principal de decizie ──────────
        # Agentul construieste contextul din perceptia V2X si memoria proprie,
        # si il trimite catre LLM. Daca Ollama nu e disponibil, llm_client
        # aplica automat fallback-ul determinist.
        others_list = [
            {
                "id":        oid,
                "ttc":       round(time_to_intersection(odata), 2),
                "priority":  odata.get("priority", "normal"),
                "direction": odata.get("direction", "?"),
                "intent":    odata.get("intent", "straight"),
                "speed_kmh": odata.get("speed_kmh", 0),
                "no_stop":   odata.get("no_stop", False),
            }
            for oid, odata in relevant.items()
        ]

        context = {
            "my_state": {
                "ttc":                  round(my_ttc, 2),
                "priority":             v.priority,
                "direction":            v.direction,
                "intent":               v.intent,
                "speed_kmh":            my_data.get("speed_kmh", 0),
                "dist_to_intersection": round(my_dist, 1),
                "no_stop":              getattr(v, "no_stop", False),
            },
            "others": others_list,
            "memory": list(self.memory)[-3:],  # ultimele 3 decizii ale agentului
        }

        llm_result = request_llm_decision(v.id, context)
        action_raw = llm_result.get("action", "GO").upper()
        reason     = llm_result.get("reason", "decizie agent")

        # Mapeaza actiunea LLM la actiunea interna
        action = "yield" if action_raw in ("YIELD", "BRAKE") else "go"
        self._record_if_new(action_raw, my_ttc, reason)
        self.last_action = action
        return action

    def _evaluate(self, my_data: dict, my_ttc: float, others: dict) -> str:
        v = self.vehicle
        for other_id, other_data in others.items():
            other_ttc = time_to_intersection(other_data)
            if other_ttc >= TTC_BRAKE * 2:
                continue
            # Urgenta are prioritate absoluta
            if other_data.get("priority") == "emergency" and v.priority != "emergency":
                self._record_if_new("YIELD", my_ttc,
                                    f"vehicul de urgenta {other_id} — prioritate absoluta",
                                    target_id=other_id)
                return "yield"
            if v.priority == "emergency":
                return "go"
            # Celalalt e no_stop (viteza mare, nu se opreste) → cedeaza intotdeauna
            other_no_stop = other_data.get("no_stop", False)
            if other_no_stop and other_ttc < my_ttc:
                other_kmh = other_data.get("speed_multiplier", 1.0) * 50
                my_kmh    = v.speed_multiplier * 50
                self._record_if_new(
                    "YIELD_SPEED_OVERRIDE", my_ttc,
                    (f"⚠ {other_id} vine cu {other_kmh:.0f} km/h si NU se opreste. "
                     f"EU ({v.id}) am prioritate legala (regula dreptei) "
                     f"DAR V2X forteaza cedarea: risc coliziune fara V2X."),
                    target_id=other_id,
                )
                return "yield"
            # Regula dreptei standard
            if is_right_of(my_data, other_data):
                self._record_if_new("YIELD", my_ttc,
                                    f"{other_id} vine din dreapta — regula dreptei",
                                    target_id=other_id)
                return "yield"
            # Celalalt ajunge mult mai repede
            if other_ttc < my_ttc - 0.5:
                other_kmh = other_data.get("speed_multiplier", 1.0) * 50
                self._record_if_new(
                    "YIELD", my_ttc,
                    f"{other_id} TTC={other_ttc:.1f}s ({other_kmh:.0f} km/h) — ajunge primul",
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
