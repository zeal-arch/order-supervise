# Walkthrough Demonstration & Evaluation Guide

This guide provides a structured, step-by-step walkthrough outline for evaluating the Order Supervisor platform locally.

---

## Service Endpoints & Verification URLs

- Next.js Web Application: `http://localhost:3000`
- FastAPI REST Swagger Documentation: `http://localhost:8000/docs`
- Temporal Web UI Dashboard: `http://localhost:8233`

---

## Step-by-Step Demonstration Flow

### Step 1: Supervisor Profile Configuration
- **Location**: `http://localhost:3000/supervisors`
- **Actions**:
  1. Inspect pre-configured supervisor templates (*Standard Retail Guardian*, *VIP Express Supervisor*, *Cost-Efficient Logistics*).
  2. Demonstrate how wake sensitivity modes (*Aggressive*, *Balanced*, *Conservative*) harmonize with default sleep intervals (*1800s*, *3600s*, *7200s*).
  3. Create a custom supervisor profile (e.g. `VIP Priority v2`) with custom directives and tool selections.
  4. Demonstrate duplicate name prevention: typing an existing name shows an inline warning and disables submission.
  5. Click **"Use in New Order"** on the created profile.

---

### Step 2: Launching an Order Workflow
- **Location**: `http://localhost:3000` (Dashboard)
- **Actions**:
  1. Enter an Order ID (e.g. `ORD-8820`) or click **"+ Random ID"**.
  2. Select the supervisor template from the dropdown.
  3. Click **"Launch"** to start the workflow.
  4. View the 2-panel cockpit on `/runs/run_XXXX`:
     - Left column: Chronological Execution & Activity Trace (`EVENT` and `ACTION` tags).
     - Right column: Sticky operational sidebar with Event Simulator, AI Memory, and Human Guidance tabs.
  5. Switch to **Temporal Web UI** (`http://localhost:8233`) and show `order-supervisor-ORD-8820` with status `Running` and event `WorkflowExecutionStarted`.

---

### Step 3: Event Ingestion & Autonomous Tool Execution
- **Location**: `http://localhost:3000/runs/run_XXXX` (Operator Cockpit)
- **Actions**:
  1. In the simulator sidebar, click **"Payment Verified"** $\rightarrow$ Agent logs confirmation and notifies warehouse to pack.
  2. Click **"Shipment Dispatched"** $\rightarrow$ Agent records FedEx tracking number (`FX-99881122`) and emails the customer.
  3. Click **"Carrier Delay Alert"** (48h blizzard delay) $\rightarrow$ The two-tier classifier marks this as `CRITICAL`:
     - Agent opens a carrier ticket with FedEx (`message_logistics_team`).
     - Agent sends a proactive update email to the customer (`message_customer`).
     - Agent records an internal incident note and schedules its next check in 1 hour.
  4. Click **"View Supervisor Decision"** to expand the agent's step-by-step reasoning trace.

---

### Step 4: Mid-Flight Human Operator Steering
- **Location**: Right sidebar $\rightarrow$ **Human Guidance** tab
- **Actions**:
  1. Select a quick preset or type a custom instruction:
     `"Offer 15% refund credit if customer complains about delay"`
  2. Click **"[Steer AI]"**.
  3. In the event simulator, send an inbound customer inquiry:
     *"Hi, will my order be delayed further due to the blizzard?"*
  4. Observe the agent incorporating the 15% refund policy into its response and active memory context.

---

### Step 5: Memory Inspection & Raw JSON Export
- **Location**: Right sidebar $\rightarrow$ **AI Memory State** card
- **Actions**:
  1. Inspect the rolling state narrative and milestone bullet list.
  2. Toggle from **"Summary"** to **"JSON"** view to inspect the compacted memory tree.
  3. Click **"Copy"** to copy `JSON.stringify(memory, null, 2)` to the clipboard.

---

### Step 6: Workflow Lifecycle Controls (Pause / Resume)
- **Location**: Top control bar
- **Actions**:
  1. Click **"Pause"** $\rightarrow$ Workflow status transitions to `PAUSED`, locking simulator actions.
  2. Click **"Resume"** $\rightarrow$ Workflow returns to `RUNNING` / `SLEEPING`.

---

### Step 7: Order Completion & Terminal Post-Mortem Report
- **Location**: Simulator sidebar
- **Actions**:
  1. Click **"Parcel Delivered"**.
  2. Order transitions to `COMPLETED`.
  3. Review the generated **Post-Mortem & Learnings** report:
     - Final Summary narrative.
     - Complete list of important actions taken.
     - Strategic key learnings on courier performance.
     - Operational feedback and recommendations.
  4. Verify in Temporal UI (`http://localhost:8233`) that the workflow has closed cleanly with a complete event ledger.
