"""
simulator.py — Loop-ul de simulare V2X (tick la 100 ms)

Responsabilități (Ziua 1 — Dimineață):
  ✅ Clasa Vehicle cu x, y, vx, vy, id, intent
  ✅ Loop de simulare (tick la 100 ms) cu update poziții
  ✅ Testare că 2 vehicule se mișcă pe ecran (log)
  ✅ Format mesaj V2X definit + sistem de coordonate agreat cu echipa

Cum se rulează:
  python simulator.py
"""

import asyncio
import logging
import time

from vehicle import Vehicle

# ---------------------------------------------------------------------------
# Logging structurat
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("V2X-Simulator")

# ---------------------------------------------------------------------------
# Constante
# ---------------------------------------------------------------------------
TICK_INTERVAL_S = 0.1       # 100 ms per tick
INTERSECTION_ZONE = 30      # raza zonei de intersecție (unități)
TTC_DANGER = 3.0            # secunde — pericol → frânare
TTC_STOP = 1.5              # secunde — stop complet


# ---------------------------------------------------------------------------
# V2X Message Bus (dict partajat — simplu, fără asyncio.Queue pentru acum)
# ---------------------------------------------------------------------------
class V2XMessageBus:
    """
    Dict partajat care simulează broadcast-ul mesajelor V2X.
    Fiecare vehicul scrie propria stare; oricine poate citi.
    """

    def __init__(self):
        self._messages: dict[str, dict] = {}

    def publish(self, msg: dict) -> None:
        self._messages[msg["id"]] = msg

    def get_all(self) -> list[dict]:
        return list(self._messages.values())

    def get(self, vehicle_id: str) -> dict | None:
        return self._messages.get(vehicle_id)


# ---------------------------------------------------------------------------
# Calcul TTC (Time To Collision)
# ---------------------------------------------------------------------------
def calc_ttc(v1: Vehicle, v2: Vehicle) -> float:
    """
    Estimează timpul până la coliziune dintre două vehicule.

    Metodă: proiecție liniară a poziției relative.
    Returnează 999 dacă vehiculele se depărtează sau sunt la același punct.
    """
    from math import sqrt

    dx = v2.x - v1.x
    dy = v2.y - v1.y
    dist = sqrt(dx ** 2 + dy ** 2)

    # Viteze relative
    dvx = v1.vx - v2.vx
    dvy = v1.vy - v2.vy
    rel_v = sqrt(dvx ** 2 + dvy ** 2)

    if rel_v == 0:
        return 999.0

    ttc = dist / rel_v
    return round(ttc, 3)


