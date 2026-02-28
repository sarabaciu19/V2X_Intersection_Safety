"""
models/agent.py — Logica de decizie a agentului V2V
La fiecare tick:
  1. Citeste starea celorlalti din V2X Bus
  2. Calculeaza TTC propriu fata de intersectie
  3. Decide: 'go' | 'brake' | 'yield'
  4. Aplica pe vehiculul propriu
  5. Logheza decizia
cooperation=False → ignora V2X Bus (demo coliziune)
"""
import time
from services import v2x_bus
from services.collision import time_to_intersection, TTC_BRAKE, TTC_YIELD, is_right_of
from utils import logger
BRAKE_FACTOR = 0.85   # reduce viteza cu 15% per tick cand frana
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
        # Fara cooperare → vehiculul continua, ignora V2X
        if not self.cooperation:
            v.state = "normal"
            self.last_action = "go"
            return "go"
        my_data = v.to_dict()
        my_ttc = time_to_intersection(my_data)
        # Departe de intersectie → revin la normal daca eram in frana
        if my_ttc >= TTC_BRAKE:
            if v.state != "normal":
                v.state = "normal"
                self.last_action = "go"
            return "go"
        others = v2x_bus.get_others(v.id)
        # Filtreaza INFRA (semafor) din agenti vehicule
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
                continue  # celalalt nu e in zona de risc
            # Urgenta → cedez intotdeauna
            if other_data.get("priority") == "emergency" and v.priority != "emergency":
                return "yield" if my_ttc < TTC_YIELD else "brake"
            # Eu sunt urgenta → trec
            if v.priority == "emergency":
                return "go"
            # Regula dreapta: daca celalalt vine din dreapta mea → cedez
            if is_right_of(my_data, other_data):
                return "yield" if my_ttc < TTC_YIELD else "brake"
            # Eu vin din dreapta lui → trec
            if is_right_of(other_data, my_data):
                return "go"
            # Frontal: cel cu TTC mai mare frana primul
            if my_ttc >= other_ttc:
                return "yield" if my_ttc < TTC_YIELD else "brake"
        return "go"
    def _apply(self, action: str, ttc: float) -> None:
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
            logger.log_decision(
                agent_id=v.id,
                action=action.upper(),
                ttc=ttc,
                reason=f"TTC={ttc:.2f}s < {'1.5' if action == 'yield' else '3.0'}s",
            )
