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
  1. Inspect pre-configured supervisor templates (*Standard E-Commerce Supervisor*, *VIP & High-Value Order Supervisor*, *Returns & Disputed Orders Supervisor*).
  2. Demonstrate how wake sensitivity modes (*Aggressive*, *Balanced*, *Conservative*) harmonize with default sleep intervals (*1800s*, *3600s*, *7200s*).
  3. Create a custom supervisor profile (e.g. `VIP Priority v2`) with custom directives and tool selections.
  4. Demonstrate duplicate name prevention: typing an existing name shows an inline warning and disables submission.
  5. Click **"Use in New Order"** on the created profile.

---

### Step 2: Browsing the Seeded Order Catalog (14 Orders)
- **Location**: `http://localhost:3000/runs` (Runs Catalog)
- **Actions**:
  1. Filter by **`ALL (14)`**, **`ACTIVE (9)`**, **`COMPLETED (3)`**, or **`PAUSED (1)`**.
  2. Demonstrate the variety of realistic e-commerce scenarios:
     - `ORD-1001` (Sarah Connor): VIP split keyboard awaiting courier scan.
     - `ORD-1003` (Elena Rostova): Active 48h blizzard delay with carrier ticket.
     - `ORD-1005` (Amara Okafor): 1st delivery attempt failed with 3 reschedule slots.
     - `ORD-1007` (Chloe Bennett): Completed delivery with full AI post-mortem.
     - `ORD-1012` (James Wilson): Paused by operator for compliance review.
  3. Click on any order (e.g. `ORD-1001` / `run_demo_1001`) to open the Operator Cockpit.

---

### Step 3: Automated Lifecycle Autopilot (30s Default)
- **Location**: `http://localhost:3000/runs/run_demo_1001`
- **Actions**:
  1. Observe that **Autopilot is active by default**:
     - The top badge reads `AUTOPLAY (30s)`.
     - The countdown timer ticks down from 30 seconds with a real-time green progress bar.
  2. As each milestone fires automatically:
     - `Payment Verified` $\rightarrow$ Agent logs confirmation and notifies warehouse to pack.
     - `Shipment Dispatched` (30s) $\rightarrow$ Agent captures FedEx tracking (`FX-99881122`) and emails customer.
     - `Carrier Delay Alert` (30s) $\rightarrow$ Agent opens a FedEx escalation ticket and emails customer.
     - `Customer Inquiry` (30s) $\rightarrow$ Agent answers customer inquiry with tracking ETA.
     - `Parcel Delivered` (30s) $\rightarrow$ Concludes order and compiles AI post-mortem report.
  3. Demonstrate speed toggles: switch between **`5s`**, **`10s`**, and **`30s`** intervals on the fly.
  4. Click **`Skip`** to immediately advance to the next event without waiting for the timer.

---

### Step 4: Manual Verification Mode
- **Location**: `http://localhost:3000/runs/run_XXXX` $\rightarrow$ Signal & Event Simulator
- **Actions**:
  1. Click **`[ Manual ]`** at the top of the simulator panel.
  2. The automated timer immediately pauses, shifting the view to manual mode.
  3. Click any individual event button (e.g. *Payment Declined*, *Customer Not Home*, *No Tracking Update*).
  4. In the *Simulate Inbound Customer Message* box, type a custom question:
     *"Can you please hold my package at the local depot for 24 hours?"*
  5. Click **Send** $\rightarrow$ Watch the agent evaluate the request, call `message_logistics_team`, and confirm the depot hold.
  6. Click **`[ Autoplay (30s) ]`** to resume automated milestone progression.

---

### Step 5: Dynamic Human Operator Steering
- **Location**: Right sidebar $\rightarrow$ **Human Guidance** tab
- **Actions**:
  1. Select a quick preset or enter a custom directive:
     `"For this order, prioritize speed over cost."`
  2. Click **Apply Directive**.
  3. Observe the instruction saved to active memory context. On the next event wake, the agent references this directive in its reasoning trace.

---

### Step 6: Workflow Lifecycle Controls (Pause / Resume / Terminate)
- **Location**: Top control bar
- **Actions**:
  1. Click **Pause** $\rightarrow$ Workflow transitions to `PAUSED`, locking signal processing.
  2. Click **Resume** $\rightarrow$ Workflow returns to `RUNNING` / `SLEEPING`.

---

### Step 7: Terminal Post-Mortem & Strategic Output
- **Location**: Completed run (e.g. `ORD-1007` or after `Parcel Delivered`)
- **Actions**:
  1. Inspect the generated **Terminal Post-Mortem Report**:
     - Final Summary narrative of the order lifecycle.
     - Important actions taken across all tools.
     - Strategic key learnings on courier performance and delay management.
     - Operational feedback and recommendations for supply chain optimization.
  2. Open **Temporal Web UI** (`http://localhost:8233`) and verify that the workflow completed cleanly with a full audit ledger.
