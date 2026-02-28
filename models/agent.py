"""
models/agent.py — Logica de decizie V2V + V2I
"""
from collections import deque
from services import v2x_bus
from services.collision import time_to_intersection, TTC_BRAKE, is_right_of
from utils import logger

MEMORY_SIZE   = 10
APPROACH_DIST = 200.0  # px — distanta maxima relevanta


def _get_my_light(direction: str) -> str:
    infra = v2x_bus.get_all().get("INFRA", {})
    return infra.get("lights", {}).get(direction, "green")


def _get_v2i_rec(vehicle_id: str) -> dict | None:
    infra = v2x_bus.get_all().get("INFRA", {})
    return infra.get("speed_recommendations", {}).get(vehicle_id)


class Agent:
    def __init__(self, vehicle, cooperation: bool = True):
        self.vehicle          = vehicle
        self.cooperation      = cooperation
        self.last_action: str = "go"
        self.memory: deque    = deque(maxlen=MEMORY_SIZE)

    @property
    def vehicle_id(self) -> str:
        return self.vehicle.id

    def get_memory(self) -> list:
        return list(self.memory)

    def _record(self, action: str, ttc: float, reason: str) -> None:
        import time as _t
        self.memory.append({
            "tick_time": _t.strftime("%H:%M:%S"),
            "action":    action,
            "ttc":       round(ttc, 3),
            "reason":    reason,
        })

    def _restore(self) -> None:
        v = self.vehicle
        if v.state not in ("waiting", "crossing", "done"):
            v.vx    = v._base_vx
            v.vy    = v._base_vy
            v.state = "moving"

    def _log_once(self, action: str, ttc: float, reason: str) -> None:
        """Logheza in buffer doar daca actiunea s-a schimbat."""
        if self.last_action != action:
            logger.log_decision(self.vehicle.id, action.upper(), ttc, reason)
        self._record(action.upper(), ttc, reason)
        self.last_action = action

    def decide(self) -> str:
        v = self.vehicle

        # Fara cooperare → merge liber
        if not self.cooperation:
            self._restore()
            self.last_action = "go"
            return "go"

        # Urgenta — ignora tot
        if v.priority == "emergency":
            self._restore()
            self.last_action = "go"
            return "go"

        # Traversare / done — nu interveni
        if v.state in ("crossing", "done"):
            self.last_action = "go"
            return "go"

        my_data = v.to_dict()
        my_ttc  = time_to_intersection(my_data)

        # ── 1. V2I ──────────────────────────────────────────────────────
        rec = _get_v2i_rec(v.id)
        if rec is not None:
            rtype = rec["type"]

            if rtype == "stop":
                if v.state == "waiting":
                    return "yield"
                # Seteaza braking — vehicle.update() opreste la wait_line
                if v.state != "braking":
                    v.state = "braking"
                self._log_once("brake", my_ttc, f"V2I: {rec.get('reason','semafor rosu')}")
                return "brake"

            if rtype == "reduce_speed":
                adv = rec.get("advisory_speed", 1.5)
                if v.state not in ("waiting",):
                    current = math.sqrt(v.vx**2 + v.vy**2)
                    if current > adv and current > 0:
                        scale   = adv / current
                        v.vx    = v._base_vx * scale
                        v.vy    = v._base_vy * scale
                        v.state = "braking"
                        self._log_once("brake", my_ttc,
                                       f"V2I: {rec.get('reason','')} → {adv:.1f} px/tick")
                        return "brake"

            if rtype == "proceed":
                if v.state == "braking":
                    self._restore()
                    self.last_action = "go"

        # ── 2. Departe → liber ───────────────────────────────────────────
        if v.dist_to_intersection() >= APPROACH_DIST:
            if v.state == "braking":
                self._restore()
            self.last_action = "go"
            return "go"

        # ── 3. V2V ──────────────────────────────────────────────────────
        others = {
            k: val for k, val in v2x_bus.get_others(v.id).items()
            if val.get("priority") != "infrastructure"
            and val.get("state") not in ("done", None)
            and val.get("dist_to_intersection", 9999) < APPROACH_DIST
            and val.get("direction") != v.direction   # exclude aceeasi banda
        }

        if not others:
            if v.state == "braking":
                self._restore()
            self.last_action = "go"
            return "go"

        action = self._evaluate(my_data, my_ttc, others)

        if action != "go":
            if v.state not in ("waiting", "crossing", "done"):
                v.state = "braking"
            self._log_once(action, my_ttc,
                           f"V2V conflict cu [{','.join(others.keys())}]")
        else:
            if v.state == "braking":
                self._restore()
            self.last_action = "go"

        return action

    def _evaluate(self, my_data: dict, my_ttc: float, others: dict) -> str:
        v = self.vehicle
        for other_id, other_data in others.items():
            other_ttc = time_to_intersection(other_data)
            if other_ttc >= TTC_BRAKE * 2:
                continue
            if other_data.get("priority") == "emergency" and v.priority != "emergency":
                return "yield"
            if v.priority == "emergency":
                return "go"
            if is_right_of(my_data, other_data):
                return "yield"
            if other_ttc < my_ttc - 0.5:
                return "yield"
        return "go"

