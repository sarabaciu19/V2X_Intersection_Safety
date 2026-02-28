#!/bin/bash
# Porneste backend + frontend dintr-o singura comanda
# Rulare: bash start-fullstack.sh
ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Porneste Ollama server daca nu ruleaza deja ───────────────────────
echo "=== Checking Ollama (port 11434) ==="
if ! curl -s --max-time 1 http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  Ollama nu ruleaza — il pornesc..."
    ollama serve > /tmp/ollama_serve.log 2>&1 &
    OLLAMA_PID=$!
    sleep 2
    if curl -s --max-time 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "  Ollama pornit (PID $OLLAMA_PID) — model: llama3.2:1b"
    else
        echo "  ATENTIE: Ollama nu a pornit — se va folosi logica determinista"
        OLLAMA_PID=""
    fi
else
    echo "  Ollama deja ruleaza."
    OLLAMA_PID=""
fi

echo "=== Starting Backend (port 8000) ==="
cd "$ROOT"
uvicorn api.server:app --reload --port 8000 &
BACKEND_PID=$!
echo "=== Starting Frontend (port 5173) ==="
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
echo ""
echo "  Backend  → http://localhost:8000"
echo "  Frontend → http://localhost:5173"
echo ""
echo "  Press Ctrl+C to stop both."
trap "kill $BACKEND_PID $FRONTEND_PID $OLLAMA_PID 2>/dev/null; exit" INT
wait
