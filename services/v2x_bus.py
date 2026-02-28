"""
services/v2x_bus.py — Canalul V2X partajat
Dict global: { vehicle_id: state_dict }
"""
from typing import Dict
_channel: Dict[str, dict] = {}
def publish(vehicle_id: str, data: dict) -> None:
    """Scrie starea unui vehicul pe bus."""
    _channel[vehicle_id] = data
def get_all() -> Dict[str, dict]:
    return dict(_channel)
def get_others(vehicle_id: str) -> Dict[str, dict]:
    """Returneaza toti ceilalti agenti."""
    return {k: v for k, v in _channel.items() if k != vehicle_id}
def get(vehicle_id: str):
    return _channel.get(vehicle_id)
def clear() -> None:
    """Goleste bus-ul la reset scenariu."""
    _channel.clear()
