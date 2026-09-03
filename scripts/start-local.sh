#!/bin/bash
# Order Supervisor - Local Development Environment Launcher (Bash / Git Bash / macOS / Linux)
# Launches Temporal Server, FastAPI Backend, Temporal Worker, and Next.js Frontend.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "======================================================"
echo "  Starting Order Supervisor Local Services (In-Terminal)"
echo "======================================================"

# Activate virtual environment (handles both Windows Git Bash and Linux/macOS)
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
    TEMPORAL_CMD="./.venv/Scripts/temporal.exe"
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    TEMPORAL_CMD="temporal"
else
    echo "Virtual environment not found. Please create one with: python -m venv .venv"
    exit 1
fi

# 1. Temporal Server
$TEMPORAL_CMD server start-dev --port 7233 --ui-port 8233 --ip 127.0.0.1 &
TEMPORAL_PID=$!

sleep 2

# 2. FastAPI Backend
uvicorn apps.api.app.main:app --port 8000 --host 127.0.0.1 --reload &
API_PID=$!

# 3. Temporal Worker
python -m temporal.worker &
WORKER_PID=$!

# 4. Next.js Frontend
cd apps/web && npm run dev &
WEB_PID=$!

echo ""
echo "All 4 services running in this terminal session!"
echo "  - Frontend UI:   http://localhost:3000"
echo "  - Backend API:   http://127.0.0.1:8000/docs"
echo "  - Temporal UI:   http://localhost:8233"
echo ""
echo "Press Ctrl+C in this terminal to stop all services."

cleanup() {
    echo ""
    echo "Shutting down all services..."
    kill $TEMPORAL_PID $API_PID $WORKER_PID $WEB_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT
wait
