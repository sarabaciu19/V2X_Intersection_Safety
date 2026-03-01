import sys
sys.path.insert(0, r'C:\Facultate\ANUL2\V2X_Intersection_Safety')

from simulation.engine import engine

print("=== INITIAL STATE ===")
for v in engine.vehicles:
    print(f"  {v.id}: dir={v.direction} speed={v.speed_multiplier*50:.0f}km/h no_stop={v.no_stop} pos=({v.x:.0f},{v.y:.0f})")
print(f"  has_semaphore={engine.central._has_semaphore}")
print()

A_was_waiting = False
B_was_waiting = False

for tick in range(1, 200):
    engine._tick()
    a = next((v for v in engine.vehicles if v.id == 'A'), None)
    b = next((v for v in engine.vehicles if v.id == 'B'), None)
    if not a or not b:
        break
    if a.state == 'waiting':
        A_was_waiting = True
    if b.state == 'waiting':
        B_was_waiting = True
    if tick % 20 == 0 or a.state == 'waiting' or b.state == 'waiting':
        print(f"t={tick:3d}  A: {a.state:8s} ({a.x:.0f},{a.y:.0f}) vx={a.vx:.1f} vy={a.vy:.1f} | B: {b.state:8s} ({b.x:.0f},{b.y:.0f}) vx={b.vx:.1f} vy={b.vy:.1f}")

print()
print(f"A ever waited: {A_was_waiting}  (should be False)")
print(f"B ever waited: {B_was_waiting}  (should be True)")
print()
print("=== DECISIONS ===")
for d in engine.central.get_decisions():
    print(f"  [{d['action']:22s}] {d['agent']}: {d['reason'][:100]}")

