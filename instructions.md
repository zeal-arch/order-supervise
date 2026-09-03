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

All necessary packages (FastAPI, SQLite fallback driver `aiosqlite`, Temporal SDK, fuzzing tools, and testing utilities) are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Step 3: Install Frontend Dependencies

```bash
cd apps/web
npm install
cd ../..
```

### Step 4: Seed the Database & 14 Demo Orders

This initializes the database schema, default supervisor templates, and a catalog of **14 diverse demo orders** (`ORD-1001` through `ORD-1014`):

```powershell
python database/seed.py
```

_(Tip: If you didn't activate the `.venv`, you can run directly: `.\.venv\Scripts\python.exe database/seed.py`)_

---

## 2. Running the Application

You can run the full platform using the **Automated 1-Click Launcher** (recommended) or manually across **4 separate terminal tabs**.

---

### Method 1: Automated 1-Click Launcher (Recommended)

This is the fastest method. It automatically manages Temporal CLI, opens port 7233, starts the API, connects the agent worker, and launches the web frontend in a single terminal.

**Windows PowerShell:**

```powershell
.\scripts\start-local.ps1
```

**macOS / Linux / Git Bash:**

```bash
bash scripts/start-local.sh
```

**What this starts:**
1. **Temporal Dev Server** (`http://localhost:8233`, gRPC port `7233`)
2. **FastAPI Backend & API Docs** (`http://127.0.0.1:8000/docs`)
3. **Temporal Worker Engine** (processes AI agent tool calls and workflow decisions)
4. **Next.js Web Frontend** (`http://localhost:3000`)

*(Press `Ctrl+C` in this terminal anytime to stop all 4 services cleanly).*

---

### Method 2: Manual Multi-Terminal Launch (4 Terminals)

If you prefer to run each service individually in its own terminal tab for debugging or inspection:

#### Terminal 1: Temporal Server

```powershell
.\.venv\Scripts\Activate.ps1
temporal server start-dev --port 7233 --ui-port 8233 --ip 127.0.0.1
```

*(Note: If `temporal` is not yet on your machine, simply run `.\scripts\start-local.ps1` once to let it auto-install, or download `temporal.exe` from [Temporal GitHub Releases](https://github.com/temporalio/cli/releases/latest) into `.venv\Scripts`).*

_Temporal Web Console: http://localhost:8233_

#### Terminal 2: FastAPI Backend Server

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn apps.api.app.main:app --port 8000 --host 127.0.0.1 --reload
```

_Interactive Swagger Docs: http://127.0.0.1:8000/docs_

#### Terminal 3: Temporal Worker Engine

```powershell
.\.venv\Scripts\Activate.ps1
python -m temporal.worker
```

_Listens for workflow tasks and executes agent decisions on queue `order-supervisor-task-queue`._

#### Terminal 4: Next.js Frontend UI

```powershell
cd apps/web
npm run dev
```

_Web Dashboard: http://localhost:3000_

---

## 3. Order Lifecycle & Simulation Testing

Every order created or opened operates with **Automated Autopilot enabled by default**, advancing through the order lifecycle in 30-second intervals, while providing a dedicated **Manual Mode** for manual testing.

### Option A: Via Web UI Dashboard (Recommended for Presentations)

1. Open `http://localhost:3000` in your browser.
2. Click on any seeded order from the list (or `ORD-1001` / `run_demo_1001`).
3. **Automated Autopilot (Active by Default)**:
   - The simulator automatically counts down 30 seconds between each milestone event:
     `Payment Verified` -> `Shipment Dispatched` (30s) -> `Carrier Delay Alert` (30s) -> `Customer Inquiry` (30s) -> `Parcel Delivered` (30s).
   - You can watch the agent wake up from Temporal sleep, run inference, execute tools, and update memory.
   - Adjust speed between **`5s`**, **`10s`**, and **`30s`** on the fly, or click **`Skip`** to immediately advance to the next event.
4. **Manual Verification Mode**:
   - Click **`[ Manual ]`** at the top of the simulator panel to pause automation.
   - Click individual event buttons (*Payment Declined*, *Customer Not Home*, *No Tracking Update*) or type a custom customer message.
   - Click **`[ Autoplay (30s) ]`** to resume automatic progression.
5. In the **Human Guidance** tab, enter live operator directives (e.g. *"For this order, prioritize speed over cost"*) to dynamically steer agent decisions.

---

### Option B: Via Command Line Script (`simulate-events.py`)

You can also simulate events directly from a terminal:

**1. Automated Full Lifecycle Simulation (30-second gaps):**
```powershell
.\.venv\Scripts\Activate.ps1
python scripts/simulate-events.py --auto --interval 30
```

**2. Interactive Manual Event Selection:**
```powershell
python scripts/simulate-events.py
```
*(Presents an interactive menu where you can choose Option `A` for full auto-simulation or select individual events `1-9`).*

**3. Injecting a Live Operator Directive via CLI:**
```powershell
python scripts/simulate-events.py --instruction "For this order, prioritize speed over cost."
```

---

## 4. Running Tests

### 4.1 Comprehensive End-to-End Live Workflow Test (`scripts/run-comprehensive-test.py`)

This test executes a complete, real-time end-to-end evaluation against the running Temporal server and FastAPI backend. It subjects a VIP order to **5 domain milestone events** and **2 live human operator interventions**:

1. **Order Launch**: Starts VIP order ($1,850.00) with `VIP & High-Value Order Supervisor`.
2. **Milestone 1 (`payment_confirmed`)**: Agent wakes up, verifies payment, and dispatches rush packing to fulfillment.
3. **Milestone 2 (`shipment_created`)**: Agent captures FedEx tracking and sends customer tracking update.
4. **Human Intervention 1 (Operator Steering)**: Operator injects a live mid-flight directive:  
   *`"VIP Client Rule: If any courier delay occurs, immediately escalate to Tier-3 logistics and offer a 20% future store credit."`*
5. **Milestone 3 (`shipment_delayed`)**: Severe 72h blizzard delay. Agent wakes up immediately, **incorporates the live operator directive**, opens a Tier-3 logistics case, and emails customer offering the 20% credit.
6. **Human Intervention 2 (Pause & Resume)**: Tests workflow control plane by sending `pause_signal` (locks workflow) and `resume_signal` (resumes workflow cleanly).
7. **Milestone 4 (`customer_message_received`)**: Customer inquires about blizzard safety. Agent answers with updated timeline.
8. **Milestone 5 (`delivered`)**: Carrier confirms delivery. Agent compiles final summary, key learnings, and recommendations.

**To run the comprehensive live test:**

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/run-comprehensive-test.py
```

---

### 4.2 Automated Test Suites (Pytest)

To run the full automated test suite (32 tests):

```powershell
.\.venv\Scripts\Activate.ps1
pytest tests
```

To run individual test suites:

```powershell
pytest tests/unit/test_assignment_compliance.py -v   # Event & tool compliance
pytest tests/workflows/test_order_supervisor.py -v     # Temporal workflow integration tests
pytest tests/api/test_schemathesis.py -v              # API fuzz tests
```

---

## 5. Database Reset

To reset the database back to clean seeded defaults (all 14 demo orders):

```powershell
python scripts/reset-db.py
```
