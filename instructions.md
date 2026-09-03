# Order Supervisor - Setup and Run Instructions

---

## 1. First-Time Installation (Run Once After Cloning)

When you clone the repository for the first time, follow these steps to set up the Python environment, install all dependencies, and seed the initial database.

Open PowerShell or your terminal in the cloned repository root folder:

### Step 1: Create and Activate Python Virtual Environment

**Windows PowerShell:**

```powershell
# 1. Create the virtual environment
python -m venv .venv

# 2. Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

_(Once activated, your terminal prompt will show `(.venv) PS D:\projects\...>`)_

**macOS / Linux / Git Bash:**

```bash
python -m venv .venv
source .venv/bin/activate
```

> **Note for Windows users**: If PowerShell blocks script activation with an execution policy error, run:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

### Step 2: Install Python Dependencies

All necessary packages for first-time setup (FastAPI, SQLite fallback driver `aiosqlite`, Temporal SDK, fuzzing tools, and testing utilities) have already been bundled and pushed directly into `requirements.txt` to save you installation and debugging time.

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

```powershell
python database/seed.py
```

_(Tip: If you didn't activate the `.venv`, you can run directly: `.\.venv\Scripts\python.exe database/seed.py`)_

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

**Option 1: Using Docker Compose (Recommended - Zero Install)**

```bash
docker-compose up -d
```

**Option 2: Using Standalone Temporal CLI**

If you have Temporal CLI (or ran `start-local.ps1` once):

```powershell
.\.venv\Scripts\Activate.ps1
temporal server start-dev --port 7233 --ui-port 8233 --ip 127.0.0.1
```

*(If Temporal CLI is not yet on your system, you can download the binary from [Temporal GitHub Releases](https://github.com/temporalio/cli/releases/latest) or run `irm https://temporal.download/cli.ps1 | iex`)*

_Web Console: http://localhost:8233_

#### Terminal 2: FastAPI Backend Server

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn apps.api.app.main:app --port 8000 --host 127.0.0.1 --reload
```

_Swagger API Docs: http://127.0.0.1:8000/docs_

#### Terminal 3: Temporal Worker

```powershell
.\.venv\Scripts\Activate.ps1
python -m temporal.worker
```

_Listens for workflow tasks on queue `order-supervisor-task-queue`._

#### Terminal 4: Next.js Frontend

```powershell
cd apps/web
npm run dev
```

_Web Dashboard: http://localhost:3000_

---

## 3. Demo Order & Verification

1. Open `http://localhost:3000` in your browser.
2. Visit `http://localhost:3000/runs/run_demo_1001` to view the seeded test order (`ORD-1001`, Sarah Connor).
3. Use the **Event Generator & Simulator** panel on the right to inject events (e.g. `payment_confirmed`, `shipment_delayed`, `delivered`).
4. Type live instructions (e.g. _"Prioritize speed over cost"_) in the **Dynamic Operator Directives** box and click Apply.

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
