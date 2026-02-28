"""
simulation/engine.py — Loop principal 30 FPS
"""
import asyncio
import time
from typing import List, Dict, Any
from models.vehicle import Vehicle
from models.agent import Agent
from services import v2x_bus
from services.central_system import CentralSystem
from services.infrastructure import InfrastructureAgent
from services.collision import time_to_intersection, TTC_BRAKE, TTC_YIELD
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
        self.agents:   List[Agent]   = []   # agenti autonomi per vehicul
        self.central             = CentralSystem()
        self.semaphore           = InfrastructureAgent()
        self.tick_count          = 0
        self.running             = False
        self.paused              = False
        self._last_state         = {}
        self._event_log: list    = []
        self._last_decision_idx  = 0
        self._custom_scenario: List[Dict[str, Any]] = []
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
        # Creeaza agenti autonomi per vehicul
        self.agents = [Agent(v, cooperation=self.cooperation) for v in self.vehicles]
        logger.log_info(f'Scenariu: {name}  cooperation={self.cooperation}')

    def reset(self, scenario: str = None):
        if scenario and (scenario in SCENARIOS or scenario == 'custom'):
            self.scenario_name = scenario
        self._load_scenario(self.scenario_name)

    def toggle_cooperation(self) -> bool:
        self.cooperation = not self.cooperation
        # Sincronizeaza flag-ul cooperation la toti agentii autonomi
        for agent in self.agents:
            agent.cooperation = self.cooperation
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
                    self.central._log(vehicle_id, 'CLEARANCE', reason='acordat manual de utilizator')
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
            self.agents.append(Agent(v, cooperation=self.cooperation))

        return {'ok': True, 'vehicle': entry, 'custom_scenario': self._custom_scenario}

    def custom_remove_vehicle(self, vehicle_id: str) -> dict:
        """Sterge un vehicul din scenariul custom."""
        before = len(self._custom_scenario)
        self._custom_scenario = [v for v in self._custom_scenario if v['id'] != vehicle_id]
        if len(self._custom_scenario) == before:
            return {'ok': False, 'reason': f'{vehicle_id} negasit in custom scenario'}
        if self.scenario_name == 'custom':
            self.vehicles = [v for v in self.vehicles if v.id != vehicle_id]
            self.agents   = [a for a in self.agents   if a.vehicle_id != vehicle_id]
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
            self.agents   = []
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

        all_done = self.vehicles and all(
            v.state == 'done' and v.is_off_screen() for v in self.vehicles
        )
        if all_done:
            if self.scenario_name == 'custom':
                self._load_scenario('custom')
            else:
                self._load_scenario(self.scenario_name)
            return

        # Semaforul se actualizeaza primul
        sem_state = self.semaphore.update()

        # CentralSystem decide clearance (V2I / reguli prioritate) — ramane pentru clearance
        if self.cooperation:
            self.central.decide(self.vehicles)

        # ── Agenti autonomi per vehicul ──────────────────────────────────
        # Fiecare agent publica propria stare pe bus si decide autonom
        for agent in self.agents:
            agent.decide()

        for v in self.vehicles:
            v.update()

        # Publica starea finala pe bus dupa update
        for v in self.vehicles:
            v2x_bus.publish(v.id, v.to_dict())

        # ── Calculeaza zone de risc ──────────────────────────────────────
        bus_data = {vid: data for vid, data in v2x_bus.get_all().items()
                    if vid != 'INFRA'}
        risk_zones = _compute_risk_zones(bus_data)

        # ── Event log ────────────────────────────────────────────────────
        all_decisions = self.central.get_decisions()
        new_entries = all_decisions[self._last_decision_idx:]
        if new_entries:
            self._last_decision_idx = len(all_decisions)
            self._event_log.extend(new_entries)
            if len(self._event_log) > 100:
                self._event_log = self._event_log[-100:]

        # Adauga si deciziile agentilor autonomi (din memoria lor)
        for agent in self.agents:
            mem = agent.get_memory()
            if mem:
                last = mem[-1]
                # Adauga in event_log doar daca nu e 'go' (reduce noise)
                if last.get('action') not in ('GO', None):
                    log_entry = {
                        'time':   last['tick_time'],
                        'agent':  agent.vehicle_id,
                        'action': last['action'],
                        'reason': last['reason'],
                        'ttc':    last['ttc'],
                    }
                    # Evita duplicate (verifica ultimele 5 intrari)
                    recent = self._event_log[-5:] if self._event_log else []
                    is_dup = any(
                        e.get('agent') == log_entry['agent'] and
                        e.get('action') == log_entry['action'] and
                        abs(e.get('ttc', 0) - log_entry['ttc']) < 0.1
                        for e in recent
                    )
                    if not is_dup:
                        self._event_log.append(log_entry)
                        if len(self._event_log) > 100:
                            self._event_log = self._event_log[-100:]

        # Colecteaza memoria agentilor pentru state
        agents_memory = {
            agent.vehicle_id: agent.get_memory()
            for agent in self.agents
        }

        self._last_state = {
            'tick':            self.tick_count,
            'timestamp':       time.time(),
            'cooperation':     self.cooperation,
            'scenario':        self.scenario_name,
            'paused':          self.paused,
            'vehicles':        [v.to_dict() for v in self.vehicles],
            'semaphore':       sem_state,
            'custom_scenario': self._custom_scenario,
            'risk':            {'risk': False, 'ttc': 999, 'action': 'go', 'pair': None, 'ttc_per_vehicle': {}},
            'risk_zones':      risk_zones,
            'collisions':      [],
            'event_log':       list(self._event_log[-20:]),
            'agents_memory':   agents_memory,
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
                'risk_zones': [],
                'collisions': [], 'event_log': [],
                'agents_memory': {},
            }
        self._last_state['custom_scenario'] = self._custom_scenario
        self._last_state['paused'] = self.paused
        return self._last_state


