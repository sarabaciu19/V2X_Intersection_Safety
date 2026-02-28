"""
services/collision.py — TTC si detectia riscului de coliziune
TTC = distanta pana la intersectie / viteza proprie
Daca TTC_A < 3s si TTC_B < 3s → risc de coliziune
Returneaza: { 'risk': bool, 'ttc': float, 'action': 'go'/'brake'/'yield', 'pair': ... }
Regula prioritatii: vehiculul din dreapta are prioritate.
"""
import math
from typing import Dict
INTERSECTION = (400, 400)   # centrul intersectiei in pixeli
TTC_BRAKE = 3.0             # secunde → frana
TTC_YIELD = 1.5             # secunde → stop complet
COLLISION_DIST = 20         # pixeli → coliziune fizica
def time_to_intersection(v: dict) -> float:
    """TTC al unui vehicul fata de centrul intersectiei."""
    dx = INTERSECTION[0] - v["x"]
    dy = INTERSECTION[1] - v["y"]
    dist = math.sqrt(dx ** 2 + dy ** 2)
    speed = math.sqrt(v["vx"] ** 2 + v["vy"] ** 2)
    return dist / speed if speed > 0 else 999.0
def is_right_of(v1: dict, v2: dict) -> bool:
    """True daca v2 vine din dreapta lui v1 (regula prioritatii)."""
    def norm(v):
        s = math.sqrt(v["vx"] ** 2 + v["vy"] ** 2)
        return (v["vx"] / s, v["vy"] / s) if s > 0 else (0, 0)
    d1 = norm(v1)
    d2 = norm(v2)
    cross = d1[0] * d2[1] - d1[1] * d2[0]
    return cross > 0
def assess_risk(vehicles: Dict[str, dict]) -> dict:
    """
    Evalueaza riscul pentru toate perechile.
    Returneaza: { risk, ttc, action, pair, ttc_per_vehicle }
    """
    ids = list(vehicles.keys())
    ttc_map = {vid: time_to_intersection(vehicles[vid]) for vid in ids}
    result = {
        "risk": False,
        "ttc": 999.0,
        "action": "go",
        "pair": None,
        "ttc_per_vehicle": ttc_map,
    }
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            id1, id2 = ids[i], ids[j]
            v1, v2 = vehicles[id1], vehicles[id2]
            t1, t2 = ttc_map[id1], ttc_map[id2]
            if t1 < TTC_BRAKE and t2 < TTC_BRAKE:
                min_ttc = min(t1, t2)
                result["risk"] = True
                result["ttc"] = round(min_ttc, 3)
                result["pair"] = (id1, id2)
                if v1.get("priority") == "emergency" or v2.get("priority") == "emergency":
                    result["action"] = "yield"
                elif min_ttc < TTC_YIELD:
                    result["action"] = "yield"
                else:
                    result["action"] = "brake"
    return result
def check_physical_collision(vehicles: Dict[str, dict]) -> list:
    """Detecteaza coliziuni fizice (distanta < COLLISION_DIST). Returneaza perechi."""
    ids = list(vehicles.keys())
    collisions = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            v1, v2 = vehicles[ids[i]], vehicles[ids[j]]
            dist = math.sqrt((v1["x"] - v2["x"]) ** 2 + (v1["y"] - v2["y"]) ** 2)
            if dist < COLLISION_DIST:
                collisions.append((ids[i], ids[j]))
    return collisions
