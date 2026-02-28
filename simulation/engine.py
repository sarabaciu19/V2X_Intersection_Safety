"""
simulation/engine.py — Loop principal 30 FPS
Un tick:
  1. update() vehicule
  2. publish() pe V2X Bus
  3. central_system.decide() — acorda clearances
  4. semaphore.update()
  5. cache snapshot → get_state()
"""
import asyncio
import time
from typing import List
from models.vehicle import Vehicle
from services import v2x_bus
from services.central_system import CentralSystem
from services.infrastructure import InfrastructureAgent
from utils import logger
FPS           = 30
TICK_INTERVAL = 1.0 / FPS
# ── Scenarii ────────────────────────────────────────────────────────────
SCENARIOS = {
    'perpendicular': [
        {'id': 'A', 'direction': 'N', 'intent': 'straight'},
        {'id': 'B', 'direction': 'V', 'intent': 'straight'},
    ],
    'multi': [
        {'id': 'A', 'direction': 'N', 'intent': 'straight'},
        {'id': 'B', 'direction': 'V', 'intent': 'straight'},
        {'id': 'C', 'direction': 'S', 'intent': 'straight'},
        {'id': 'D', 'direction': 'E', 'intent': 'straight'},
    ],
    'emergency': [
        {'id': 'AMB', 'direction': 'N', 'intent': 'straight', 'priority': 'emergency', 'speed_multiplier': 1.5},
        {'id': 'B',   'direction': 'V', 'intent': 'straight'},
        {'id': 'C',   'direction': 'E', 'intent': 'straight'},
    ],
    'intents': [
        {'id': 'A', 'direction': 'N', 'intent': 'straight'},
        {'id': 'B', 'direction': 'V', 'intent': 'left'},
        {'id': 'C', 'direction': 'S', 'intent': 'right'},
    ],
}
class SimulationEngine:
    def __init__(self):
        self.scenario_name  = 'perpendicular'
        self.cooperation    = True   # False = manual mode (user grants clearances)
        self.vehicles: List[Vehicle] = []
        self.central        = CentralSystem()
        self.semaphore      = InfrastructureAgent()
        self.tick_count     = 0
        self.running        = False
        self._last_state    = {}
        self._event_log: list = []
        self._last_decision_idx = 0
        self._load_scenario('perpendicular')
    # ── Configurare ────────────────────────────────────────────────────
    def _load_scenario(self, name: str):
        defs = SCENARIOS.get(name, SCENARIOS['perpendicular'])
        v2x_bus.clear()
        logger.clear()
        self.central.reset()
        self.semaphore      = InfrastructureAgent()
        self.tick_count          = 0
        self.scenario_name       = name
        self._event_log          = []
        self._last_decision_idx  = 0
        self.vehicles = [
            Vehicle(
                id=d['id'],
                direction=d['direction'],
                intent=d.get('intent', 'straight'),
                priority=d.get('priority', 'normal'),
                speed_multiplier=d.get('speed_multiplier', 1.0),
            )
            for d in defs
        ]
        logger.log_info(f'Scenariu: {name}  cooperation={self.cooperation}')
    def reset(self, scenario: str = None):
        if scenario and scenario in SCENARIOS:
            self.scenario_name = scenario
        self._load_scenario(self.scenario_name)
    def toggle_cooperation(self) -> bool:
        self.cooperation = not self.cooperation
        # Când se trece pe manual (cooperation=False), revocă toate clearance-urile
        if not self.cooperation:
            for v in self.vehicles:
                if v.state == 'waiting':
                    v.clearance = False
        logger.log_info(f'Cooperation {"AUTO" if self.cooperation else "MANUAL"}')
        return self.cooperation

    def grant_clearance(self, vehicle_id: str) -> dict:
        """Utilizatorul acordă manual clearance unui vehicul care așteaptă."""
        for v in self.vehicles:
            if v.id == vehicle_id:
                if v.state == 'waiting':
                    v.clearance = True
                    v.state = 'crossing'
                    v.vx = v._base_vx
                    v.vy = v._base_vy
                    msg = f'Clearance manual acordat de utilizator'
                    self.central._log(vehicle_id, 'CLEARANCE', reason=msg)
                    logger.log_info(f'Manual clearance: {vehicle_id}')
                    return {'ok': True, 'vehicle_id': vehicle_id, 'state': 'crossing'}
                return {'ok': False, 'reason': f'Vehicle {vehicle_id} is {v.state}, not waiting'}
        return {'ok': False, 'reason': f'Vehicle {vehicle_id} not found'}
    def get_scenarios(self) -> list:
        return list(SCENARIOS.keys())
    # ── Loop ───────────────────────────────────────────────────────────
    async def run(self):
        self.running = True
        while self.running:
            t0 = time.monotonic()
            self._tick()
            elapsed = time.monotonic() - t0
            await asyncio.sleep(max(0.0, TICK_INTERVAL - elapsed))
    def stop(self):
        self.running = False
    # ── Tick ───────────────────────────────────────────────────────────
    def _tick(self):
        self.tick_count += 1
        # Resetare automata cand toate vehiculele au terminat
        all_done = self.vehicles and all(v.state == 'done' for v in self.vehicles)
        if all_done:
            self._load_scenario(self.scenario_name)
            return
        # 1. Clearance logic
        if self.cooperation:
            # AUTO: sistemul central decide
            self.central.decide(self.vehicles)
        # MANUAL (cooperation=False): nu acordăm nimic automat — utilizatorul decide
        # 2. Misca vehiculele
        for v in self.vehicles:
            v.update()
        # 3. Publica pe V2X Bus
        for v in self.vehicles:
            v2x_bus.publish(v.id, v.to_dict())
        # 4. Semafor
        sem_state = self.semaphore.update()
        # 5. Colecteaza decizii noi din sistemul central
        all_decisions = self.central.get_decisions()
        if not hasattr(self, '_last_decision_idx'):
            self._last_decision_idx = 0
        new_entries = all_decisions[self._last_decision_idx:]
        if new_entries:
            self._last_decision_idx = len(all_decisions)
            self._event_log.extend(new_entries)
            if len(self._event_log) > 100:
                self._event_log = self._event_log[-100:]
        # 6. Snapshot
        self._last_state = {
            'tick':        self.tick_count,
            'timestamp':   time.time(),
            'cooperation': self.cooperation,
            'scenario':    self.scenario_name,
            'vehicles':    [v.to_dict() for v in self.vehicles],
            'semaphore':   sem_state,
            'risk': {
                'risk':   False,
                'ttc':    999,
                'action': 'go',
                'pair':   None,
                'ttc_per_vehicle': {},
            },
            'collisions':  [],
            'event_log':   list(self._event_log[-10:]),
        }
    def get_state(self) -> dict:
        return self._last_state or {
            'tick': 0, 'timestamp': time.time(),
            'cooperation': self.cooperation,
            'scenario': self.scenario_name,
            'vehicles': [], 'semaphore': {'light': 'green'},
            'risk': {'risk': False, 'ttc': 999, 'action': 'go', 'pair': None, 'ttc_per_vehicle': {}},
            'collisions': [], 'event_log': [],
        }
engine = SimulationEngine()
