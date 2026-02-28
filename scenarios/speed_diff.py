"""
Scenariu 3 — Viteze diferite
A vine din Nord cu viteza mare (vy=8)
B vine din Vest cu viteza mica (vx=2)
"""
from scenarios.scenario_base import ScenarioBase, VehicleDef
SCENARIO = ScenarioBase(
    name="speed_diff",
    description="Viteza mare vs mica. TTC-urile sunt foarte diferite.",
    vehicles=[
        VehicleDef(id="A", x=400, y=50,  vx=0, vy=8),
        VehicleDef(id="B", x=50,  y=400, vx=2, vy=0),
    ],
)
