"""
utils/logger.py — Logging structurat al deciziilor agentilor
Format: {'time': '12:34:05', 'agent': 'B', 'action': 'BRAKE', 'ttc': 1.8}
Salveaza in decisions.json si trimite prin WebSocket la frontend (EventLog).
"""
import json
import time
import logging
from datetime import datetime
from pathlib import Path
# Fisier de output
DECISIONS_FILE = Path(__file__).parent.parent / "decisions.json"
# Logger standard Python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
_log = logging.getLogger("V2X")
# Buffer in-memory (ultimele 100 decizii) — trimis la frontend
_buffer: list[dict] = []
def log_decision(agent_id: str, action: str, ttc: float, reason: str = "") -> dict:
    """
    Inregistreaza o decizie a unui agent.
    Returneaza entry-ul pentru a fi trimis prin WebSocket.
    """
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent_id,
        "action": action,          # 'BRAKE' | 'YIELD' | 'GO'
        "ttc": round(ttc, 2),
        "reason": reason,
        "timestamp": time.time(),
    }
    _buffer.append(entry)
    if len(_buffer) > 100:
        _buffer.pop(0)
    # Log consola
    level = logging.WARNING if action in ("BRAKE", "YIELD") else logging.INFO
    _log.log(level, f"Agent {agent_id} → {action} | TTC={ttc:.2f}s | {reason}")
    # Salveaza pe disc (append)
    _save_to_file(entry)
    return entry
def log_collision(id1: str, id2: str) -> None:
    """Inregistreaza o coliziune fizica."""
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": f"{id1}+{id2}",
        "action": "COLLISION",
        "ttc": 0.0,
        "reason": "No cooperation — physical collision",
        "timestamp": time.time(),
    }
    _buffer.append(entry)
    _log.error(f"COLIZIUNE! {id1} <-> {id2}")
    _save_to_file(entry)
def log_info(msg: str) -> None:
    _log.info(msg)
def get_recent(n: int = 10) -> list[dict]:
    """Returneaza ultimele n decizii — pentru frontend EventLog."""
    return list(_buffer[-n:])
def get_all() -> list[dict]:
    return list(_buffer)
def clear() -> None:
    _buffer.clear()
def _save_to_file(entry: dict) -> None:
    try:
        existing = []
        if DECISIONS_FILE.exists():
            with open(DECISIONS_FILE, "r") as f:
                existing = json.load(f)
        existing.append(entry)
        # Pastreaza ultimele 500 in fisier
        if len(existing) > 500:
            existing = existing[-500:]
        with open(DECISIONS_FILE, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception:
        pass  # Nu blocam simularea daca scrierea esueaza
