import requests
import json
import logging
import time as _time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional
from services.collision import TTC_BRAKE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_client")

OLLAMA_URL  = "http://localhost:11434/api/generate"
OLLAMA_PING = "http://localhost:11434/api/tags"
MODEL_NAME  = "llama3.2:1b"

executor = ThreadPoolExecutor(max_workers=4)

# ── Cache decizii LLM per vehicul (async) ─────────────────────────────
# Structura: { vid: {"action": str, "reason": str, "ts": float} }
_llm_cache: dict = {}
_pending:   dict = {}   # { vid: Future }
_CACHE_TTL  = 1.8       # secunde — reutilizeaza decizia LLM pana la urmatorul raspuns

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


# ── Prompturi ────────────────────────────────────────────────────────

# Prompt pentru decizia principala (GO/YIELD/BRAKE) — in engleza pt acuratete
SINGLE_SYSTEM = (
    'You are an autonomous V2X intersection agent. You perceive the environment through V2X radio messages '
    'from other vehicles and use your own memory of past decisions to make context-aware choices.\n'
    'Your goal: safely cross the intersection without collision. You must reason autonomously — '
    'do NOT blindly follow fixed rules. Consider speed, distance, priorities, and your recent behavior.\n\n'
    'Guidelines (not strict rules — use judgment):\n'
    '  - Emergency vehicles (ambulance, fire truck) should always be given priority\n'
    '  - Vehicles arriving much sooner (lower TTC) generally have practical priority\n'
    '  - Avoid oscillating: if you just yielded, do not immediately switch to GO unless situation changed\n'
    '  - Vehicles on the same road going opposite directions use separate lanes — no conflict\n'
    '  - If no conflict exists, GO\n\n'
    'Respond ONLY with JSON: {"action": "GO"|"YIELD"|"BRAKE", "reason": "scurt motiv in romana (max 8 cuvinte)"}\n'
)


def _get_single_decision(v: dict) -> tuple:
    """
    Apeleaza Ollama sincron pentru un singur vehicul.
    Returneaza (vid, {action, reason}) sau (vid, None) la eroare.
    Ruleaza in thread-pool — nu blocheaza simularea.
    """
    global _ollama_available
    vid     = v["id"]
    ms      = v.get("my_state", {})
    others  = v.get("others", [])
    memory  = v.get("memory", [])

    others_summary = ", ".join(
        f'{o["id"]}(ttc={o.get("ttc", 999):.1f}s, prio={o.get("priority","normal")}, dir={o.get("direction","?")})'
        for o in others
    ) or "none"

    # Rezumat memorie recenta — ajuta LLM-ul sa nu oscileze intre decizii
    memory_summary = ""
    if memory:
        mem_entries = memory[-3:]
        memory_summary = "My last decisions: " + "; ".join(
            f'{m.get("action","?")} ({m.get("reason","")[:25]})'
            for m in mem_entries
        ) + ".\n"

    prompt = (
        f"{SINGLE_SYSTEM}"
        f"\nVehicle {vid}:\n"
        f"  - TTC to intersection: {ms.get('ttc', 999):.1f}s\n"
        f"  - Priority: {ms.get('priority', 'normal')}\n"
        f"  - Direction: {ms.get('direction', '?')}, Intent: {ms.get('intent', 'straight')}\n"
        f"  - Speed: {ms.get('speed_kmh', 0)} km/h\n"
        f"  - Distance to intersection: {ms.get('dist_to_intersection', 999):.0f}px\n"
        f"Conflicting vehicles nearby: [{others_summary}].\n"
        f"{memory_summary}"
        f"Decision (JSON only):"
    )
    payload = {
        "model":   MODEL_NAME,
        "prompt":  prompt,
        "stream":  False,
        "format":  "json",
        "options": {"temperature": 0.0, "num_predict": 60},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=8.0)
        if response.status_code == 200:
            raw      = response.json().get("response", "{}")
            repaired = _repair_json(raw)
            data     = json.loads(repaired)
            action   = data.get("action", "GO").upper().strip()
            reason   = data.get("reason", "decizie AI").strip()
            if action not in ("GO", "YIELD", "BRAKE"):
                action = "GO"
            logger.info(f"[LLM] {vid}: {action} — {reason}")
            return vid, {"action": action, "reason": reason}
    except requests.exceptions.ConnectionError:
        _ollama_available = False
        logger.warning(f"Ollama conexiune esuata pentru {vid}")
    except requests.exceptions.Timeout:
        _ollama_available = False
        logger.warning(f"Ollama timeout pentru {vid}")
    except Exception as e:
        logger.warning(f"Ollama parse eroare pentru {vid}: {e}")
    return vid, None


