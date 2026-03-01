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
from services.collision import time_to_intersection, TTC_BRAKE, TTC_YIELD, check_physical_collision
from utils import logger
from scenarios import SCENARIOS, NO_SEMAPHORE_SCENARIOS

FPS           = 30
TICK_INTERVAL = 1.0 / FPS


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
        self._custom_scenario: List[Dict[str, Any]] = []
        self._custom_has_semaphore: bool = True  # default: custom cu semafor
        self._crash_timers: Dict[str, int] = {}   # vehicle_id -> tick cand a intrat in crashed
        self._active_collisions: list = []         # coliziuni active (vizibile pe canvas)
        self._load_scenario('perpendicular')

    # ── Configurare ────────────────────────────────────────────────────

    def _load_scenario(self, name: str):
        if name == 'custom':
            has_semaphore = self._custom_has_semaphore
            defs = list(self._custom_scenario)
        else:
            has_semaphore = name not in NO_SEMAPHORE_SCENARIOS
            defs = SCENARIOS.get(name, SCENARIOS['perpendicular'])
        v2x_bus.clear()
        logger.clear()
        self.central.reset()
        self.semaphore           = InfrastructureAgent()
        self.tick_count          = 0
        self.scenario_name       = name
        self._event_log          = []
        self._crash_timers       = {}
        self._active_collisions  = []
        # Calculam spawn_tick (2 secunde delay = 60 ticks per vehicul pe aceeasi directie)
        # Si offset de pozitie ca sa nu se suprapuna la spawn
        lane_counts = {}
        SPAWN_GAP = 30
        self.vehicles = []
        for d in defs:
            direction = d['direction']
            count = lane_counts.get(direction, 0)
            
            v = Vehicle(
                id=d['id'],
                direction=direction,
                intent=d.get('intent', 'straight'),
                priority=d.get('priority', 'normal'),
                speed_multiplier=d.get('speed_multiplier', 1.0),
                v2x_enabled=d.get('v2x_enabled', True),
                no_stop=d.get('no_stop', False),
                spawn_tick=count * 30 # Reduced from 80 to 30 (1s)
            )
            
            # Repozitionam vehiculul "in spate" pe baza indexului de spawn
            if direction == 'N': v.y -= count * 60
            elif direction == 'S': v.y += count * 60
            elif direction == 'E': v.x += count * 60
            elif direction == 'V': v.x -= count * 60

            # Offset manual de pozitie (pentru sincronizare timpi de sosire)
            v.x += d.get('spawn_x_offset', 0)
            v.y += d.get('spawn_y_offset', 0)

            # Sincronizam _init pentru reset
            v._init = (v.x, v.y, v.vx, v.vy)
            
            self.vehicles.append(v)
            lane_counts[direction] = count + 1
        
        # Creeaza agenti autonomi per vehicul
        self.agents = [Agent(v, cooperation=self.cooperation) for v in self.vehicles]
        
        # Configureaza semaforul si sistemul central in functie de scenariu
        self.semaphore.reset(has_semaphore)
        self.central.set_semaphore_state(has_semaphore)

        # Publica starea INITIALA pe bus (important daca e pauza)
        self.semaphore.update()
        for v in self.vehicles:
            v2x_bus.publish(v.id, v.to_dict())
            
        logger.log_info(f'Scenariu: {name} (cooperation={self.cooperation}) încărcat.')
        self._update_state()

    def reset(self, scenario: str = None):
        logger.log_info(f"RESET cerut pentru: {scenario} (curent: {self.scenario_name})")
        if scenario and (scenario in SCENARIOS or scenario == 'custom'):
            self.scenario_name = scenario
        self._load_scenario(self.scenario_name)
        self._update_state()

    def _update_state(self):
        """Genereaza si salveaza starea curenta pentru API / frontend."""
        bus_data = {vid: data for vid, data in v2x_bus.get_all().items()
                    if vid != 'INFRA'}
        risk_zones = _compute_risk_zones(bus_data)
        
        # Sursa principala pentru panoul de sus (banner risc)
        from services.collision import assess_risk
        global_risk = assess_risk(bus_data)

        agents_memory = {
            agent.vehicle_id: agent.get_memory()
            for agent in self.agents
        }
        
        sem_state = self.semaphore.get_state() if hasattr(self.semaphore, 'get_state') else {}
        # Adaug flag-ul has_semaphore in sem_state pentru frontend
        sem_state['has_semaphore'] = self.semaphore.has_semaphore

        self._last_state = {
            'tick':            self.tick_count,
            'timestamp':       time.monotonic(),
            'cooperation':     self.cooperation,
            'scenario':        self.scenario_name,
            'paused':          self.paused,
            'vehicles':        [v.to_dict() for v in self.vehicles if v.state != 'done'],
            'semaphore':       sem_state,
            'custom_scenario': self._custom_scenario,
            'custom_has_semaphore': self._custom_has_semaphore,
            'risk':            global_risk,
            'risk_zones':      risk_zones,
            'event_log':       list(logger.get_all()[-20:]),
            'collisions':      list(self._active_collisions),
            'agents_memory':   agents_memory
        }

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
            'v2x_enabled':      vehicle_def.get('v2x_enabled', True),
        }
        
        # Calculam spawn_tick si offset bazat pe cate masini sunt deja pe aceeasi directie
        direction = entry['direction']
        count = sum(1 for v in self._custom_scenario if v['direction'] == direction)
        entry['spawn_tick'] = count * 30 # 30 ticks = 1s
        entry['spawn_offset'] = count * 60 # 60px gap for safety
        
        self._custom_scenario.append(entry)

        if self.scenario_name == 'custom':
            v = Vehicle(
                id=entry['id'],
                direction=entry['direction'],
                intent=entry['intent'],
                priority=entry['priority'],
                speed_multiplier=entry['speed_multiplier'],
                v2x_enabled=entry['v2x_enabled'],
                spawn_tick=entry.get('spawn_tick', 0)
            )
            
            # Aplica offset-ul si pentru custom (bazat pe spawn_offset salvat)
            offset = entry.get('spawn_offset', 0)
            if v.direction == 'N': v.y -= offset
            elif v.direction == 'S': v.y += offset
            elif v.direction == 'E': v.x += offset
            elif v.direction == 'V': v.x -= offset
            v._init = (v.x, v.y, v.vx, v.vy)
            
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
                if 'v2x_enabled' in updates:
                    entry['v2x_enabled'] = bool(updates['v2x_enabled'])
                return {'ok': True, 'vehicle': entry}
        return {'ok': False, 'reason': f'{vehicle_id} negasit'}

    def custom_clear(self) -> dict:
        self._custom_scenario = []
        self._custom_has_semaphore = True  # reset la default
        if self.scenario_name == 'custom':
            self.vehicles = []
            self.agents   = []
        return {'ok': True, 'custom_scenario': []}

    def set_custom_semaphore(self, has_semaphore: bool) -> dict:
        """Setează dacă scenariul custom are semafor sau nu."""
        self._custom_has_semaphore = has_semaphore
        return {'ok': True, 'has_semaphore': has_semaphore}

    def get_custom_scenario(self) -> list:
        return list(self._custom_scenario)

    def get_scenarios(self) -> list:
        return list(SCENARIOS.keys()) + ['custom']

    # ── Loop ───────────────────────────────────────────────────────────

    async def run(self):
        self.running = True
        while self.running:
            t0 = time.monotonic()
            try:
                if not self.paused:
                    self._tick()
            except Exception as e:
                logger.log_info(f"FATAL Simulation Error: {e}")
                import traceback
                traceback.print_exc()
            elapsed = time.monotonic() - t0
            await asyncio.sleep(max(0.0, TICK_INTERVAL - elapsed))

    def stop(self):
        self.running = False

    # ── Tick ───────────────────────────────────────────────────────────

    def _tick(self):
        self.tick_count += 1

        all_done = self.vehicles and all(
            v.state in ('done', 'crashed') for v in self.vehicles
        )
        # Verifica daca toate masinile au terminat sau au fost crashuite si timeouted
        really_done = self.vehicles and all(
            v.state == 'done' for v in self.vehicles
        )
        if really_done:
            if self.scenario_name == 'custom':
                self._load_scenario('custom')
            else:
                self._load_scenario(self.scenario_name)
            return

        # Semaforul se actualizeaza primul
        sem_state = self.semaphore.update()

        # Publica starea curenta pe bus INAINTE de decizii
        for v in self.vehicles:
            v2x_bus.publish(v.id, v.to_dict())

        # CentralSystem decide clearance (V2I / reguli prioritate)
        if self.cooperation:
            self.central.decide(self.vehicles)

        # Agenti autonomi — decizia LLM seteaza flag-ul agent_yield pe vehicul
        # vehicle.update() il respecta in _desired_speed_factor() → factor=0 → oprire
        for agent in self.agents:
            action = agent.decide()
            v = agent.vehicle
            # Nu intervenim daca vehiculul e deja in waiting/crossing/crashed/done
            if v.state in ("waiting", "crossing", "crashed", "done"):
                v.agent_yield = False
                continue
            if action == "yield":
                v.agent_yield = True
            else:  # go
                v.agent_yield = False

        # Updateaza pozitiile — pasam vehiculele pe aceeasi directie pentru following
        active = [v for v in self.vehicles if v.state != 'done']
        for v in self.vehicles:
            same_dir = [o for o in active
                        if o.id != v.id and o.direction == v.direction]
            v.update(same_dir, active_vehicles=active, current_tick=self.tick_count)

        # Publica starea finala pentru bus
        for v in self.vehicles:
            v2x_bus.publish(v.id, v.to_dict())

        # ── Detectare coliziuni fizice ────────────────────────────────────
        # Ignoram vehiculele care nu s-au spawnat inca
        active_data = {
            v.id: v.to_dict() for v in self.vehicles 
            if v.state not in ('done', 'crashed') and getattr(v, 'spawn_tick', 0) <= self.tick_count
        }
        collisions = check_physical_collision(active_data)
        for (id1, id2) in collisions:
            # Marcam vehiculele ca 'crashed' daca nu sunt deja
            for vid in (id1, id2):
                if vid not in self._crash_timers:
                    self._crash_timers[vid] = self.tick_count
                    logger.log_decision(vid, '💥 COLIZIUNE', 0.0, f'coliziune fizică cu {id2 if vid == id1 else id1}')
                for v in self.vehicles:
                    if v.id == vid and v.state != 'crashed':
                        v.state = 'crashed'
                        v.vx = 0.0
                        v.vy = 0.0
            pair_key = tuple(sorted([id1, id2]))
            if not any(tuple(sorted(c['vehicles'])) == pair_key for c in self._active_collisions):
                self._active_collisions.append({'vehicles': [id1, id2], 'tick': self.tick_count})

        # ── Timeout crashed vehicles: dupa 60 ticks (~2s) → done ─────────
        CRASH_TIMEOUT = 60
        for vid, crash_tick in list(self._crash_timers.items()):
            delta = self.tick_count - crash_tick
            if delta >= CRASH_TIMEOUT:
                for v in self.vehicles:
                    if v.id == vid:
                        v.state = 'done'
                        v2x_bus.publish(v.id, v.to_dict()) # update final pentru frontend
                del self._crash_timers[vid]
                logger.log_decision(vid, '🗑 REMOVED', 0.0, 'vehicul avariat îndepărtat din scenă')

        # Curata coliziunile active daca ambele vehicule sunt done
        self._active_collisions = [
            c for c in self._active_collisions
            if not all(
                any(v.id == vid and v.state == 'done' for v in self.vehicles)
                for vid in c['vehicles']
            )
        ]

        self._update_state()

    def get_state(self) -> dict:
        st = self._last_state or {}
        if st:
            st['paused'] = self.paused
            st['cooperation'] = self.cooperation
        return st


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
