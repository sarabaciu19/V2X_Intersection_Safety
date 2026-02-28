from scenarios.scenario_base import ScenarioBase, VehicleDef

SCENARIO = ScenarioBase(
    name="emergency",
    description="Vehicul de urgenta vine din Vest si vireaza spre Sud. Vehiculul A vine din Nord si cedeaza automat.",
    vehicles=[
        # URGENTA: vine din Vest (x=50, y=400), merge spre Est (vx=+6)
        # Va vira spre Sud in intersecție (logica in agent)
        VehicleDef(
            id="URGENTA",
            x=50,
            y=400,
            vx=6,
            vy=0,
            priority="emergency"
        ),

        # Vehicul normal A: vine din Nord (x=400, y=50), merge spre Sud (vy=+3)
        VehicleDef(
            id="A",
            x=400,
            y=50,
            vx=0,
            vy=3
        ),
    ],
)
