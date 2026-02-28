"""
models/agent.py — Logica de decizie a agentului V2V + V2I (semafor)
La fiecare tick:
  1. Citeste recomandarea de viteza V2I din bus (stop / reduce_speed / proceed)
  2. Daca V2I zice stop → yield imediat
  3. Daca V2I zice reduce_speed → aplica viteza recomandata
  4. Verifica semaforul clasic (fallback)
  5. Negociere V2V (TTC + regula dreptei)
  6. Aplica si logheza decizia
cooperation=False → ignora V2X Bus si semaforul (demo coliziune)
"""
import math
from collections import deque
from services import v2x_bus
from services.collision import time_to_intersection, TTC_BRAKE, TTC_YIELD, is_right_of
from utils import logger

BRAKE_FACTOR = 0.85
MEMORY_SIZE  = 10


def _get_my_light(direction: str) -> str:
    infra = v2x_bus.get_all().get("INFRA", {})
    return infra.get("lights", {}).get(direction, "green")


def _get_v2i_recommendation(vehicle_id: str) -> dict | None:
    infra = v2x_bus.get_all().get("INFRA", {})
    return infra.get("speed_recommendations", {}).get(vehicle_id)


class Agent:
    def __init__(self, vehicle, cooperation: bool = True):
        self.vehicle      = vehicle
        self.cooperation  = cooperation
        self.last_action: str = "go"
        self.memory: deque    = deque(maxlen=MEMORY_SIZE)
        self.last_full_reason = "N/A"

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

    def decide(self) -> str:
        v = self.vehicle

        if not self.cooperation:
            v.state = "moving"
            self.last_action = "go"
            return "go"

        my_data = v.to_dict()
        my_ttc  = time_to_intersection(my_data)

        # ── 1. Recomandare V2I ──────────────────────────────────────────
        rec = _get_v2i_recommendation(v.id)
        if rec is not None and rec["type"] != "proceed":
            rec_type  = rec["type"]
            adv_speed = rec.get("advisory_speed")
            reason    = rec.get("reason", "recomandare V2I")

<<<<<<< Updated upstream
        # 4. Decizie Generativa (V2I + V2V)
        # Pentru performanta: Chemam AI-ul doar daca suntem la o distanta relevanta
        if dist > 350 and my_ttc > 10:
            self._record_decision("GO", round(my_ttc, 2), f"abordez intersectia (dist={dist}px)")
            return "go"

        # Citeste starea semaforului si a celorlalti vehicule de pe bus
        light = _get_my_light(v.direction)
=======
<<<<<<< HEAD
            if rec_type == "stop":
                self._apply("yield", my_ttc, reason=f"V2I: {reason}")
                return "yield"

            if rec_type == "reduce_speed" and adv_speed is not None:
                current = math.sqrt(v.vx ** 2 + v.vy ** 2)
                if current > adv_speed and current > 0:
                    scale = adv_speed / current
                    v.vx *= scale
                    v.vy *= scale
                    v.state = "braking"
                    if self.last_action != "brake":
                        logger.log_decision(v.id, "REDUCE_SPEED", my_ttc,
                                            f"V2I: {reason} → {adv_speed:.1f} px/tick")
                    self.last_action = "brake"
                    self._record("BRAKE", my_ttc, f"V2I reduce_speed → {adv_speed:.1f}")
                    return "brake"

        # ── 2. Semafor clasic (fallback) ────────────────────────────────
        if my_ttc < TTC_BRAKE:
            light = _get_my_light(v.direction)
            if light == "red":
                self._apply("yield", my_ttc, reason="SEMAFOR ROSU")
                return "yield"
            if light == "yellow":
                action = "yield" if my_ttc < TTC_YIELD else "brake"
                self._apply(action, my_ttc, reason="SEMAFOR GALBEN")
                return action

        # ── 3. Departe de intersectie → revin la viteza normala ─────────
        if my_ttc >= TTC_BRAKE:
            if v.state == "braking":
                v.vx    = v._base_vx
                v.vy    = v._base_vy
                v.state = "moving"
                self.last_action = "go"
            self._record("GO", my_ttc, "liber")
            return "go"

        # ── 4. Negociere V2V ────────────────────────────────────────────
