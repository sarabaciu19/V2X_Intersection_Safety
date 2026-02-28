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
You are an autonomous AI driving agent in a V2X (Vehicle-to-Everything) environment. 
Your goal is to navigate an intersection safely and efficiently.
Input: You receive a JSON describing your current state and the state of nearby vehicles.
Output: You MUST respond EXCLUSIVELY with a JSON object in this format:
{
  "action": "GO" | "BRAKE" | "YIELD",
  "reason": "A short explanation in Romanian of your decision."
}
Rules:
- Emergency vehicles (priority='emergency') ALWAYS have priority.
- If TTC (Time To Collision) is < 1.5s, you must BRAKE or YIELD.
- Use the right-hand rule if no other priority applies.
- Respond ONLY with the JSON. No extra text.
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
        # Timeout mai mic pentru a nu bloca prea mult daca motorul e offline
        response = requests.post(OLLAMA_URL, json=payload, timeout=2.0)
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
        logger.error(f"Error calling Ollama: {e}")
    
    # Fallback in caz de eroare sau format invalid
    return {
        "action": "BRAKE",
        "reason": "Eroare comunicare AI — siguranță activată (braking)."
    }
