"""
infrastructure.py — Agentul Infrastructura (Semafor Inteligent V2I)
--------------------------------------------------------------------

DE CE EXISTA:
  Comunicarea V2I (Vehicle-to-Infrastructure) e o parte din cerinta.
  Semaforul nu e un element pasiv — e un AGENT care:
    1. Citeste starea tuturor vehiculelor din V2X Bus
    2. Calculeaza riscuri la nivel de intersectie
    3. Publica recomandari (culoare semafor, alerte) in V2X Bus
    4. Reactioneaza la vehicule de urgenta

DIFERENTA FATA DE UN SEMAFOR NORMAL:
  Un semafor normal schimba culoarea dupa un timer fix.
  Semaforul nostru INTELLIGENT vede ca un vehicul de urgenta se apropie
  si da verde imediat, indiferent de timer — asta e V2I real.

CUM SE INTEGREAZA:
  Persoana 1 apeleaza infra_agent.update(v2x_bus) la fiecare tick,
  dupa ce vehiculele si-au publicat starea.
  Semaforul adauga in v2x_bus['INFRA'] recomandarea sa.
  Vehiculele citesc 'INFRA' si respecta semaforul daca cooperation=True.
"""

import math

# ─── Durate semafor (in tick-uri, 1 tick = 100ms) ────────────────────────────
GREEN_DURATION = 150  # 15 secunde verde
YELLOW_DURATION = 30  # 3 secunde galben
RED_DURATION = 150  # 15 secunde rosu


class InfrastructureAgent:
    """
    Agentul infrastructura — semaforul inteligent.

    Publicata in V2X Bus sub cheia 'INFRA'.
    """

    def __init__(self, intersection_x=400, intersection_y=400):
        self.intersection_x = intersection_x  # centrul intersectiei pe canvas
        self.intersection_y = intersection_y

        # Starea semaforului
        self.light = "green"
        self.timer = 0

        # Istoricul recomandarilor (pentru logging)
        self.last_recommendation = None
        self.emergency_override = False  # True daca urgenta a preluat controlul

    def update(self, v2x_bus: dict) -> dict:
        """
        Apelat la fiecare tick.

        1. Citeste vehiculele din V2X Bus
        2. Detecteaza urgente
        3. Calculeaza riscuri la nivel de intersectie
        4. Actualizeaza culoarea semaforului
        5. Publica recomandarea in V2X Bus

        Returneaza starea agentului (pentru logging si frontend).
        """
        vehicles = {
            k: v for k, v in v2x_bus.items()
            if k not in ("INFRA",) and isinstance(v, dict) and "x" in v
        }

        # ── 1. Detectie vehicul de urgenta ───────────────────────────────────
        emergency_detected = self._detect_emergency(vehicles)

        if emergency_detected:
            # Override: da verde imediat vehiculului de urgenta
            self.light = "green"
            self.emergency_override = True
            self.timer = 0  # Reseteaza timer-ul
        else:
            self.emergency_override = False
            # ── 2. Ciclu normal semafor ───────────────────────────────────────
            self._tick_light_cycle()

        # ── 3. Calculeaza recomandari de viteza ───────────────────────────────
        speed_recommendations = self._calc_speed_recommendations(vehicles)

        # ── 4. Detecteaza vehicule care se apropie de intersectie ─────────────
        approaching = self._detect_approaching(vehicles)

        # ── 5. Construieste recomandarea si o publica in V2X Bus ──────────────
        recommendation = {
            "type": "INFRA",
            "light": self.light,
            "emergency_override": self.emergency_override,
            "approaching_vehicles": approaching,
            "speed_recommendations": speed_recommendations,
            "risk_alert": len(approaching) >= 2,  # Atentie daca 2+ vehicule se apropie
        }

        v2x_bus["INFRA"] = recommendation
        self.last_recommendation = recommendation
        return recommendation

    # ── Metode interne ────────────────────────────────────────────────────────

    def _tick_light_cycle(self):
        """Ciclul normal al semaforului bazat pe timer."""
        self.timer += 1

        if self.light == "green" and self.timer >= GREEN_DURATION:
            self.light = "yellow"
            self.timer = 0
        elif self.light == "yellow" and self.timer >= YELLOW_DURATION:
            self.light = "red"
            self.timer = 0
        elif self.light == "red" and self.timer >= RED_DURATION:
            self.light = "green"
            self.timer = 0

    def _detect_emergency(self, vehicles: dict) -> bool:
        """
        Verifica daca vreun vehicul din V2X Bus are flag 'emergency': True.
        Returneaza True daca se apropie de intersectie.
        """
        for vid, vdata in vehicles.items():
            if vdata.get("emergency", False) or vdata.get("priority") == "emergency":
                # Verifica daca e aproape de intersectie
                dist = self._distance_to_intersection(vdata)
                if dist < 200:  # In raza de 200px de intersectie
                    return True
        return False

    def _distance_to_intersection(self, vdata: dict) -> float:
        """Distanta euclidiana de la vehicul la centrul intersectiei."""
        dx = vdata["x"] - self.intersection_x
        dy = vdata["y"] - self.intersection_y
        return math.sqrt(dx ** 2 + dy ** 2)

    def _detect_approaching(self, vehicles: dict) -> list:
        """
        Returneaza lista vehiculelor care se indreapta spre intersectie
        (distanta < 250px si se apropie, nu se departeaza).
        """
        approaching = []
        for vid, vdata in vehicles.items():
            dist = self._distance_to_intersection(vdata)
            if dist < 250:
                # Verifica daca se apropie (produsul scalar negativ = se indreapta spre centru)
                dx = vdata["x"] - self.intersection_x
                dy = vdata["y"] - self.intersection_y
                dot = dx * vdata.get("vx", 0) + dy * vdata.get("vy", 0)
                if dot < 0:  # Se indreapta spre intersectie
                    approaching.append({"id": vid, "distance": round(dist, 1)})
        return approaching

    def _calc_speed_recommendations(self, vehicles: dict) -> dict:
        """
        Calculeaza viteza recomandata pentru fiecare vehicul bazat pe semafor.

        Logica simpla:
          - Verde: mentine viteza
          - Galben: incetineste
          - Rosu: opreste inainte de intersectie

        In realitate asta e "Green Wave" sau "GLOSA" (Green Light Optimal Speed Advisory).
        """
        recommendations = {}
        for vid, vdata in vehicles.items():
            dist = self._distance_to_intersection(vdata)
            speed = vdata.get("speed", 0)

            if self.light == "green":
                recommendations[vid] = {"action": "maintain", "reason": "green_light"}
            elif self.light == "yellow":
                recommendations[vid] = {"action": "slow_down", "reason": "yellow_light"}
            elif self.light == "red":
                if dist < 100 and speed > 0:
                    recommendations[vid] = {"action": "stop", "reason": "red_light"}
                else:
                    recommendations[vid] = {"action": "slow_down", "reason": "red_approaching"}

        return recommendations

    def get_state(self) -> dict:
        """Starea curenta a agentului (pentru dashboard frontend)."""
        return {
            "light": self.light,
            "timer": self.timer,
            "emergency_override": self.emergency_override,
            "last_recommendation": self.last_recommendation
        }