# ---------------------------------------------------------------------------
# Simulator principal
# ---------------------------------------------------------------------------
class Simulator:
    """
    Gestionează loop-ul de simulare și agenții V2X.

    cooperation=True  → vehiculele comunică și frânează bazat pe TTC
    cooperation=False → vehiculele ignoră mesajele V2X (demo coliziune)
    """

    def __init__(self, vehicles: list[Vehicle], cooperation: bool = True):
        self.vehicles = vehicles
        self.cooperation = cooperation
        self.bus = V2XMessageBus()
        self.tick_count = 0
        self.running = False
        self.decision_log: list[dict] = []   # ultimele decizii ale agenților

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    async def run(self, max_ticks: int = 200) -> None:
        """
        Pornește simularea asincronă.
        max_ticks = 200 → ~20 secunde la 100 ms/tick
        """
        self.running = True
        log.info("=" * 60)
        log.info("🚗 Simulator V2X pornit")
        log.info(f"   Vehicule: {[v.id for v in self.vehicles]}")
        log.info(f"   Cooperare: {'ON ✅' if self.cooperation else 'OFF ❌'}")
        log.info(f"   TTC pericol: {TTC_DANGER}s | TTC stop: {TTC_STOP}s")
        log.info("=" * 60)

        while self.running and self.tick_count < max_ticks:
            tick_start = time.monotonic()

            self._tick()

            # Respectăm intervalul de 100 ms
            elapsed = time.monotonic() - tick_start
            sleep_time = max(0.0, TICK_INTERVAL_S - elapsed)
            await asyncio.sleep(sleep_time)

        log.info("=" * 60)
        log.info(f"✅ Simulare încheiată după {self.tick_count} tick-uri "
                 f"({self.tick_count * TICK_INTERVAL_S:.1f}s)")
        log.info("=" * 60)

    def stop(self) -> None:
        self.running = False

    # ------------------------------------------------------------------
    # Un singur tick
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        self.tick_count += 1

        # 1. Fiecare vehicul publică starea sa pe bus-ul V2X
        for v in self.vehicles:
            self.bus.publish(v.to_v2x_message())

        # 2. Logică de decizie (cooperation)
        if self.cooperation:
            self._apply_cooperation_logic()

        # 3. Update poziții
        for v in self.vehicles:
            v.update_position()

        # 4. Log starea la fiecare 5 tick-uri (nu spam)
        if self.tick_count % 5 == 0:
            self._log_state()

        # 5. Verifică coliziuni
        self._check_collisions()

    # ------------------------------------------------------------------
    # Logică cooperare V2X
    # ------------------------------------------------------------------

    def _apply_cooperation_logic(self) -> None:
        """
        Pentru fiecare pereche de vehicule, calculează TTC.
        Dacă TTC < TTC_DANGER → vehiculul mai lent frânează.
        Dacă TTC < TTC_STOP  → vehiculul mai lent se oprește complet.
        """
        from math import sqrt

        vehicles = self.vehicles
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                v1, v2 = vehicles[i], vehicles[j]

                # Ignoră vehicule deja oprite
                speed_v1 = sqrt(v1.vx ** 2 + v1.vy ** 2)
                speed_v2 = sqrt(v2.vx ** 2 + v2.vy ** 2)
                if speed_v1 == 0 and speed_v2 == 0:
                    continue

                ttc = calc_ttc(v1, v2)

                # Vehiculul care cedează = cel fără prioritate de urgență
                # Dacă ambele normale → cel cu viteză mai mică frânează primul
                if ttc < TTC_STOP:
                    loser = v2 if v2.priority != "emergency" else v1
                    if sqrt(loser.vx ** 2 + loser.vy ** 2) > 0:
                        loser.stop()
                        self._record_decision(loser.id, "STOP", ttc, v1.id, v2.id)

                elif ttc < TTC_DANGER:
                    loser = v2 if v2.priority != "emergency" else v1
                    if not loser.braking:
                        loser.apply_braking(factor=0.6)
                        self._record_decision(loser.id, "BRAKE", ttc, v1.id, v2.id)

    def _record_decision(
        self, agent_id: str, action: str, ttc: float, id1: str, id2: str
    ) -> None:
        entry = {
            "tick": self.tick_count,
            "agent": agent_id,
            "action": action,
            "ttc": ttc,
            "pair": (id1, id2),
            "timestamp": time.time(),
        }
        self.decision_log.append(entry)
        log.warning(
            f"⚠️  DECIZIE | Tick {self.tick_count:>4} | "
            f"Agent {agent_id} → {action} | TTC={ttc:.2f}s | "
            f"Pereche: ({id1}, {id2})"
        )

    # ------------------------------------------------------------------
    # Coliziuni
    # ------------------------------------------------------------------

    def _check_collisions(self) -> None:
        from math import sqrt

        for i in range(len(self.vehicles)):
            for j in range(i + 1, len(self.vehicles)):
                v1, v2 = self.vehicles[i], self.vehicles[j]
                dist = sqrt((v2.x - v1.x) ** 2 + (v2.y - v1.y) ** 2)
                if dist < 10:  # <10 unități → coliziune
                    log.error(
                        f"💥 COLIZIUNE! {v1.id} ↔ {v2.id} | "
                        f"dist={dist:.2f} | tick={self.tick_count}"
                    )

    # ------------------------------------------------------------------
    # Logging stare
    # ------------------------------------------------------------------

    def _log_state(self) -> None:
        t = self.tick_count * TICK_INTERVAL_S
        log.info(f"--- Tick {self.tick_count:>4} | t={t:.1f}s ---")
        for v in self.vehicles:
            msg = v.to_v2x_message()
            log.info(
                f"  [{v.id}] pos=({msg['x']:>8.2f}, {msg['y']:>8.2f}) | "
                f"vel=({msg['vx']:>5.2f}, {msg['vy']:>5.2f}) | "
                f"intent={msg['intent']:<10} | "
                f"priority={msg['priority']:<10} | "
                f"braking={msg['braking']}"
            )


# ---------------------------------------------------------------------------
# Entry point — test cu 2 vehicule (Ziua 1 Dimineață)
# ---------------------------------------------------------------------------

def make_test_scenario() -> list[Vehicle]:
    """
    Scenariu de test: 2 vehicule pe traiectorii perpendiculare
    care se îndreaptă spre intersecția din (0, 0).

    Vehicul A: vine de jos (y=-200) → se mișcă în sus (vy=+5)
    Vehicul B: vine din stânga (x=-200) → se mișcă spre dreapta (vx=+5)
    """
    vehicle_a = Vehicle(
        vehicle_id="A",
        x=0,
        y=-200,
        vx=0,
        vy=5,
        intent="straight",
    )
    vehicle_b = Vehicle(
        vehicle_id="B",
        x=-200,
        y=0,
        vx=5,
        vy=0,
        intent="straight",
    )
    return [vehicle_a, vehicle_b]


async def main():
    log.info("🔧 V2X Intersection Safety — Ziua 1 Dimineață")
    log.info("   Sistem de coordonate: intersecție la (0,0), vehicule din ±200")

    # --- Test 1: Cu cooperare (vehiculul frânează) ---
    log.info("\n📋 SCENARIUL 1 — Cooperare ON")
    vehicles = make_test_scenario()
    sim = Simulator(vehicles, cooperation=True)
    await sim.run(max_ticks=50)

    log.info(f"\n📊 Decizii luate: {len(sim.decision_log)}")
    for d in sim.decision_log:
        log.info(f"   Tick {d['tick']:>3}: {d['agent']} → {d['action']} (TTC={d['ttc']:.2f}s)")

    # --- Test 2: Fără cooperare (coliziune demonstrată) ---
    log.info("\n📋 SCENARIUL 2 — Cooperare OFF (demo coliziune)")
    vehicles2 = make_test_scenario()
    sim2 = Simulator(vehicles2, cooperation=False)
    await sim2.run(max_ticks=50)


if __name__ == "__main__":
    asyncio.run(main())
