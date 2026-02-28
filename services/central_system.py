"""
services/central_system.py — Sistem central cu regulile de circulatie din Romania
Reguli (OUG 195/2002):
  1. Urgenta trece primul
  2. Vehicul deja in intersectie (crossing) continua
  3. Prioritate de dreapta
  4. Viraj stanga cedeaza celor care merg inainte/dreapta
  5. Egalitate -> FIFO
"""
import time
from typing import List, Dict, Optional
from utils import logger
# RIGHT_OF[dir] = directia care vine din DREAPTA ta (tu cedezi acelei directii)
# N merge spre S -> dreapta sa e V (Vest)
# E merge spre V -> dreapta sa e N (Nord)
# S merge spre N -> dreapta sa e E (Est)
# V merge spre E -> dreapta sa e S (Sud)
RIGHT_OF: Dict[str, str] = {
    'N': 'V',
    'E': 'N',
    'S': 'E',
    'V': 'S',
}
OPPOSITE = {'N': 'S', 'S': 'N', 'E': 'V', 'V': 'E'}
def _has_conflict(d1: str, i1: str, d2: str, i2: str) -> bool:
    if d1 == d2:
        return False
    if OPPOSITE.get(d1) == d2:
        if i1 == 'straight' and i2 == 'straight':
            return False
        return True
    return True  # perpendicular -> conflict mereu
def _who_yields(d1: str, i1: str, d2: str, i2: str) -> Optional[str]:
    # Viraj stanga cedeaza
    if i1 == 'left' and i2 != 'left':
        return d1
    if i2 == 'left' and i1 != 'left':
        return d2
    # Prioritate de dreapta:
    # d1 cedeaza daca d2 vine din dreapta lui d1
    if RIGHT_OF.get(d1) == d2:
        return d1
    # d2 cedeaza daca d1 vine din dreapta lui d2
    if RIGHT_OF.get(d2) == d1:
        return d2
    # Egalitate (ex: ambii au prioritate egala) -> FIFO
    return None
class CentralSystem:
    def __init__(self):
        self.waiting_since: Dict[str, float] = {}
        self.decisions:     List[dict]       = []
        self._last_logged:  Dict[str, str]   = {}
        self._prev_crossing: set             = set()
    def decide(self, vehicles: list) -> Dict[str, bool]:
        now = time.time()
        clearances = {v.id: False for v in vehicles}
        waiting  = [v for v in vehicles if v.state == 'waiting']
        crossing = [v for v in vehicles if v.state == 'crossing']
        # ── Track timp asteptare ──────────────────────────────────────
        current_waiting_ids = {v.id for v in waiting}
        for v in waiting:
            self.waiting_since.setdefault(v.id, now)
        for vid in list(self.waiting_since):
            if vid not in current_waiting_ids:
                del self.waiting_since[vid]
                self._last_logged.pop(vid, None)
        # Daca un vehicul a TERMINAT traversarea (era crossing, acum nu mai e)
        # -> reseteaza log-ul pentru cei care asteptau dupa el
        current_crossing_ids = {v.id for v in crossing}
        finished = self._prev_crossing - current_crossing_ids
        if finished:
            for v in waiting:
                self._last_logged.pop(v.id, None)
        self._prev_crossing = current_crossing_ids
        # ── 1. Cei care traverseaza continua ─────────────────────────
        for v in crossing:
            clearances[v.id] = True
        # ── 2. Urgente trec imediat ───────────────────────────────────
        emergency = [v for v in waiting if v.priority == 'emergency']
        for ev in emergency:
            clearances[ev.id] = True
            self._log_change(ev.id, 'CLEARANCE', '🚑 urgenta - prioritate maxima')
        # ── 3. Vehicule normale - aplica regulile ─────────────────────
        # Sorteaza candidatii: cei cu prioritate de dreapta fata de altii merg primul
        # Scor prioritate: numara cati alti candidati cedeaza fata de tine
        # (mai multi cedeaza fata de tine = prioritate mai mare = treci primul)
        normal = [v for v in waiting if v.priority != 'emergency']

        def priority_score(v):
            score = 0
            for other in normal:
                if other.id == v.id:
                    continue
                if _has_conflict(v.direction, v.intent, other.direction, other.intent):
                    loser = _who_yields(v.direction, v.intent, other.direction, other.intent)
                    if loser == other.direction:
                        score += 1   # other cedeaza fata de v => v are prioritate
                    elif loser == v.direction:
                        score -= 1   # v cedeaza fata de other => other are prioritate
            return (-score, self.waiting_since.get(v.id, now))  # desc prioritate, asc timp

        normal = sorted(normal, key=priority_score)
        granted = list(crossing) + list(emergency)
        for candidate in normal:
            yield_reason: Optional[str] = None
            for active in granted:
                if not _has_conflict(candidate.direction, candidate.intent,
                                     active.direction,   active.intent):
                    continue
                loser = _who_yields(candidate.direction, candidate.intent,
                                    active.direction,   active.intent)
                if loser == candidate.direction:
                    yield_reason = _explain_yield(candidate, active)
                    break
                elif loser == active.direction:
                    yield_reason = f'asteapta sa termine {active.id}'
                    break
                else:
                    # FIFO
                    wait_c = now - self.waiting_since.get(candidate.id, now)
                    wait_a = now - self.waiting_since.get(active.id, now)
                    if wait_c < wait_a:
                        yield_reason = f'FIFO: {active.id} asteapta de mai mult'
                        break
            if yield_reason:
                clearances[candidate.id] = False
                self._log_change(candidate.id, 'ASTEAPTA', yield_reason)
            else:
                clearances[candidate.id] = True
                granted.append(candidate)
                waited = round(now - self.waiting_since.get(candidate.id, now), 1)
                self._log_change(candidate.id, 'CLEARANCE',
                                 f'clearance acordat (asteptat {waited}s)')
        # ── Aplica pe obiecte ─────────────────────────────────────────
        for v in vehicles:
            v.clearance = clearances[v.id]
        return clearances
    def _log_change(self, vid: str, action: str, reason: str):
        if self._last_logged.get(vid) == action:
            return
        self._last_logged[vid] = action
        entry = {
            'time':      time.strftime('%H:%M:%S'),
            'agent':     vid,
            'action':    action,
            'reason':    reason,
            'ttc':       0,
            'timestamp': time.time(),
        }
        self.decisions.append(entry)
        if len(self.decisions) > 200:
            self.decisions.pop(0)
        logger.log_decision(vid, action, ttc=0, reason=reason)
    def reset(self):
        self.waiting_since.clear()
        self.decisions.clear()
        self._last_logged.clear()
        self._prev_crossing.clear()
    def get_decisions(self) -> List[dict]:
        return list(self.decisions)
def _explain_yield(candidate, active) -> str:
    if candidate.intent == 'left' and active.intent != 'left':
        return (f'viraj stanga cedeaza lui {active.id} '
                f'({active.intent} din {active.direction})')
    if RIGHT_OF.get(candidate.direction) == active.direction:
        return (f'prioritate dreapta: {active.id} vine din dreapta '
                f'({active.direction}), {candidate.direction} cedeaza')
    return f'conflict cu {active.id} ({active.direction})'
