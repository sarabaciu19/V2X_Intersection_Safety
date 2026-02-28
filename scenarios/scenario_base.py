
class ScenarioBase:
    """
    Clasa de baza. Toate scenariile o mostenesc.

    Fiecare scenariu concret trebuie sa:
      1. Apeleze super().__init__(name, description)
      2. Populeze self.vehicles cu obiecte Vehicle
      3. Optionally: suprascrie _agent_logic() pentru comportament custom
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.vehicles: list[Vehicle] = []
        self.collision_occurred = False
        self.cooperation_enabled = True
        self.tick_count = 0
        self.collision_tick = None

    # ── Metode publice (apelate din simulatorul Persoanei 1) ─────────────────

    def reset(self):
        """Reseteaza scenariul la starea initiala (butonul Reset din frontend)."""
        for v in self.vehicles:
            v.reset()
        self.collision_occurred = False
        self.tick_count = 0
        self.collision_tick = None

    def set_cooperation(self, enabled: bool):
        """
        Activeaza/dezactiveaza cooperarea V2X.
        Cand e False: agentii NU reactioneaza la datele celorlalti → coliziune.
        Cand e True: agentii folosesc datele V2X → coliziune evitata.
        """
        self.cooperation_enabled = enabled

    def update(self, v2x_bus: dict) -> dict:
        """
        Apelat la fiecare tick de simulare (100ms).

        1. Publica starea fiecarui vehicul in V2X Bus
        2. Daca cooperation=True: ruleaza logica de decizie
        3. Updateaza pozitiile
        4. Detecteaza coliziuni
        5. Returneaza starea completa pentru WebSocket
        """
        self.tick_count += 1

        # Pasul 1: Fiecare vehicul isi publica starea in V2X Bus
        for v in self.vehicles:
            v2x_bus[v.id] = v.to_dict()

        # Pasul 2: Logica de decizie (doar daca cooperare activa)
        if self.cooperation_enabled:
            self._agent_logic(v2x_bus)

        # Pasul 3: Update pozitii
        for v in self.vehicles:
            v.x += v.vx
            v.y += v.vy

        # Pasul 4: Detectie coliziune
        self._detect_collisions()

        # Pasul 5: Returneaza starea
        return self._build_state(v2x_bus)

    # ── Metode interne ───────────────────────────────────────────────────────

    def calc_ttc(self, v1: Vehicle, v2: Vehicle) -> float:
        """
        Calculeaza Time To Collision intre 2 vehicule.

        Formula: TTC = distanta / viteza_relativa

        Daca vehiculele se departeaza (viteza relativa negativa) → nu e risc → returnam 999.
        """
        dx = v2.x - v1.x
        dy = v2.y - v1.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Viteza relativa = cat de repede se apropie unul de celalalt
        rel_vx = v1.vx - v2.vx
        rel_vy = v1.vy - v2.vy
        relative_speed = math.sqrt(rel_vx ** 2 + rel_vy ** 2)

        if relative_speed < 0.01:
            return 999.0  # Nu se apropie — nu e pericol

        ttc = distance / relative_speed
        return round(ttc, 2)

    def _detect_collisions(self):
        """Verifica daca oricare 2 vehicule se suprapun (coliziune)."""
        vehicles = self.vehicles
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                v1, v2 = vehicles[i], vehicles[j]
                dx = v1.x - v2.x
                dy = v1.y - v2.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist < COLLISION_RADIUS:
                    self.collision_occurred = True
                    self.collision_tick = self.tick_count

    def _agent_logic(self, v2x_bus: dict):
        """
        Logica de decizie implicita.

        Fiecare vehicul citeste V2X Bus, calculeaza TTC cu ceilalti,
        si decide: normal / franeaza / stop.

        Scenariile concrete pot suprascrie aceasta metoda pentru
        comportament specific (ex: urgenta, prioritate semafor).
        """
        for v in self.vehicles:
            min_ttc = 999.0

            for other_id, other_data in v2x_bus.items():
                if other_id == v.id or other_id == "INFRA":
                    continue

                # Construieste obiect temporar pentru calcul TTC
                other = Vehicle(
                    vehicle_id=other_data["id"],
                    x=other_data["x"], y=other_data["y"],
                    vx=other_data["vx"], vy=other_data["vy"],
                    priority=other_data.get("priority", "normal")
                )

                # Vehiculul de urgenta are prioritate absoluta — nu franeaza
                if other.priority == "emergency":
                    # Ceilalti cedeza in fata lui, nu invers
                    ttc = self.calc_ttc(v, other)
                    if ttc < TTC_DANGER and v.priority != "emergency":
                        v.state = "stopped"
                        v.vx = 0
                        v.vy = 0
                    continue

                ttc = self.calc_ttc(v, other)
                min_ttc = min(min_ttc, ttc)

            # Decizie bazata pe TTC minim detectat
            if min_ttc < TTC_CRITICAL:
                v.state = "stopped"
                v.vx *= 0  # Stop complet
                v.vy *= 0
            elif min_ttc < TTC_DANGER:
                v.state = "braking"
                v.vx *= BRAKE_FORCE  # Reduce viteza gradual
                v.vy *= BRAKE_FORCE
            else:
                # Daca a franaat dar pericolul a trecut, reia viteza
                # (nu complet — in realitate ai nevoie de accelerare progresiva)
                if v.state in ("braking",):
                    v.state = "normal"

    def _build_state(self, v2x_bus: dict) -> dict:
        """Construieste starea completa pentru WebSocket (trimisa la frontend)."""
        # Calculeaza TTC minim global (pentru overlay-ul de risc)
        min_ttc = 999.0
        vehicles = self.vehicles
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                ttc = self.calc_ttc(vehicles[i], vehicles[j])
                min_ttc = min(min_ttc, ttc)

        return {
            "scenario": self.name,
            "tick": self.tick_count,
            "cooperation": self.cooperation_enabled,
            "vehicles": [v.to_dict() for v in self.vehicles],
            "ttc_global": min_ttc if min_ttc < 999 else None,
            "risk_level": self._get_risk_level(min_ttc),
            "collision": self.collision_occurred,
            "collision_tick": self.collision_tick,
            "v2x_bus": {k: v for k, v in v2x_bus.items()}
        }

    def _get_risk_level(self, ttc: float) -> str:
        """Traduce TTC numeric in nivel de risc pentru frontend."""
        if ttc < TTC_CRITICAL:
            return "critical"
        elif ttc < TTC_DANGER:
            return "danger"
        elif ttc < 5.0:
            return "warning"
        else:
            return "safe"