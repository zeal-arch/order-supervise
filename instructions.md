# Order Supervisor - Setup and Run Instructions

---

## The Golden Rule: Working Directory

Every single command must be run from the **`order-supervisor` root directory**.

Before running any command, make sure your terminal shows:
```powershell
PS D:\projects\sagapilot\order-supervisor>
```

If you are currently inside `.venv` or any subfolder, jump back to root:
```powershell
cd D:\projects\sagapilot\order-supervisor
```

---

## Quick Start (Automated 1-Click)

The simplest way to run all 4 services inside your VS Code terminal (no external windows):

### In Windows PowerShell:
```powershell
.\scripts\start-local.ps1
```

### In Git Bash / Linux / macOS:
```bash
bash scripts/start-local.sh
```

*This starts Temporal Server, FastAPI Backend, Temporal Worker, and Next.js Frontend in the background. Press `Ctrl+C` in that terminal at any time to stop all services.*

---

## Manual Step-by-Step Guide (If Running in 4 Separate Terminals)

If you prefer running each service in its own terminal tab, open 4 terminal tabs in **`D:\projects\sagapilot\order-supervisor`**:

### Terminal 1: Temporal Server
```powershell
# 1. Ensure you are at root:
cd D:\projects\sagapilot\order-supervisor

# 2. Start Temporal:
.\.venv\Scripts\temporal.exe server start-dev --port 7233 --ui-port 8233 --ip 127.0.0.1
```
*Web Console: http://localhost:8233*

---

### Terminal 2: FastAPI Backend Server
```powershell
# 1. Ensure you are at root:
cd D:\projects\sagapilot\order-supervisor

# 2. Activate environment:
.\.venv\Scripts\Activate.ps1

# 3. Start Backend:
uvicorn apps.api.app.main:app --port 8000 --host 127.0.0.1 --reload
```
*Swagger API Docs: http://127.0.0.1:8000/docs*

---

### Terminal 3: Temporal Worker
```powershell
# 1. Ensure you are at root:
cd D:\projects\sagapilot\order-supervisor

# 2. Activate environment:
.\.venv\Scripts\Activate.ps1

# 3. Start Worker:
python -m temporal.worker
```
*Listens for workflow execution tasks on queue `order-supervisor-task-queue`.*

---

### Terminal 4: Next.js Frontend Web UI
```powershell
# 1. Navigate to apps/web:
cd D:\projects\sagapilot\order-supervisor\apps\web

# 2. Start Frontend:
npm run dev
```
*Frontend Application: http://localhost:3000*

---

## How to Reset the Database to a Clean Slate (0 Orders)
```powershell
cd D:\projects\sagapilot\order-supervisor
.\.venv\Scripts\python.exe scripts/reset-db.py
```
*This wipes all previous test runs and initializes fresh supervisor templates with 0 demo orders.*

---

## Common Mistakes and How to Avoid Them

| Error | Why It Happened | Solution |
| :--- | :--- | :--- |
| `can't open file ... No such file or directory` | Your terminal is inside `.venv` or a subfolder. | Type `cd D:\projects\sagapilot\order-supervisor` first. |
| `The term 'temporal.exe' is not recognized` | Path is wrong because you are not in the root directory. | Type `cd D:\projects\sagapilot\order-supervisor` first. |
| `No module named 'apps'` | Running from `.venv/Scripts` instead of the project root. | Always run from `order-supervisor/`. |
| `No module named 'sqlalchemy'` | Running without activating the virtual environment. | Run `.\.venv\Scripts\Activate.ps1` before running `python` or `uvicorn`. |
