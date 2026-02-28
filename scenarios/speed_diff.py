"""
speed_diff.py — Scenariul 3: Viteze Diferite
----------------------------------------------

DE CE EXISTA:
  Demonstreaza ca sistemul functioneaza si in cazuri mai subtile,
  nu doar la coliziuni evidente. Cand un vehicul lent si unul rapid
  se apropie de intersectie, TTC-ul e mai mic decat pare vizual.

CE SE INTAMPLA:
  - Vehicul A vine din Nord cu viteza MARE (vy=8)
  - Vehicul B vine din Vest cu viteza MICA (vx=2)
  - Fara V2X: A ajunge mult mai repede → coliziune cu B care e deja in intersectie
  - Cu V2X: B calculeaza ca A va ajunge curand si opreste preventiv

LOGICA SPECIALA:
  Demonstreaza ca TTC tine cont de viteza relativa, nu doar de distanta.
  Chiar daca B e aparent departe, TTC-ul mic (din cauza lui A rapid) declanseaza franarea.
"""

from .scenario_base import ScenarioBase, Vehicle, TTC_DANGER, TTC_CRITICAL, BRAKE_FORCE


class SpeedDifferenceScenario(ScenarioBase):

    def __init__(self):
        super().__init__(
            name="Viteze Diferite",
            description="A vine rapid (v=8), B vine lent (v=2). TTC mic detectat preventiv."
        )
        self._init_vehicles()

    def _init_vehicles(self):
        """
        A: viteza mare, ajunge la intersectie rapid
        B: viteza mica, ar fi in intersectie cand A ajunge → coliziune
        """
        self.vehicles = [
            Vehicle(id="A", x=400, y=50, vx=0, vy=8),  # rapid, din Nord
            Vehicle(id="B", x=50, y=400, vx=2, vy=0),  # lent, din Vest
        ]

    def _agent_logic(self, v2x_bus: dict):
        """
        Ambii agenti calculeaza TTC cu celalalt.
        Cel cu TTC mai mic (in pericol mai mare) ia decizia de franare.

        In acest scenariu: B va detecta ca A vine foarte repede
        si va frana preventiv, chiar daca distanta pare OK.
        """
        vehicle_a = next(v for v in self.vehicles if v.id == "A")
        vehicle_b = next(v for v in self.vehicles if v.id == "B")

        if "A" not in v2x_bus or "B" not in v2x_bus:
            return

        ttc_b_sees_a = self.calc_ttc(vehicle_b, vehicle_a)
        ttc_a_sees_b = self.calc_ttc(vehicle_a, vehicle_b)

        # B reactioneaza la A (B e cel in pericol — A vine rapid)
        if ttc_b_sees_a < TTC_CRITICAL:
            vehicle_b.state = "stopped"
            vehicle_b.vx = 0
            vehicle_b.vy = 0
        elif ttc_b_sees_a < TTC_DANGER:
            vehicle_b.state = "braking"
            vehicle_b.vx *= BRAKE_FORCE
            vehicle_b.vy *= BRAKE_FORCE
        else:
            if vehicle_b.state == "braking":
                vehicle_b.state = "normal"

        # A continua normal (e mai rapid, are dreptul de trecere in acest scenariu)
        # Dar franeaza daca B cumva e deja in intersectie
        if ttc_a_sees_b < TTC_CRITICAL:
            vehicle_a.state = "braking"
            vehicle_a.vx *= BRAKE_FORCE
            vehicle_a.vy *= BRAKE_FORCE
        else:
            vehicle_a.state = "normal"