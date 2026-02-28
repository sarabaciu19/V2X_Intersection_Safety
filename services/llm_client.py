import requests
import json
import logging
import time as _time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional

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
    'You are a V2X intersection safety agent. Decide what a vehicle should do.\n'
    'Rules (in priority order):\n'
    '  1. If any other vehicle has EMERGENCY priority → YIELD\n'
    '  2. If another vehicle comes from the OPPOSITE direction on the SAME road\n'
    '     (N<->S on vertical road, or E<->V on horizontal road) → NO PATH CONFLICT.\n'
    '     Both vehicles use separate parallel lanes and can cross simultaneously → GO.\n'
    '  3. If your TTC is significantly higher than a CONFLICTING vehicle (>0.3s diff) → YIELD\n'
    '  4. If your TTC is lower than all conflicting vehicles → GO\n'
    '  5. If no conflict → GO\n'
    'Respond ONLY with JSON: {"action": "GO"|"YIELD"|"BRAKE", "reason": "short reason in Romanian (max 8 words)"}\n'
)

# Prompt pentru explicatie text (motiv in romana)
REASON_PROMPT = (
    'Esti un sistem V2X. Explica pe scurt IN ROMANA (max 8 cuvinte) decizia unui vehicul la intersectie.\n'
    'Raspunde DOAR cu JSON: {"reason":"explicatie scurta in romana"}\n'
)


def _get_ai_reason(vid: str, action: str, my_ttc: float, others_summary: str) -> str:
    """Foloseste Ollama DOAR pentru a genera o explicatie in romana."""
    global _ollama_available
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
        _ollama_available = False
    except requests.exceptions.Timeout:
        _ollama_available = False
    except Exception:
        pass
    return ""


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

    others_summary = ", ".join(
        f'{o["id"]}(ttc={o.get("ttc", 999):.1f}s, prio={o.get("priority","normal")})'
        for o in others
    ) or "none"

    has_emergency = any(o.get("priority") == "emergency" for o in others)
    my_ttc        = ms.get("ttc", 999.0)
    ttc_conflict  = any(o.get("ttc", 999) < my_ttc - 0.3 for o in others)

    hint = ""
    if has_emergency:
        hint = "Emergency vehicle nearby — rule 1 applies.\n"
    elif ttc_conflict:
        hint = "Your TTC is higher — you should yield (rule 2).\n"

    prompt = (
        f"{SINGLE_SYSTEM}"
        f"Vehicle {vid}: ttc={my_ttc:.1f}s, priority={ms.get('priority','normal')}, "
        f"direction={ms.get('direction','?')}, speed={ms.get('speed',0):.1f}px/tick.\n"
        f"Nearby: [{others_summary}].\n"
        f"{hint}"
        f"JSON:"
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
