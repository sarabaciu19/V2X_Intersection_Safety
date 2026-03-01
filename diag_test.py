import requests
import time
import json

BASE_URL = "http://localhost:8000"

def check():
    print("--- Diagnostic Check (take 2) ---")
    
    # 1. Reset specifically to no_v2x
    print("Resetting to no_v2x...")
    requests.post(f"{BASE_URL}/reset", json={"scenario": "no_v2x"})
    requests.post(f"{BASE_URL}/start")
    
    time.sleep(2)
    
    # Check initial state
    s1 = requests.get(f"{BASE_URL}/state").json()
    print(f"Tick at 2s: {s1.get('tick')}")
    print(f"Vehicles: {[v['id'] for v in s1.get('vehicles', [])]}")
    
    # Wait for collision and removal (should happen around 5-10s)
    print("Waiting 10 seconds...")
    time.sleep(10)
    
    s2 = requests.get(f"{BASE_URL}/state").json()
    print(f"Tick at 12s: {s2.get('tick')}")
    vehicles = s2.get('vehicles', [])
    print(f"Vehicles: {[v['id'] for v in vehicles]}")
    states = {v['id']: v['state'] for v in vehicles}
    print(f"States: {states}")
    
    # If the simulation reloaded, tick will be small.
    # If removal worked but not all are done, tick will be large.
    if s2.get('tick') < s1.get('tick'):
        print("SUCCESS: Simulation reloaded (all vehicles done)!")
    elif 'done' in states.values():
        print("SUCCESS: Vehicles found in 'done' state (removal logic triggered)!")
    elif 'crashed' in states.values():
        print("Wait: Vehicles still in 'crashed' state. Timeout might be too long or tick too slow.")
    else:
        print("Check vehicle positions - they might still be moving or done.")

if __name__ == "__main__":
    try:
        check()
    except Exception as e:
        print(f"Error: {e}")
