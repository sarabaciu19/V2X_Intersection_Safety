"""
emergency.py — Scenariul 2: Vehicul de Urgenta
------------------------------------------------

DE CE EXISTA:
  Vehiculele de urgenta (ambulanta, pompieri) au prioritate absoluta.
  In realitate, vehiculele conectate V2X pot detecta automat apropierea
  unei ambulante si elibera intersectia INAINTE ca soferul s-o vada.

CE SE INTAMPLA:
  - URGENTA vine din Sud, se misca spre Nord cu viteza mare (vy=-6)
  - Vehicul A vine din Nord cu viteza normala (vy=3)
  - URGENTA publica flag 'emergency': True in V2X Bus
  - A detecteaza flag-ul, opreste complet si asteapta
  - Agentul infrastructura (semaforul) vede urgenta → da verde imediat

LOGICA SPECIALA:
  Prioritatea de urgenta suprascrie orice alta logica (TTC, semafor, etc.).
  Demonstreaza juriului ca sistemul poate gestiona cazuri speciale.
"""

from .scenario_base import ScenarioBase, Vehicle, TTC_DANGER, BRAKE_FORCE


class EmergencyScenario(ScenarioBase):

    def __init__(self):
        super().__init__(
            name="Vehicul de Urgenta",
            description="Ambulanta vine din Sud cu prioritate absoluta. Vehiculul normal cedeaza automat."
        )
        self._init_vehicles()

    def _init_vehicles(self):
        """
        URGENTA: vine din Sud pe banda dreapta (x=420), se misca spre Nord (vy negativ, rapid)
        A: vine din Nord pe banda sa (x=380), se misca spre Sud (vy pozitiv, normal)
        Sunt pe benzi diferite (offset 40px) — se intalnesc la intersectie fara overlap perfect
        """
        self.vehicles = [
            Vehicle(id="A",       x=380, y=50,  vx=0, vy=3,  priority="normal"),
            Vehicle(id="URGENTA", x=420, y=750, vx=0, vy=-6, priority="emergency"),
        ]

    def _agent_logic(self, v2x_bus: dict):
        """
        Logica de urgenta:
          1. URGENTA publica flag-ul sau in V2X Bus
          2. Orice vehicul normal care detecteaza o urgenta in apropiere → STOP
          3. URGENTA nu franeaza niciodata
        """
        vehicle_a      = next(v for v in self.vehicles if v.id == "A")
        vehicle_urg    = next(v for v in self.vehicles if v.id == "URGENTA")

        # URGENTA isi publica starea cu flag explicit
        v2x_bus["URGENTA"] = {
            **vehicle_urg.to_dict(),
            "emergency": True,      # Flag citit de ceilalti agenti
            "siren": True           # Folosit de frontend pentru efectul vizual
        }

        # Vehiculul A citeste V2X Bus si cauta flag de urgenta
        emergency_nearby = any(
            data.get("emergency", False)
            for agent_id, data in v2x_bus.items()
            if agent_id != "A" and agent_id != "INFRA"
        )

        if emergency_nearby:
            # Calculeaza TTC cu vehiculul de urgenta
            ttc = self.calc_ttc(vehicle_a, vehicle_urg)

            if ttc < TTC_DANGER:
                # Opreste complet — lasa urgenta sa treaca
                vehicle_a.state = "stopped"
                vehicle_a.vx = 0
                vehicle_a.vy = 0
        else:
            if vehicle_a.state == "stopped":
                # Urgenta a trecut — reia mersul
                vehicle_a.state = "normal"
                vehicle_a.vy = vehicle_a.original["vy"]

        # Urgenta merge mereu cu viteza maxima
        vehicle_urg.state = "emergency"