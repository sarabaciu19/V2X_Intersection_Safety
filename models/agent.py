"""
models/agent.py — Logica de decizie a agentului V2V + V2I (semafor)
La fiecare tick:
  1. Citeste starea semaforului din V2X Bus
  2. Daca semafor rosu/galben → yield imediat (cooperare cu infrastructura)
  3. Altfel: calculeaza TTC, consulta ceilalti agenti, decide: 'go' | 'brake' | 'yield'
  4. Aplica pe vehiculul propriu
  5. Logheza decizia
cooperation=False → ignora V2X Bus si semaforul (demo coliziune)
"""
import time
from services import v2x_bus
from services.collision import time_to_intersection, TTC_BRAKE, TTC_YIELD, is_right_of
from utils import logger

BRAKE_FACTOR = 0.85   # reduce viteza cu 15% per tick cand frana


def _get_my_light(direction: str) -> str:
    """Citeste culoarea semaforului pentru directia mea din V2X Bus."""
    infra = v2x_bus.get_all().get("INFRA", {})
    lights = infra.get("lights", {})
    return lights.get(direction, "green")  # default verde daca nu exista


class Agent:
    """Agent V2X asociat unui singur vehicul."""
    def __init__(self, vehicle, cooperation: bool = True):
        self.vehicle = vehicle
        self.cooperation = cooperation
        self.last_action: str = "go"

    def decide(self) -> str:
        """
        Calculeaza si aplica decizia. Returneaza: 'go' | 'brake' | 'yield'
        """
        v = self.vehicle

        # Fara cooperare → vehiculul continua, ignora V2X si semaforul
        if not self.cooperation:
            v.state = "normal"
            self.last_action = "go"
            return "go"

        my_data = v.to_dict()
        my_ttc = time_to_intersection(my_data)

        # ── Verifica semaforul V2I ──────────────────────────────────────
        # Semaforul se respecta cand vehiculul e aproape de intersectie
        if my_ttc < TTC_BRAKE:
            light = _get_my_light(v.direction)
            if light == "red":
                self._apply("yield", my_ttc, reason="SEMAFOR ROSU")
                return "yield"
            if light == "yellow":
                action = "yield" if my_ttc < TTC_YIELD else "brake"
                self._apply(action, my_ttc, reason="SEMAFOR GALBEN")
                return action

        # Departe de intersectie → revin la normal daca eram in frana
        if my_ttc >= TTC_BRAKE:
            if v.state != "normal":
                v.state = "normal"
                self.last_action = "go"
            return "go"

        # ── Negociere V2V ───────────────────────────────────────────────
        others = v2x_bus.get_others(v.id)
        others = {k: val for k, val in others.items() if val.get("priority") != "infrastructure"}

        if not others:
            return "go"

        action = self._evaluate(my_data, my_ttc, others)
        self._apply(action, my_ttc)
        return action

    def _evaluate(self, my_data: dict, my_ttc: float, others: dict) -> str:
        v = self.vehicle
        for other_id, other_data in others.items():
            other_ttc = time_to_intersection(other_data)
            if other_ttc >= TTC_BRAKE:
                continue

            # Urgenta → cedez intotdeauna
            if other_data.get("priority") == "emergency" and v.priority != "emergency":
                return "yield" if my_ttc < TTC_YIELD else "brake"

            # Eu sunt urgenta → trec
            if v.priority == "emergency":
                return "go"

            # Regula dreapta
            if is_right_of(my_data, other_data):
                return "yield" if my_ttc < TTC_YIELD else "brake"

            if is_right_of(other_data, my_data):
                return "go"

            # Frontal: cel cu TTC mai mare frana primul
            if my_ttc >= other_ttc:
                return "yield" if my_ttc < TTC_YIELD else "brake"

        return "go"

    def _apply(self, action: str, ttc: float, reason: str = None) -> None:
        v = self.vehicle
        prev = self.last_action
        if action == "brake":
            v.vx *= BRAKE_FACTOR
            v.vy *= BRAKE_FACTOR
            v.state = "braking"
        elif action == "yield":
            v.vx = 0.0
            v.vy = 0.0
            v.state = "yielding"
        else:
            v.state = "normal"
        self.last_action = action

        # Log doar la schimbare de actiune
        if action != prev and action != "go":
            default_reason = f"TTC={ttc:.2f}s < {'1.5' if action == 'yield' else '3.0'}s"
            logger.log_decision(
                agent_id=v.id,
                action=action.upper(),
                ttc=ttc,
                reason=reason or default_reason,
            )
