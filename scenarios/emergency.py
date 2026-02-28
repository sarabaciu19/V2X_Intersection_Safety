"""
Scenariu 2 — Vehicul de Urgenta
URGENTA vine din Sud (x=400, y=750) cu vy=-6
B vine din Vest (x=50, y=400) cu vx=4
"""
from scenarios.scenario_base import ScenarioBase, VehicleDef
SCENARIO = ScenarioBase(
    name="emergency",
    description="Ambulanta cu prioritate. Ceilalti agenti cedeaza automat.",
    vehicles=[
        VehicleDef(id="URGENTA", x=400, y=750, vx=0,  vy=-6, priority="emergency"),
        VehicleDef(id="B",       x=50,  y=400, vx=4,  vy=0),
    ],
)
