# Order Supervisor - Setup and Run Instructions

---

## 1. First-Time Installation (Run Once After Cloning)

When you clone the repository for the first time, follow these steps to set up the Python environment, install all dependencies, and seed the initial database.

Open PowerShell or your terminal in the cloned repository root folder:

### Step 1: Create and Activate Python Virtual Environment
**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux / Git Bash:**
```bash
python -m venv .venv
source .venv/bin/activate
```

> **Note for Windows users**: If PowerShell shows an execution policy error, run:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Install Frontend Dependencies
```bash
cd apps/web
npm install
cd ../..
```

### Step 4: Seed the Database & Demo Order
This initializes the database schema, default supervisor templates, and a pre-configured demo test order (`ORD-1001`):
```bash
python database/seed.py
```

---

## 2. Running the Application

You can run the full stack using the automated script or across individual terminals.

### Option A: Automated 1-Click Launcher (Recommended)

**Windows PowerShell:**
```powershell
.\scripts\start-local.ps1
```

**macOS / Linux / Git Bash:**
```bash
bash scripts/start-local.sh
```

This single command starts:
1. Temporal Dev Server (`http://localhost:8233`, gRPC: `7233`)
2. FastAPI Backend (`http://localhost:8000/docs`)
3. Temporal Worker (processes workflow activities and agent decisions)
4. Next.js Frontend (`http://localhost:3000`)

Press `Ctrl+C` in that terminal to stop all running services.

---

### Option B: Manual Multi-Terminal Launch

If you prefer running each service in its own terminal tab:

#### Terminal 1: Temporal Server
Using Docker:
```bash
docker-compose up -d
```
*Or using the local Temporal CLI binary:*
```powershell
temporal server start-dev --port 7233 --ui-port 8233 --ip 127.0.0.1
```
*Web Console: http://localhost:8233*

#### Terminal 2: FastAPI Backend Server
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn apps.api.app.main:app --port 8000 --host 127.0.0.1 --reload
```
*Swagger API Docs: http://127.0.0.1:8000/docs*

#### Terminal 3: Temporal Worker
```powershell
.\.venv\Scripts\Activate.ps1
python -m temporal.worker
```
*Listens for workflow tasks on queue `order-supervisor-task-queue`.*

#### Terminal 4: Next.js Frontend
```powershell
cd apps/web
npm run dev
```
*Web Dashboard: http://localhost:3000*

---

## 3. Demo Order & Verification

1. Open `http://localhost:3000` in your browser.
2. Visit `http://localhost:3000/runs/run_demo_1001` to view the seeded test order (`ORD-1001`, Sarah Connor).
3. Use the **Event Generator & Simulator** panel on the right to inject events (e.g. `payment_confirmed`, `shipment_delayed`, `delivered`).
4. Type live instructions (e.g. *"Prioritize speed over cost"*) in the **Dynamic Operator Directives** box and click Apply.

---

## 4. Running Tests

To run the full automated test suite (32 tests):
```powershell
.\.venv\Scripts\Activate.ps1
pytest tests
```

To run individual test suites:
```powershell
pytest tests/unit/test_assignment_compliance.py -v   # Event & tool compliance
pytest tests/workflows/test_order_supervisor.py -v     # Temporal workflow tests
pytest tests/api/test_schemathesis.py -v              # API fuzz tests
```

---

## 5. Database Reset

To reset the database back to clean seeded defaults:
```powershell
python scripts/reset-db.py
```
