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
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found. Please create one with: python -m venv .venv"
    exit 1
fi

# Detect or install Temporal CLI
TEMPORAL_CMD=""
if [ -f ".venv/Scripts/temporal.exe" ]; then
    TEMPORAL_CMD="./.venv/Scripts/temporal.exe"
elif [ -f ".venv/bin/temporal" ]; then
    TEMPORAL_CMD="./.venv/bin/temporal"
elif command -v temporal >/dev/null 2>&1; then
    TEMPORAL_CMD="temporal"
else
    echo "Temporal CLI not found. Downloading standalone Temporal CLI..."
    curl -sSf https://temporal.download/cli.sh | sh
    if [ -f "$HOME/.temporalio/bin/temporal" ]; then
        TEMPORAL_CMD="$HOME/.temporalio/bin/temporal"
    elif [ -f "./.temporalio/bin/temporal" ]; then
        TEMPORAL_CMD="./.temporalio/bin/temporal"
    else
        TEMPORAL_CMD="temporal"
    fi
fi

# 1. Temporal Server
echo "[1/4] Starting Temporal Server on port 7233..."
$TEMPORAL_CMD server start-dev --port 7233 --ui-port 8233 --ip 127.0.0.1 &
TEMPORAL_PID=$!

# Wait for Temporal Server port to open
for i in {1..30}; do
    if nc -z 127.0.0.1 7233 2>/dev/null || curl -s http://127.0.0.1:8233 >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

# 2. FastAPI Backend
echo "[2/4] Starting FastAPI Backend on http://127.0.0.1:8000..."
uvicorn apps.api.app.main:app --port 8000 --host 127.0.0.1 --reload &
API_PID=$!

# 3. Temporal Worker
echo "[3/4] Starting Temporal Worker..."
python -m temporal.worker &
WORKER_PID=$!

# 4. Next.js Frontend
echo "[4/4] Starting Next.js Web UI on http://localhost:3000..."
(cd apps/web && npm run dev) &
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
