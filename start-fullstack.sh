#!/bin/bash

# 🚀 Start V2X Intersection Safety - FULL STACK (Frontend + Backend)

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🚗 V2X Intersection Safety - Full Stack Start             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "📋 Verificare Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nu e instalat!"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1)
echo "✅ $PYTHON_VERSION"

# Check Node
echo "📋 Verificare Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js nu e instalat!"
    exit 1
fi
NODE_VERSION=$(node --version)
echo "✅ Node.js $NODE_VERSION"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  OPȚIUNI:                                                  ║"
echo "║  1) Backend Only        python main.py                    ║"
echo "║  2) Frontend Only       cd frontend && npm run dev        ║"
echo "║  3) Full Stack (Ctrl+C  să oprești)                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

read -p "Alege opțiune (1/2/3): " OPTION

case $OPTION in
  1)
    echo ""
    echo "🚀 PORNIRE BACKEND..."
    echo ""
    pip install -q fastapi uvicorn websockets pydantic 2>/dev/null
    python main.py
    ;;
  2)
    echo ""
    echo "🚀 PORNIRE FRONTEND..."
    echo ""
    cd frontend
    npm install --silent 2>/dev/null
    npm run dev
    ;;
  3)
    echo ""
    echo "🚀 PORNIRE FULL STACK (Frontend + Backend)..."
    echo ""

    # Install backend dependencies silently
    echo "📦 Instalare dependențe Python..."
    pip install -q fastapi uvicorn websockets pydantic 2>/dev/null
    echo "✅ Done"

    # Install frontend dependencies silently
    echo "📦 Instalare dependențe Frontend..."
    cd frontend
    npm install --silent 2>/dev/null
    cd ..
    echo "✅ Done"

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  STARTING BOTH SERVERS...                                  ║"
    echo "║                                                            ║"
    echo "║  Backend:  http://localhost:8000                          ║"
    echo "║  Frontend: http://localhost:3000                          ║"
    echo "║                                                            ║"
    echo "║  Apasă Ctrl+C pentru a opri                              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # Start backend in background
    python main.py &
    BACKEND_PID=$!

    sleep 2

    # Start frontend in background
    cd frontend && npm run dev &
    FRONTEND_PID=$!

    # Wait for both processes
    wait
    ;;
  *)
    echo "❌ Opțiune invalida!"
    exit 1
    ;;
esac

