"""
perpendicular.py — Scenariul 1: Coliziune Perpendiculara
---------------------------------------------------------

DE CE EXISTA:
  Acesta e scenariul PRINCIPAL — cel pe care il arati primul juriului.
  Simuleaza cel mai frecvent tip de accident: doi soferi care nu se vad
  reciproc la o intersectie cu vizibilitate blocata (unghi mort).

CE SE INTAMPLA:
  - Vehicul A vine din Nord, se deplaseaza spre Sud (vy pozitiv)
  - Vehicul B vine din Vest, se deplaseaza spre Est (vx pozitiv)
  - Fara V2X: ambii ajung la centrul intersectiei in acelasi timp → coliziune
  - Cu V2X: B primeste pozitia lui A, calculeaza TTC = 1.8s < 3s → franeaza
  - Rezultat: A trece, B asteapta, coliziune evitata

LOGICA SPECIALA (fata de ScenarioBase):
  Vehiculul B este cel care cedeaza (e "din dreapta" lui A in logica romaneasca).
  Suprascrie _agent_logic() pentru a implementa regula prioritatii la dreapta.
"""

from .scenario_base import ScenarioBase, Vehicle, TTC_DANGER, TTC_CRITICAL, BRAKE_FORCE


class PerpendicularScenario(ScenarioBase):

    def __init__(self):
        super().__init__(
            name="Coliziune Perpendiculara",
            description="Unghi mort — A vine din Nord, B din Vest. Fara V2X: coliziune. Cu V2X: B franeaza."
        )
        self._init_vehicles()

    def _init_vehicles(self):
        """
        Coordonate calculate astfel incat ambele vehicule sa ajunga
        la intersectie (400, 400) aproximativ in acelasi timp.

        A: incepe la (400, 50), viteza vy=4  → ajunge la y=400 in 87 tick-uri
        B: incepe la (50, 400), viteza vx=4  → ajunge la x=400 in 87 tick-uri
        → Fara interventie: coliziune garantata la tick ~87
        """
        self.vehicles = [
            Vehicle(id="A", x=400, y=50, vx=0, vy=4),  # vine din Nord
            Vehicle(id="B", x=50, y=400, vx=4, vy=0),  # vine din Vest
        ]

    def _agent_logic(self, v2x_bus: dict):
        """
        Regula prioritatii la dreapta:
          - A e prioritar (vine din dreapta lui B in sistemul nostru de coord)
          - B citeste pozitia lui A din V2X Bus si cedeaza

        Nota: In scenariul de baza ambii ar putea frana.
        Aici vrem sa demonstram o DECIZIE specifica → mai impresionant la demo.
        """
        vehicle_a = next(v for v in self.vehicles if v.id == "A")
        vehicle_b = next(v for v in self.vehicles if v.id == "B")

        # B citeste datele lui A din V2X Bus
        if "A" not in v2x_bus:
            return

        # Calculeaza TTC intre B si A
        ttc = self.calc_ttc(vehicle_b, vehicle_a)

        # Doar B ia decizia (A e prioritar — nu franeaza)
        if ttc < TTC_CRITICAL:
            vehicle_b.state = "stopped"
            vehicle_b.vx = 0
            vehicle_b.vy = 0
        elif ttc < TTC_DANGER:
            vehicle_b.state = "braking"
            vehicle_b.vx *= BRAKE_FORCE
            vehicle_b.vy *= BRAKE_FORCE
        else:
            if vehicle_b.state == "braking":
                vehicle_b.state = "normal"

        # A merge intotdeauna normal (e prioritar)
        vehicle_a.state = "normal"