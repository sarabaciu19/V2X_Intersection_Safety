#!/bin/bash
# Porneste backend + frontend dintr-o singura comanda
# Rulare: bash start-fullstack.sh
ROOT="$(cd "$(dirname "$0")" && pwd)"
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
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
