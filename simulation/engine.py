"""
simulation/engine.py — Loop-ul principal al simularii
Flux per tick (la ~30 FPS):
  1. update()  — misca vehiculele
  2. publish() — scrie pe V2X Bus
  3. decide()  — agentii iau decizii
  4. semafor   — emite stare
  5. collisions — detecteaza coliziuni fizice
  6. get_state() — snapshot complet pentru frontend/WebSocket
"""
import asyncio
import time
from typing import Dict, List
from models.vehicle import Vehicle
from models.agent import Agent
from services import v2x_bus
from services.collision import assess_risk, check_physical_collision
from services.infrastructure import InfrastructureAgent
from scenarios.perpendicular import SCENARIO as S_PERP
from scenarios.emergency import SCENARIO as S_EMG
from scenarios.speed_diff import SCENARIO as S_SPEED
from utils import logger
FPS = 30
TICK_INTERVAL = 1.0 / FPS
# Scenarii disponibile
SCENARIOS = {
    "perpendicular": S_PERP,
    "emergency":     S_EMG,
    "speed_diff":    S_SPEED,
}
class SimulationEngine:
    def __init__(self):
        self.scenario_name: str = "perpendicular"
        self.cooperation: bool = True
        self.vehicles: List[Vehicle] = []
        self.agents: List[Agent] = []
        self.semaphore = InfrastructureAgent()
        self.tick_count: int = 0
        self.running: bool = False
        self._last_state: dict = {}
        self._collision_events: list = []
        self._load_scenario("perpendicular")
    # ------------------------------------------------------------------
    # Configurare
    # ------------------------------------------------------------------
    def _load_scenario(self, name: str) -> None:
        scenario = SCENARIOS.get(name, S_PERP)
        v2x_bus.clear()
        logger.clear()
        self.vehicles = [
            Vehicle(
                id=vd.id, x=vd.x, y=vd.y,
                vx=vd.vx, vy=vd.vy,
                priority=vd.priority,
            )
            for vd in scenario.vehicles
        ]
        self.agents = [Agent(v, cooperation=self.cooperation) for v in self.vehicles]
        self.semaphore = InfrastructureAgent()
        self._collision_events.clear()
        self.tick_count = 0
        self.scenario_name = name
        logger.log_info(f"Scenariu incarcat: {name} | cooperation={self.cooperation}")
    def reset(self, scenario: str = None) -> None:
        if scenario and scenario in SCENARIOS:
            self.scenario_name = scenario
        self._load_scenario(self.scenario_name)
    def toggle_cooperation(self) -> bool:
        self.cooperation = not self.cooperation
        for agent in self.agents:
            agent.cooperation = self.cooperation
            if self.cooperation:
                agent.vehicle.state = "normal"
        logger.log_info(f"Cooperare {'ACTIVATA' if self.cooperation else 'DEZACTIVATA'}")
        return self.cooperation
    def set_scenario(self, name: str) -> None:
        if name in SCENARIOS:
            self.reset(scenario=name)
    def get_scenarios(self) -> list:
        return list(SCENARIOS.keys())
    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------
    async def run(self) -> None:
        self.running = True
        while self.running:
            t0 = time.monotonic()
            self._tick()
            elapsed = time.monotonic() - t0
            await asyncio.sleep(max(0.0, TICK_INTERVAL - elapsed))
    def stop(self) -> None:
        self.running = False
    # ------------------------------------------------------------------
    # Un singur tick
    # ------------------------------------------------------------------
    def _tick(self) -> None:
        self.tick_count += 1
        # 1. Misca vehiculele
        for v in self.vehicles:
            v.update()
        # 2. Publica pe V2X Bus
        for v in self.vehicles:
            v2x_bus.publish(v.id, v.to_dict())
        # 3. Agentii decid
        for agent in self.agents:
            agent.decide()
        # 4. Semafor
        semaphore_state = self.semaphore.update()
        # 5. Coliziuni fizice
        current = v2x_bus.get_all()
        collisions = check_physical_collision(
            {k: v for k, v in current.items() if k != "INFRA"}
        )
        for pair in collisions:
            if not self._collision_events or self._collision_events[-1].get("pair") != list(pair):
                self._collision_events.append({
                    "tick": self.tick_count,
                    "pair": list(pair),
                    "timestamp": time.time(),
                })
                logger.log_collision(pair[0], pair[1])
        # 6. Risc global
        vehicle_states = {k: v for k, v in current.items() if k != "INFRA"}
        risk = assess_risk(vehicle_states)
        # 7. Cache snapshot
        self._last_state = {
            "tick": self.tick_count,
            "timestamp": time.time(),
            "cooperation": self.cooperation,
            "scenario": self.scenario_name,
            "vehicles": [v.to_dict() for v in self.vehicles],
            "risk": risk,
            "semaphore": semaphore_state,
            "collisions": self._collision_events[-5:],
            "event_log": logger.get_recent(10),
        }
    def get_state(self) -> dict:
        return self._last_state or {
            "tick": 0, "timestamp": time.time(),
            "cooperation": self.cooperation,
            "scenario": self.scenario_name,
            "vehicles": [], "risk": {"risk": False, "ttc": 999, "action": "go",
                                     "pair": None, "ttc_per_vehicle": {}},
            "semaphore": {"light": "green", "phase": "NS", "emergency": False,
                          "recommendation": "starting", "green_for": [], "red_for": []},
            "collisions": [], "event_log": [],
        }
# Instanta globala — importata de server.py
engine = SimulationEngine()
