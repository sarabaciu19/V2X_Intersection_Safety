from simulation.engine import engine
from utils import logger

engine.reset('perpendicular')
stops = {}
for i in range(350):
    engine._tick()
    for v in engine.vehicles:
        if v.state == 'waiting' and v.id not in stops:
            stops[v.id] = i
        if v.state == 'crossing' and v.id in stops:
            tick_s = stops.pop(v.id)
            print(f"  {v.id}: stopped={tick_s} -> crossing={i}  pos=({v.x:.0f},{v.y:.0f})")

log = logger.get_all()
print(f"Log entries: {len(log)}")
for e in log:
    reason = e["reason"].encode("ascii", "replace").decode()[:55]
    print(f"  {e['agent']:4s} {e['action']:14s} {reason}")

