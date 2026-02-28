import requests
import json
import logging
from concurrent.futures import ThreadPoolExecutor

# Configurare logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_client")

executor = ThreadPoolExecutor(max_workers=10) # Permite 10 masini sa "gandeasca" simultan

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:1b"  # Sau 3b, in functie de ce are utilizatorul

SYSTEM_PROMPT = """
You are an autonomous AI driving agent in a V2X environment.
Input: JSON describing your state (TTC, distance, traffic light, nearby vehicles).
Output: EXCLUSIVELY a JSON object:
{
  "action": "GO" | "BRAKE" | "YIELD",
  "reason": "A short natural explanation in Romanian."
}
Decision Logic:
1. If light is 'red', you MUST YIELD.
2. If an 'emergency' vehicle is approaching at low TTC, you MUST YIELD/BRAKE.
3. If road is clear and TTC is high, just GO.
4. Use the right-hand rule for V2V negotiation.
Respond ONLY with JSON.
"""

def get_llm_decision(vehicle_id: str, context: dict) -> dict:
    """
    Trimite contextul V2X catre Ollama si returneaza o decizie.
    """
    prompt = f"Vehicle ID: {vehicle_id}\nContext: {json.dumps(context)}\nWhat is your next action?"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "stream": False,
        "format": "json"
    }
    
    try:
        # Timeout mai relaxat pentru situatii cu multi agenti
        response = requests.post(OLLAMA_URL, json=payload, timeout=5.0)
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "{}")
            decision = json.loads(response_text)
            
            # Validare format
            if "action" in decision and "reason" in decision:
                return {
                    "action": decision["action"].upper(),
                    "reason": decision["reason"]
                }
    except Exception as e:
        logger.error(f"Ollama Error for {vehicle_id}: {e}")
    
    # Fallback in caz de eroare sau format invalid
    return {
        "action": "BRAKE",
        "reason": "Eroare comunicare AI — siguranță activată (braking)."
    }
