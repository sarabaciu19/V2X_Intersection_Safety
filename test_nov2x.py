import sys
sys.path.insert(0, r'C:\Facultate\ANUL2\V2X_Intersection_Safety')
from simulation.engine import engine

engine.reset('no_v2x')
print('Vehicles:')
for v in engine.vehicles:
    print(f'  {v.id}: spd={v.speed_multiplier*50:.0f}km/h no_stop={v.no_stop} v2x={v.v2x_enabled}')
print('has_semaphore:', engine.central._has_semaphore)
print()

collision_tick = None
for i in range(1, 250):
    engine._tick()
    a = next((v for v in engine.vehicles if v.id == 'A'), None)
    b = next((v for v in engine.vehicles if v.id == 'B'), None)
    if not a or not b:
        break
    if engine._active_collisions and collision_tick is None:
        collision_tick = i
        print(f'COLIZIUNE la tick={i}!')
        print(f'  A: state={a.state} pos=({a.x:.0f},{a.y:.0f})')
        print(f'  B: state={b.state} pos=({b.x:.0f},{b.y:.0f})')
        break
    if i % 25 == 0:
        print(f't={i:3d}  A:{a.state:8s}({a.x:.0f},{a.y:.0f}) B:{b.state:8s}({b.x:.0f},{b.y:.0f})')

if collision_tick is None:
    print('EROARE: fara coliziune!')
    for v in engine.vehicles:
        print(f'  {v.id}: state={v.state} pos=({v.x:.0f},{v.y:.0f})')