def request_llm_decision(vid: str, context: dict) -> dict:
    """
    Interfata PRINCIPALA pentru Agent — returneaza decizia LLM pentru un vehicul.

    Functionare async cu cache:
    - Daca exista o decizie recenta in cache (<_CACHE_TTL sec) → o returneaza imediat
    - Trimite simultan o cerere noua catre Ollama in background (thread-pool)
    - Cat timp Ollama calculeaza, agentul foloseste cache-ul sau fallback-ul determinist
    - Cand raspunsul Ollama soseste, il stocheaza in cache

    context: { "my_state": {ttc, priority, direction, speed}, "others": [{id, ttc, priority}] }
    """
    global _ollama_available, _call_count

    now = _time.time()

    _call_count += 1
    if _call_count % _RECHECK_INTERVAL == 0:
        prev = _ollama_available
        _ollama_available = _check_ollama()
        if _ollama_available and not prev:
            logger.info("Ollama a revenit online — decizii LLM reactivate.")

    # Returneaza cache daca e proaspat
    cached = _llm_cache.get(vid)
    if cached and (now - cached.get("ts", 0)) < _CACHE_TTL:
        return cached

    # Fara Ollama → fallback imediat
    if not _ollama_available:
        return _deterministic_fallback(context)

    # Lanseaza cerere noua in background daca nu exista deja una in zbor
    fut = _pending.get(vid)
    if fut is None or fut.done():
        v_ctx = {"id": vid, **context}
        _pending[vid] = executor.submit(_get_single_decision, v_ctx)
        fut = _pending[vid]

    # Verifica daca cererea curenta e gata
    if fut.done():
        _, result = fut.result()
        _pending.pop(vid, None)
        if result:
            _llm_cache[vid] = {**result, "ts": now}
            return _llm_cache[vid]

    # Inca in asteptare → returneaza cache vechi sau fallback
    if cached:
        return cached
    return _deterministic_fallback(context)


def get_batch_decisions(vehicles_context: list) -> dict:
    """
    Decizii batch pentru toate vehiculele via LLM (async cu cache).
    Folosit de CentralSystem sau alte componente care lucreaza cu lista de vehicule.
    Pentru decizii per-vehicul din Agent, foloseste request_llm_decision().
    """
    result = {}
    for v in vehicles_context:
        vid     = v["id"]
        context = {k: val for k, val in v.items() if k != "id"}
        decision = request_llm_decision(vid, context)
        result[vid] = decision

    if result:
        logger.info(f"Decizii LLM batch: { {k: v['action'] for k, v in result.items()} }")
    return result


def get_llm_decision(vehicle_id: str, context: dict) -> dict:
    """Interfata per-vehicul (compatibilitate cu codul vechi)."""
    ctx     = {"id": vehicle_id, **context}
    results = get_batch_decisions([ctx])
    return results.get(vehicle_id, _deterministic_fallback(context))


def _deterministic_fallback(context: dict) -> dict:
    """
    Fallback determinist cand Ollama nu e disponibil.
    Replica logica din agent._evaluate() pentru consistenta.
    """
    my     = context.get("my_state", {})
    my_ttc = my.get("ttc", 999.0)
    others = context.get("others", [])

    if my.get("priority") == "emergency":
        return {"action": "GO", "reason": "urgență — prioritate absolută"}

    for o in others:
        other_ttc = o.get("ttc", 999.0)
        if other_ttc >= TTC_BRAKE * 2:
            continue
        if o.get("priority") == "emergency":
            return {"action": "YIELD", "reason": f"urgență {o.get('id')} — prioritate absolută"}
        if o.get("no_stop") and other_ttc < my_ttc:
            return {"action": "YIELD", "reason": f"{o.get('id')} nu se oprește — cedează"}
        if other_ttc < my_ttc - 0.5:
            return {"action": "YIELD", "reason": f"TTC mai mic: {o.get('id')} ajunge primul"}

    return {"action": "GO", "reason": "drum liber — niciun conflict"}
