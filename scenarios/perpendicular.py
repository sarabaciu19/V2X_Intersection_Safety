"""
Scenariu 1 — Coliziune Perpendiculara
A vine din Nord (x=400, y=50) cu vy=4
B vine din Vest (x=50, y=400) cu vx=4
"""
from scenarios.scenario_base import ScenarioBase, VehicleDef
SCENARIO = ScenarioBase(
    name="perpendicular",
    description="Unghi mort — A nu vede B. Fara V2X → coliziune. Cu V2X → B frana.",
    vehicles=[
        VehicleDef(id="A", x=400, y=50,  vx=0, vy=4),
        VehicleDef(id="B", x=50,  y=400, vx=4, vy=0),
    ],
)
