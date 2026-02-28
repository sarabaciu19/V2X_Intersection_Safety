"""
models/agent.py — Agent autonom V2X per vehicul
Arhitectura:
  - Fiecare vehicul are propriul agent care decide AUTONOM
  - Agentul citeste EXCLUSIV din V2X Bus (nu acceseaza obiectele Python direct)
  - Agentul pastreaza o memorie interna (buffer ultimele 10 decizii)
La fiecare tick:
  1. Publica propria stare pe V2X Bus
  2. Citeste starea semaforului din V2X Bus (V2I)
  3. Daca semafor rosu/galben → yield imediat
  4. Altfel: calculeaza TTC, consulta ceilalti agenti prin V2X Bus, decide: 'go' | 'brake' | 'yield'
  5. Aplica decizia si o adauga in memoria proprie
  6. Logheza decizia
cooperation=False → ignora V2X Bus si semaforul (demo coliziune)
"""
import time
from collections import deque
from services import v2x_bus
from services.collision import time_to_intersection, TTC_BRAKE, TTC_YIELD, is_right_of
from utils import logger

BRAKE_FACTOR = 0.85   # reduce viteza cu 15% per tick cand frana
MEMORY_SIZE  = 10     # numarul de decizii retinute in memoria agentului


def _get_my_light(direction: str) -> str:
    """Citeste culoarea semaforului pentru directia mea EXCLUSIV din V2X Bus."""
    infra = v2x_bus.get_all().get("INFRA", {})
    lights = infra.get("lights", {})
    return lights.get(direction, "green")  # default verde daca nu exista


class Agent:
    """
    Agent V2X autonom asociat unui singur vehicul.
    Decide independent pe baza mesajelor de pe V2X Bus.
    Pastreaza memorie interna cu ultimele MEMORY_SIZE decizii.
    """
    def __init__(self, vehicle, cooperation: bool = True):
        self.vehicle     = vehicle
        self.cooperation = cooperation
        self.last_action: str = "go"
        # Memoria agentului: buffer circular cu ultimele MEMORY_SIZE decizii
        self.memory: deque = deque(maxlen=MEMORY_SIZE)

    @property
    def vehicle_id(self) -> str:
        return self.vehicle.id

    def _publish_self(self) -> None:
        """Publica starea proprie pe V2X Bus pentru ca alti agenti sa o vada."""
        v2x_bus.publish(self.vehicle.id, self.vehicle.to_dict())

    def _read_self(self) -> dict:
        """
        Citeste propria stare EXCLUSIV din V2X Bus.
        Agentul nu acceseaza direct atributele vehiculului pentru logica de decizie.
        """
        data = v2x_bus.get(self.vehicle.id)
        if data is None:
            # Prima publicare — foloseste to_dict() o singura data pentru init
            self._publish_self()
            data = v2x_bus.get(self.vehicle.id) or {}
        return data

    def _record_decision(self, action: str, ttc: float, reason: str, target_id: str = None) -> None:
        """Adauga decizia curenta in memoria agentului."""
        entry = {
            "tick_time": time.strftime("%H:%M:%S"),
            "action":    action,
            "ttc":       round(ttc, 3),
            "reason":    reason,
            "target_id": target_id,
            "timestamp": time.time(),
        }
        self.memory.append(entry)

    def get_memory(self) -> list:
        """Returneaza o copie a memoriei agentului (ultima MEMORY_SIZE decizii)."""
        return list(self.memory)

    def decide(self) -> str:
        """
        Agentul decide autonom citind EXCLUSIV V2X Bus.
        Returneaza: 'go' | 'brake' | 'yield'
        """
        v = self.vehicle

        # Publica propria stare pe bus inainte de a decide
        self._publish_self()

        # Fara cooperare → vehiculul continua, ignora V2X si semaforul
        if not self.cooperation:
            v.state = "normal"
            self.last_action = "go"
            return "go"

        # Citeste propria stare din V2X Bus (nu din atribute Python direct)
        my_data = self._read_self()
        if not my_data:
            return "go"

        # Calculeaza TTC din datele de pe bus
        my_ttc = time_to_intersection(my_data)

        # ── Verifica semaforul V2I (citit din V2X Bus) ──────────────────
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
            if v.state not in ("normal", "moving", "crossing", "waiting", "done"):
                v.state = "normal"
                self.last_action = "go"
            return "go"

        # ── Negociere V2V (citit din V2X Bus) ───────────────────────────
        # Agentul citeste EXCLUSIV mesajele celorlalti de pe bus
        others = v2x_bus.get_others(v.id)
        others = {k: val for k, val in others.items() if val.get("priority") != "infrastructure"}

        if not others:
            return "go"

        action, target_id = self._evaluate(my_data, my_ttc, others)
        self._apply(action, my_ttc, target_id=target_id)
        return action

    def _evaluate(self, my_data: dict, my_ttc: float, others: dict) -> tuple:
        """Evalueaza actiunea pe baza datelor citite din V2X Bus."""
        my_priority = my_data.get("priority", "normal")
        for other_id, other_data in others.items():
            other_ttc = time_to_intersection(other_data)
            if other_ttc >= TTC_BRAKE:
                continue

            # Urgenta → cedez intotdeauna
            if other_data.get("priority") == "emergency" and my_priority != "emergency":
                return ("yield" if my_ttc < TTC_YIELD else "brake", other_id)

            # Eu sunt urgenta → trec
            if my_priority == "emergency":
                return ("go", None)

            # Regula dreapta
            if is_right_of(my_data, other_data):
                return ("yield" if my_ttc < TTC_YIELD else "brake", other_id)

            if is_right_of(other_data, my_data):
                return ("go", None)

            # Frontal: cel cu TTC mai mare frana primul
            if my_ttc >= other_ttc:
                return ("yield" if my_ttc < TTC_YIELD else "brake", other_id)

        return ("go", None)

    def _apply(self, action: str, ttc: float, reason: str = None, target_id: str = None) -> None:
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

        default_reason = reason or f"TTC={ttc:.2f}s < {'1.5' if action == 'yield' else '3.0'}s"

        # Salveaza decizia in memoria agentului (mereu, nu doar la schimbare)
        self._record_decision(action.upper(), ttc, default_reason, target_id=target_id)

        # Log doar la schimbare de actiune
        if action != prev and action != "go":
            logger.log_decision(
                agent_id=v.id,
                action=action.upper(),
                ttc=ttc,
                reason=default_reason,
            )
