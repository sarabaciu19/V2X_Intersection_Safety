"""
scenarios/scenario_base.py — Clasa de baza pentru scenarii
"""
from dataclasses import dataclass, field
from typing import List
@dataclass
class VehicleDef:
    id: str
    x: float
    y: float
    vx: float
    vy: float
    priority: str = "normal"
@dataclass
class ScenarioBase:
    name: str
    description: str
    vehicles: List[VehicleDef] = field(default_factory=list)
    auto_reset_after: float = 5.0
