"""
simulation/engine.py — Loop principal 30 FPS
"""
import asyncio
import time
from typing import List, Dict, Any
from models.vehicle import Vehicle, SPAWN, VELOCITY
from services import v2x_bus
from services.central_system import CentralSystem
from services.infrastructure import InfrastructureAgent
from utils import logger

FPS           = 30
TICK_INTERVAL = 1.0 / FPS

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

# Scenariul custom editabil de utilizator
# NOTE: stocat ca atribut pe engine instance, nu ca global,
# ca sa supravietuiasca uvicorn --reload


class SimulationEngine:
    def __init__(self):
        self.scenario_name       = 'perpendicular'
        self.cooperation         = True
        self.vehicles: List[Vehicle] = []
        self.central             = CentralSystem()
        self.semaphore           = InfrastructureAgent()
        self.tick_count          = 0
        self.running             = False
        self.paused              = False
        self._last_state         = {}
        self._event_log: list    = []
        self._last_decision_idx  = 0
        self._custom_scenario: List[Dict[str, Any]] = []   # ← pe instanta
        self._load_scenario('perpendicular')

    # ── Configurare ────────────────────────────────────────────────────

    def _load_scenario(self, name: str):
        if name == 'custom':
            defs = list(self._custom_scenario)
        else:
            defs = SCENARIOS.get(name, SCENARIOS['perpendicular'])
        v2x_bus.clear()
        logger.clear()
        self.central.reset()
        self.semaphore           = InfrastructureAgent()
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
        if scenario and (scenario in SCENARIOS or scenario == 'custom'):
            self.scenario_name = scenario
        self._load_scenario(self.scenario_name)

    def toggle_cooperation(self) -> bool:
        self.cooperation = not self.cooperation
        if not self.cooperation:
            for v in self.vehicles:
                if v.state == 'waiting':
                    v.clearance = False
        logger.log_info(f'Cooperation {"AUTO" if self.cooperation else "MANUAL"}')
        return self.cooperation

    def start(self):
        """Porneste / reia simularea."""
        self.paused = False
        logger.log_info('Simulare PORNITA')

    def stop_sim(self):
        """Pauzeaza simularea (vehiculele se opresc pe loc)."""
        self.paused = True
        logger.log_info('Simulare OPRITA')

    def grant_clearance(self, vehicle_id: str) -> dict:
        for v in self.vehicles:
            if v.id == vehicle_id:
                if v.state == 'waiting':
                    v.clearance = True
                    v.state = 'crossing'
                    v.vx = v._base_vx
                    v.vy = v._base_vy
                    self.central._log_change(vehicle_id, 'CLEARANCE', 'acordat manual de utilizator')
                    return {'ok': True, 'vehicle_id': vehicle_id, 'state': 'crossing'}
                return {'ok': False, 'reason': f'{vehicle_id} este {v.state}, nu waiting'}
        return {'ok': False, 'reason': f'{vehicle_id} negasit'}

    # ── Custom scenario management ──────────────────────────────────────

    def custom_add_vehicle(self, vehicle_def: dict) -> dict:
        """Adauga un vehicul la scenariul custom."""
        vid = vehicle_def.get('id', '').strip()
        direction = vehicle_def.get('direction', '').upper()

        if not vid:
            return {'ok': False, 'reason': 'id lipsa'}
        if direction not in ('N', 'S', 'E', 'V'):
            return {'ok': False, 'reason': f'directie invalida: {direction}. Valori: N, S, E, V'}
        if any(v['id'] == vid for v in self._custom_scenario):
            return {'ok': False, 'reason': f'ID {vid} deja exista'}

        entry = {
            'id':               vid,
            'direction':        direction,
            'intent':           vehicle_def.get('intent', 'straight'),
            'priority':         vehicle_def.get('priority', 'normal'),
            'speed_multiplier': float(vehicle_def.get('speed_multiplier', 1.0)),
        }
        self._custom_scenario.append(entry)

        if self.scenario_name == 'custom':
            v = Vehicle(
                id=entry['id'],
                direction=entry['direction'],
                intent=entry['intent'],
                priority=entry['priority'],
                speed_multiplier=entry['speed_multiplier'],
            )
            self.vehicles.append(v)

        return {'ok': True, 'vehicle': entry, 'custom_scenario': self._custom_scenario}

    def custom_remove_vehicle(self, vehicle_id: str) -> dict:
        """Sterge un vehicul din scenariul custom."""
        before = len(self._custom_scenario)
        self._custom_scenario = [v for v in self._custom_scenario if v['id'] != vehicle_id]
        if len(self._custom_scenario) == before:
            return {'ok': False, 'reason': f'{vehicle_id} negasit in custom scenario'}
        if self.scenario_name == 'custom':
            self.vehicles = [v for v in self.vehicles if v.id != vehicle_id]
        return {'ok': True, 'removed': vehicle_id, 'custom_scenario': self._custom_scenario}

    def custom_update_vehicle(self, vehicle_id: str, updates: dict) -> dict:
        """Modifica parametrii unui vehicul din scenariul custom."""
        for entry in self._custom_scenario:
            if entry['id'] == vehicle_id:
                if 'intent' in updates:
                    entry['intent'] = updates['intent']
                if 'priority' in updates:
                    entry['priority'] = updates['priority']
                if 'speed_multiplier' in updates:
                    entry['speed_multiplier'] = float(updates['speed_multiplier'])
                return {'ok': True, 'vehicle': entry}
        return {'ok': False, 'reason': f'{vehicle_id} negasit'}

    def custom_clear(self) -> dict:
        self._custom_scenario = []
        if self.scenario_name == 'custom':
            self.vehicles = []
        return {'ok': True, 'custom_scenario': []}

    def get_custom_scenario(self) -> list:
        return list(self._custom_scenario)

    def get_scenarios(self) -> list:
        return list(SCENARIOS.keys()) + ['custom']

    # ── Loop ───────────────────────────────────────────────────────────

    async def run(self):
        self.running = True
        while self.running:
            t0 = time.monotonic()
            if not self.paused:
                self._tick()
            elapsed = time.monotonic() - t0
            await asyncio.sleep(max(0.0, TICK_INTERVAL - elapsed))

    def stop(self):
        self.running = False

    # ── Tick ───────────────────────────────────────────────────────────

    def _tick(self):
        self.tick_count += 1

        all_done = self.vehicles and all(v.state == 'done' for v in self.vehicles)
        if all_done:
            # Custom: nu se reseteaza automat (utilizatorul controleaza)
            if self.scenario_name == 'custom':
                # Respawn — reincarca custom cu aceleasi definitii
                self._load_scenario('custom')
            else:
                self._load_scenario(self.scenario_name)
            return

        if self.cooperation:
            self.central.decide(self.vehicles)

        for v in self.vehicles:
            v.update()

        for v in self.vehicles:
            v2x_bus.publish(v.id, v.to_dict())

        sem_state = self.semaphore.update()

        all_decisions = self.central.get_decisions()
        new_entries = all_decisions[self._last_decision_idx:]
        if new_entries:
            self._last_decision_idx = len(all_decisions)
            self._event_log.extend(new_entries)
            if len(self._event_log) > 100:
                self._event_log = self._event_log[-100:]

        self._last_state = {
            'tick':            self.tick_count,
            'timestamp':       time.time(),
            'cooperation':     self.cooperation,
            'scenario':        self.scenario_name,
            'paused':          self.paused,
            'vehicles':        [v.to_dict() for v in self.vehicles],
            'semaphore':       sem_state,
            'custom_scenario': self._custom_scenario,
            'risk': {'risk': False, 'ttc': 999, 'action': 'go', 'pair': None, 'ttc_per_vehicle': {}},
            'collisions':      [],
            'event_log':       list(self._event_log[-20:]),
        }

    def get_state(self) -> dict:
        if not self._last_state:
            return {
                'tick': 0, 'timestamp': time.time(),
                'cooperation': self.cooperation,
                'scenario': self.scenario_name,
                'paused': self.paused,
                'vehicles': [], 'semaphore': {'light': 'green'},
                'custom_scenario': self._custom_scenario,
                'risk': {'risk': False, 'ttc': 999, 'action': 'go', 'pair': None, 'ttc_per_vehicle': {}},
                'collisions': [], 'event_log': [],
            }
        # Asigura ca custom_scenario e mereu la zi (nu din cache tick)
        self._last_state['custom_scenario'] = self._custom_scenario
        self._last_state['paused'] = self.paused
        return self._last_state


engine = SimulationEngine()
