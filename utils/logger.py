"""
logger.py — Logging Structurat al Deciziilor Agentilor
-------------------------------------------------------

DE CE EXISTA:
  Juriul vrea sa VADA ca agentii iau decizii, nu doar sa vada animatia.
  Logger-ul capteaza fiecare actiune (BRAKE, STOP, RESUME, EMERGENCY_YIELD)
  cu timestamp, agent, motiv si TTC-ul care a declansat decizia.

UNDE APARE IN DEMO:
  1. In frontend: EventLog component — ultimele 10 decizii in timp real
  2. In consola Python: print colorat pentru debugging
  3. In fisierul decisions.json — il arati juriului dupa demo ca dovada

FORMAT LOG:
  {
    "time": "14:32:05.123",
    "tick": 87,
    "agent": "B",
    "action": "BRAKE",
    "ttc": 1.8,
    "reason": "TTC sub pragul de pericol (3.0s)",
    "cooperation": true
  }
"""

import json
import time
from datetime import datetime
from pathlib import Path

# ── Tipuri de actiuni ─────────────────────────────────────────────────────────
ACTION_BRAKE = "BRAKE"
ACTION_STOP = "STOP"
ACTION_RESUME = "RESUME"
ACTION_EMERGENCY_YIELD = "EMERGENCY_YIELD"
ACTION_COLLISION = "COLLISION"
ACTION_INFRA_OVERRIDE = "INFRA_OVERRIDE"


class DecisionLogger:
    """
    Logheaza deciziile agentilor si le face disponibile pentru:
      - Frontend (via WebSocket — trimis ca parte din state)
      - Fisier JSON (decisions.json)
      - Consola (pentru debugging in timp real)
    """

    def __init__(self, log_file: str = "decisions.json", max_memory: int = 100):
        self.log_file = Path(log_file)
        self.max_memory = max_memory  # Cate decizii tine in memorie
        self.decisions: list[dict] = []  # Log in memorie
        self.last_states: dict = {}  # Ultima stare a fiecarui agent (pentru detectie schimbare)

        # Creeaza fisierul gol la start
        self._write_to_file(clear=True)

    def log_decision(
            self,
            agent_id: str,
            action: str,
            ttc: float = None,
            reason: str = "",
            cooperation: bool = True,
            tick: int = 0
    ):
        """
        Inregistreaza o decizie a unui agent.

        Apelat din scenario_base._agent_logic() cand un agent isi schimba starea.
        """
        entry = {
            "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "tick": tick,
            "agent": agent_id,
            "action": action,
            "ttc": round(ttc, 2) if ttc is not None else None,
            "reason": reason,
            "cooperation": cooperation
        }

        # Adauga in memorie
        self.decisions.append(entry)
        if len(self.decisions) > self.max_memory:
            self.decisions.pop(0)  # Sterge cel mai vechi

        # Afiseaza in consola (cu culori ANSI)
        self._print_colored(entry)

        # Scrie in fisier
        self._write_to_file()

        return entry

    def log_vehicle_state_change(
            self,
            agent_id: str,
            old_state: str,
            new_state: str,
            ttc: float = None,
            tick: int = 0,
            cooperation: bool = True
    ):
        """
        Helper: logheaza automat daca starea unui agent s-a schimbat.
        Apeleaza-l din _agent_logic() pentru a nu duplica logica de detectie.

        Exemplu:
          logger.log_vehicle_state_change("B", "normal", "braking", ttc=1.8, tick=87)
        """
        if old_state == new_state:
            return None  # Nu s-a schimbat nimic — nu logam

        action_map = {
            ("normal", "braking"): (ACTION_BRAKE, f"TTC={ttc}s < {3.0}s"),
            ("normal", "stopped"): (ACTION_STOP, f"TTC={ttc}s < {1.5}s"),
            ("braking", "stopped"): (ACTION_STOP, f"TTC={ttc}s critic"),
            ("braking", "normal"): (ACTION_RESUME, "Pericol trecut"),
            ("stopped", "normal"): (ACTION_RESUME, "Drum liber"),
            ("normal", "emergency"): (ACTION_EMERGENCY_YIELD, "Urgenta detectata"),
        }

        action, reason = action_map.get(
            (old_state, new_state),
            (f"{old_state.upper()}→{new_state.upper()}", "Schimbare stare")
        )

        return self.log_decision(
            agent_id=agent_id,
            action=action,
            ttc=ttc,
            reason=reason,
            cooperation=cooperation,
            tick=tick
        )

    def log_collision(self, agent_ids: list, tick: int):
        """Logheaza o coliziune (cand cooperation=False)."""
        return self.log_decision(
            agent_id=" + ".join(agent_ids),
            action=ACTION_COLLISION,
            reason="Cooperare dezactivata — coliziune inevitabila",
            cooperation=False,
            tick=tick
        )

    def get_recent(self, n: int = 10) -> list:
        """
        Returneaza ultimele N decizii.
        Apelat de WebSocket handler pentru a trimite log-ul la frontend.
        """
        return self.decisions[-n:]

    def get_all(self) -> list:
        """Returneaza toate deciziile (pentru export JSON complet)."""
        return self.decisions

    def clear(self):
        """Reseteaza log-ul (la apasarea butonului Reset din frontend)."""
        self.decisions = []
        self.last_states = {}
        self._write_to_file(clear=True)

    # ── Metode interne ────────────────────────────────────────────────────────

    def _print_colored(self, entry: dict):
        """Afiseaza log-ul in consola cu culori ANSI pentru debugging."""
        colors = {
            ACTION_BRAKE: "\033[93m",  # Galben
            ACTION_STOP: "\033[91m",  # Rosu
            ACTION_RESUME: "\033[92m",  # Verde
            ACTION_EMERGENCY_YIELD: "\033[95m",  # Magenta
            ACTION_COLLISION: "\033[91m\033[1m",  # Rosu bold
            ACTION_INFRA_OVERRIDE: "\033[96m",  # Cyan
        }
        reset = "\033[0m"
        color = colors.get(entry["action"], "\033[97m")

        ttc_str = f" | TTC={entry['ttc']}s" if entry["ttc"] else ""
        coop_str = " [V2X ON]" if entry["cooperation"] else " [V2X OFF]"

        print(
            f"{color}[{entry['time']}] tick={entry['tick']:04d} "
            f"Agent={entry['agent']:8s} {entry['action']:20s}"
            f"{ttc_str} | {entry['reason']}{coop_str}{reset}"
        )

    def _write_to_file(self, clear: bool = False):
        """Scrie log-ul in decisions.json (pentru prezentarea juriului)."""
        try:
            if clear:
                data = {"session_start": datetime.now().isoformat(), "decisions": []}
            else:
                data = {
                    "session_start": datetime.now().isoformat(),
                    "total_decisions": len(self.decisions),
                    "decisions": self.decisions
                }
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Nu oprim simularea daca log-ul da erori
            print(f"[Logger] Eroare scriere fisier: {e}")


# ── Instanta globala (importata de Persoana 1 in simulatorul principal) ────────
# Persoana 1 face: from utils.logger import logger
# Persoana 3 defineste scenariile si apeleaza logger.log_decision() din logica agentilor
logger = DecisionLogger(log_file="decisions.json")