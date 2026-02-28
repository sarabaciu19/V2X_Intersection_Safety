"""
services/llm_client.py — Client optional Ollama LLM
Daca requests nu este instalat sau Ollama nu ruleaza,
returneaza intotdeauna fallback-ul determinist (BRAKE).
"""
import json
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("llm_client")
executor = ThreadPoolExecutor(max_workers=4)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:1b"

SYSTEM_PROMPT = """
You are an autonomous AI driving agent in a V2X environment.
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
Respond ONLY with JSON: {"action": "GO"|"BRAKE"|"YIELD", "reason": "..."
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
=======
>>>>>>> 07d2302322b2f0cd6fe91251e994771a3d18f8d2
>>>>>>> Stashed changes
"""

_FALLBACK = {"action": "BRAKE", "reason": "Ollama indisponibil — fallback determinist."}


def get_llm_decision(vehicle_id: str, context: dict) -> dict:
    """Apeleaza Ollama; returneaza fallback daca nu e disponibil."""
    try:
        import requests as _req
    except ImportError:
        return _FALLBACK

    prompt = f"Vehicle: {vehicle_id}\nContext: {json.dumps(context)}\nAction?"
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "stream": False,
        "format": "json",
    }
    try:
<<<<<<< Updated upstream
        # Timeout mai relaxat pentru situatii cu multi agenti
        response = requests.post(OLLAMA_URL, json=payload, timeout=5.0)
=======
<<<<<<< HEAD
        response = _req.post(OLLAMA_URL, json=payload, timeout=1.5)
=======
        # Timeout mai relaxat pentru situatii cu multi agenti
        response = requests.post(OLLAMA_URL, json=payload, timeout=5.0)
>>>>>>> 07d2302322b2f0cd6fe91251e994771a3d18f8d2
>>>>>>> Stashed changes
        if response.status_code == 200:
            decision = json.loads(response.json().get("response", "{}"))
            if "action" in decision and "reason" in decision:
                return {"action": decision["action"].upper(), "reason": decision["reason"]}
    except Exception as e:
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
        logger.debug(f"Ollama unavailable for {vehicle_id}: {e}")

    return _FALLBACK
=======
>>>>>>> Stashed changes
        logger.error(f"Ollama Error for {vehicle_id}: {e}")
    
    # Fallback in caz de eroare sau format invalid
    return {
        "action": "BRAKE",
        "reason": "Eroare comunicare AI — siguranță activată (braking)."
    }
>>>>>>> 07d2302322b2f0cd6fe91251e994771a3d18f8d2