=======
        # 4. Decizie Generativa (V2I + V2V)
        # Pentru performanta: Chemam AI-ul doar daca suntem la o distanta relevanta
        if dist > 350 and my_ttc > 10:
            self._record_decision("GO", round(my_ttc, 2), f"abordez intersectia (dist={dist}px)")
            return "go"

        # Citeste starea semaforului si a celorlalti vehicule de pe bus
        light = _get_my_light(v.direction)
>>>>>>> 07d2302322b2f0cd6fe91251e994771a3d18f8d2
>>>>>>> Stashed changes
        others = {
            k: val for k, val in v2x_bus.get_others(v.id).items()
            if val.get("priority") != "infrastructure"
        }
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
        if not others:
            self._record("GO", my_ttc, "niciun alt vehicul")
            return "go"

        action = self._evaluate(my_data, my_ttc, others)
        self._apply(action, my_ttc)
        return action

    def _evaluate(self, my_data: dict, my_ttc: float, others: dict) -> str:
=======
>>>>>>> Stashed changes

        # LLM decide tot contextul: distanță, semafor, vecini
        action, target_id = self._evaluate(my_data, my_ttc, light, others)
        self._apply(action, my_ttc, target_id=target_id)
        return action

    def _evaluate(self, my_data: dict, my_ttc: float, light: str, others: dict) -> tuple:
        """Evalueaza actiunea consultand LLM-ul (Ollama)."""
        # Daca avem deja o cerere in curs, nu facem alta
        if hasattr(self, '_future') and not self._future.done():
            return (self.last_action, None)

        # Throttling/Cooldown constant
        if self.ai_cooldown > 0:
            self.ai_cooldown -= 1
            return (self.last_action, None)

        self.ai_cooldown = 15

        # Pregatim contextul complet pentru LLM
        context = {
            "my_state": {
                "id": self.vehicle.id,
                "ttc": round(my_ttc, 2),
                "dist": round(my_data.get("dist_to_intersection", 0), 1),
                "priority": my_data.get("priority", "normal"),
                "direction": my_data.get("direction", "N"),
                "intent": my_data.get("intent", "straight"),
                "light": light
            },
            "others": []
        }

        for oid, odata in others.items():
            ottc = time_to_intersection(odata)
            if ottc < TTC_BRAKE:
                context["others"].append({
                    "id": oid,
                    "ttc": round(ottc, 2),
                    "dist": round(odata.get("dist_to_intersection", 0), 1),
                    "priority": odata.get("priority", "normal")
                })

        # Apelam LLM in fundal (non-blocking)
        self._future = executor.submit(get_llm_decision, self.vehicle.id, context)

        # Target ID pentru vizualizare
        target_id = None
        if self.last_action != "go" and context["others"]:
            target_id = context["others"][0]["id"]

        return (self.last_action, target_id)

    def _apply(self, action: str, ttc: float, reason: str = None, target_id: str = None) -> None:
>>>>>>> 07d2302322b2f0cd6fe91251e994771a3d18f8d2
        v = self.vehicle
        for other_id, other_data in others.items():
            other_ttc = time_to_intersection(other_data)
            if other_ttc >= TTC_BRAKE:
                continue
            if other_data.get("priority") == "emergency" and v.priority != "emergency":
                return "yield" if my_ttc < TTC_YIELD else "brake"
            if v.priority == "emergency":
                return "go"
            if is_right_of(my_data, other_data):
                return "yield" if my_ttc < TTC_YIELD else "brake"
            if is_right_of(other_data, my_data):
                return "go"
            if my_ttc >= other_ttc:
                return "yield" if my_ttc < TTC_YIELD else "brake"
        return "go"

    def _apply(self, action: str, ttc: float, reason: str = None) -> None:
        v    = self.vehicle
        prev = self.last_action

        if action == "brake":
            v.vx   *= BRAKE_FACTOR
            v.vy   *= BRAKE_FACTOR
            v.state = "braking"
        elif action == "yield":
            v.vx    = 0.0
            v.vy    = 0.0
            v.state = "waiting"
        else:
            if v.state == "braking":
                v.vx = v._base_vx
                v.vy = v._base_vy
            v.state = "moving"

        self.last_action = action
        final_reason = reason or f"TTC={ttc:.2f}s"
        self._record(action.upper(), ttc, final_reason)

        if action != prev and action != "go":
            logger.log_decision(v.id, action.upper(), ttc, final_reason)