# ── Zone de risc ────────────────────────────────────────────────────────────

def _compute_risk_zones(bus_data: dict) -> list:
    """
    Calculeaza zonele de risc pe baza distantei vehiculelor fata de intersectie.
    Returneaza o lista de zone (cercuri) de desenat pe canvas:
      { x, y, radius, level: 'high'|'medium'|'low', vehicles: [id1, id2] }
    """
    import math
    INTERSECTION_X, INTERSECTION_Y = 400, 400

    # Praguri de distanta (px) pentru risc vizibil pe canvas
    # La viteza 3px/tick, 270px ≈ 90 tickuri  ≈ distanta de abordare
    DIST_HIGH   = 80    # ambele vehicule < 80px → risc înalt
    DIST_MEDIUM = 180   # ambele vehicule < 180px → risc mediu
    DIST_WARN   = 300   # ambele vehicule < 300px → risc scăzut (avertizare)

    zones = []
    ids = [vid for vid, data in bus_data.items()
           if data.get('state') not in ('done', None)]

    # Distanta fata de intersectie per vehicul
    dist_map = {}
    for vid in ids:
        v = bus_data[vid]
        dx = INTERSECTION_X - v.get('x', 0)
        dy = INTERSECTION_Y - v.get('y', 0)
        dist_map[vid] = math.sqrt(dx**2 + dy**2)

    for i, id1 in enumerate(ids):
        for id2 in ids[i+1:]:
            d1, d2 = dist_map.get(id1, 9999), dist_map.get(id2, 9999)
            # Ambele vehicule trebuie sa fie in zona de avertizare
            if d1 > DIST_WARN or d2 > DIST_WARN:
                continue
            min_dist = min(d1, d2)
            v1 = bus_data[id1]
            v2 = bus_data[id2]
            # Zona: intre cele doua vehicule, centrata pe intersectie
            # daca sunt aproape → zona la intersectie, altfel la mijlocul traseului
            cx = (v1.get('x', INTERSECTION_X) + v2.get('x', INTERSECTION_X)) / 2
            cy = (v1.get('y', INTERSECTION_Y) + v2.get('y', INTERSECTION_Y)) / 2
            # Tragem centrul spre intersectie cu 40%
            cx = cx + (INTERSECTION_X - cx) * 0.4
            cy = cy + (INTERSECTION_Y - cy) * 0.4
            # TTC afapt (px/tick) pentru afisaj
            spd1 = math.sqrt(v1.get('vx', 0)**2 + v1.get('vy', 0)**2)
            spd2 = math.sqrt(v2.get('vx', 0)**2 + v2.get('vy', 0)**2)
            ttc1 = d1 / spd1 if spd1 > 0.1 else 999
            ttc2 = d2 / spd2 if spd2 > 0.1 else 999
            min_ttc = min(ttc1, ttc2)
            # Nivel de risc bazat pe distanta
            if min_dist < DIST_HIGH:
                level, radius = 'high', 60
            elif min_dist < DIST_MEDIUM:
                level, radius = 'medium', 50
            else:
                level, radius = 'low', 40
            zones.append({
                'x':        round(cx, 1),
                'y':        round(cy, 1),
                'radius':   radius,
                'level':    level,
                'vehicles': [id1, id2],
                'ttc':      round(min_ttc, 1),
            })

    return zones


engine = SimulationEngine()
