import requests
import json
import logging
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_client")

OLLAMA_URL  = "http://localhost:11434/api/generate"
OLLAMA_PING = "http://localhost:11434/api/tags"
MODEL_NAME  = "llama3.2:1b"

executor = ThreadPoolExecutor(max_workers=2)

# ── Disponibilitate Ollama ─────────────────────────────────────────────
_ollama_available: bool = False
_call_count = 0
_RECHECK_INTERVAL = 30   # re-verifica disponibilitatea la fiecare 30 tick-uri

def _check_ollama() -> bool:
    try:
        r = requests.get(OLLAMA_PING, timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False

_ollama_available = _check_ollama()
if _ollama_available:
    logger.info(f"Ollama disponibil — decizii AI activate ({MODEL_NAME}).")
else:
    logger.warning("Ollama indisponibil — se foloseste logica determinista.")


def _repair_json(raw: str) -> str:
    """Repara JSON trunchiat returnat de Ollama (num_predict prea mic)."""
    raw = raw.strip()
    if not raw:
        return "{}"
    try:
        json.loads(raw)
        return raw
    except Exception:
        pass
    # Cauta primul bloc { ... } complet
    try:
        start = raw.index('{')
        depth = 0
        for i, ch in enumerate(raw[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    candidate = raw[start:i+1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except Exception:
                        break
    except ValueError:
        pass
    # Inchide JSON trunchiat
    patched = raw
    open_braces  = patched.count('{') - patched.count('}')
    open_strings = patched.count('"') % 2
    if open_strings:
        patched += '"'
    patched += '}' * max(open_braces, 0)
    try:
        json.loads(patched)
        return patched
    except Exception:
        return "{}"


# ── Prompt per vehicul ────────────────────────────────────────────────

REASON_PROMPT = (
    'Esti un sistem V2X. Explica pe scurt IN ROMANA (max 8 cuvinte) decizia unui vehicul la intersectie.\n'
    'Raspunde DOAR cu JSON: {"reason":"explicatie scurta in romana"}\n'
)


def _get_ai_reason(vid: str, action: str, my_ttc: float, others_summary: str) -> str:
    """Foloseste Ollama DOAR pentru a genera o explicatie in romana. Decizia e determinista."""
    prompt = (
        f'{REASON_PROMPT}'
        f'Vehicul {vid} decide {action}. TTC={my_ttc:.1f}s. Conflicte: [{others_summary if others_summary else "niciunul"}].\n'
        f'JSON:'
    )
    payload = {
        "model":   MODEL_NAME,
        "prompt":  prompt,
        "stream":  False,
        "format":  "json",
        "options": {"temperature": 0.3, "num_predict": 40},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=6.0)
        if response.status_code == 200:
            raw      = response.json().get("response", "{}")
            repaired = _repair_json(raw)
            data     = json.loads(repaired)
            reason   = data.get("reason", "").strip()
            if reason and len(reason) > 3:
                return reason
    except requests.exceptions.ConnectionError:
        global _ollama_available
        _ollama_available = False
    except requests.exceptions.Timeout:
        global _ollama_available
        _ollama_available = False
    except Exception:
        pass
    return ""


def _get_single_decision(v: dict) -> tuple:
    """Apeleaza Ollama pentru un singur vehicul. Returneaza (vid, decizie|None)."""
    global _ollama_available
    vid = v["id"]
    ms  = v.get("my_state", {})
    others_summary = ", ".join(
        f'{o["id"]}(ttc={o.get("ttc", 999):.1f},prio={o.get("priority","normal")})'
        for o in v.get("others", [])
    )
    prompt = (
        f'{SINGLE_SYSTEM}'
        f'My id={vid}, my ttc={ms.get("ttc", 999):.1f}s, priority={ms.get("priority","normal")}.\n'
        f'Nearby vehicles: [{others_summary if others_summary else "none"}].\n'
        f'{"YIELD because emergency vehicle nearby." if any(o.get("priority")=="emergency" for o in v.get("others",[])) else ""}'
        f'{"YIELD because my ttc is higher." if any(o.get("ttc",999) < ms.get("ttc",999)-0.3 for o in v.get("others",[])) else ""}'
        f'JSON:'
    )
    payload = {
        "model":   MODEL_NAME,
        "prompt":  prompt,
        "stream":  False,
        "format":  "json",
        "options": {"temperature": 0.0, "num_predict": 80},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=8.0)
        if response.status_code == 200:
            raw      = response.json().get("response", "{}")
            repaired = _repair_json(raw)
            data     = json.loads(repaired)
            action   = data.get("action", "GO").upper().strip()
            reason   = data.get("reason", "decizie AI")
            if action not in ("GO", "YIELD"):
                action = "GO"
            logger.debug(f"Ollama {vid}: {action} — {reason}")
            return vid, {"action": action, "reason": reason}
    except requests.exceptions.ConnectionError:
        _ollama_available = False
        logger.warning(f"Ollama conexiune esuata pentru {vid}")
    except requests.exceptions.Timeout:
        _ollama_available = False
        logger.warning(f"Ollama timeout pentru {vid}")
    except Exception as e:
        # Eroare de parsare — NU dezactivam Ollama, doar folosim fallback pt acest vehicul
        logger.warning(f"Ollama parse eroare pentru {vid}: {e}")
    return vid, None


def get_batch_decisions(vehicles_context: list) -> dict:
    """
    Decizii pentru toate vehiculele:
    - Actiunea (GO/YIELD) e determinata DETERMINIST (corect 100%)
    - Motivul e generat de Ollama in romana (daca disponibil)
    - Semaforul e gestionat de vehicle.update() + CentralSystem, NU aici
    """
    global _ollama_available, _call_count
    _call_count += 1

    if _call_count % _RECHECK_INTERVAL == 0:
        prev = _ollama_available
        _ollama_available = _check_ollama()
        if _ollama_available and not prev:
            logger.info("Ollama a revenit online.")

    result = {}
    for v in vehicles_context:
        vid     = v["id"]
        ms      = v.get("my_state", {})
        others  = v.get("others", [])
        prio    = ms.get("priority", "normal")
        my_ttc  = ms.get("ttc", 999.0)

        # ── Decizie determinista (actiunea corecta garantata) ───────────
        has_emerg_other = any(o.get("priority") == "emergency" for o in others)

        if prio == "emergency":
            action       = "GO"
            default_reason = "urgenta — prioritate absoluta"
        elif has_emerg_other:
            action       = "YIELD"
            emerg_id     = next(o["id"] for o in others if o.get("priority") == "emergency")
            default_reason = f"urgenta {emerg_id} are prioritate"
        else:
            # Regula TTC: vehiculul cu TTC mai mare cedeaza
            conflict = next(
                (o for o in others if o.get("ttc", 999) < my_ttc - 0.3),
                None
            )
            if conflict:
                action         = "YIELD"
                default_reason = f"conflict cu {conflict['id']}, TTC mai mic"
            else:
                action         = "GO"
                default_reason = "drum liber"

        # ── Motiv generat de Ollama in romana (optional) ─────────────────
        if _ollama_available:
            others_summary = ", ".join(
                f'{o["id"]}(ttc={o.get("ttc",999):.1f})'
                for o in others
            )
            ai_reason = _get_ai_reason(vid, action, my_ttc, others_summary)
            reason = ai_reason if ai_reason else default_reason
        else:
            reason = default_reason

        result[vid] = {"action": action, "reason": reason}

    if result:
        logger.info(f"Decizii V2X: { {k: v['action'] for k, v in result.items()} }")
    return result


def get_llm_decision(vehicle_id: str, context: dict) -> dict:
    """Interfata per-vehicul (compatibilitate cu codul vechi)."""
    ctx     = {"id": vehicle_id, **context}
    results = get_batch_decisions([ctx])
    return results.get(vehicle_id, _deterministic_fallback(context))


def _deterministic_fallback(context: dict) -> dict:
    """
    Fallback determinist cand Ollama nu e disponibil.
    Decide DOAR pe baza conflictelor V2V si urgentei — NU pe baza semaforului.
    """
    my     = context.get("my_state", {})
    my_ttc = my.get("ttc", 999.0)
    others = context.get("others", [])

    if my.get("priority") == "emergency":
        return {"action": "GO", "reason": "urgenta — prioritate absoluta"}
    for o in others:
        if o.get("priority") == "emergency":
            return {"action": "YIELD", "reason": f"urgenta {o.get('id')} are prioritate"}
        if o.get("ttc", 999) < my_ttc - 0.5:
            return {"action": "YIELD", "reason": f"conflict cu {o.get('id')}, TTC mai mic"}
    return {"action": "GO", "reason": "drum liber"}
