# Order Supervisor AI Agent Platform

> Long-running AI supervisor that oversees e-commerce orders from creation to completion, orchestrated with **Temporal** workflows, **FastAPI**, **PostgreSQL**, and **Next.js (App Router + Tailwind CSS)**.

---

## 📸 Product Showcase

### 1. Live Order Control Room & Event Simulator
Supervise order lifecycles in real-time with milestone progress tracking, an active event stream, and a one-click event injector.

![Order Control Room](.github/public/order-run-dashboard.png)

### 2. Live Agent Memory Context & Dynamic Operator Directives
Inspect auto-compacting memory, cumulative milestone history, and inject mid-flight human guidance (e.g. *"Prioritize speed over cost"*).

![AI Memory and Live Operator Guidance](.github/public/live-activity-and-memory.png)

### 3. Supervisor Configuration & Wake Policy Sensitivity
Define custom AI templates, adjust classifier wake sensitivity (Conservative, Balanced, Aggressive), set sleep intervals, and toggle enabled tools.

![Supervisor Configuration Profiles](.github/public/supervisor-config-templates.png)

### 4. Temporal Long-Running Deterministic Workflow
Zero compute/token waste during dormant intervals with Temporal timers, activities, and signal handling.

![Temporal Workflow Timeline](.github/public/temporal-workflow-timeline.png)

---

## 🎯 Test Subject & Instant Showcase Order

The repository includes a ready-to-inspect test subject order seeded directly into the database:

- **Order ID**: `ORD-1001`
- **Customer**: Sarah Connor (`sarah@cyberdyne.io`)
- **Product**: Ergonomic Split Mechanical Keyboard ($499.00)
- **Active Supervisor**: `VIP & High-Value Order Supervisor` (Aggressive wake mode)
- **Active Human Directive**: *"For this order, prioritize speed over cost."*
- **Current State**: `SLEEPING` (awaiting courier pickup scan after verifying payment and alerting warehouse with rush priority)

To view the test subject, simply start the app and visit:
```
http://localhost:3000/runs/run_demo_1001
```

---

## Key Capabilities & Architectural Highlights

- **1 Workflow Run per Order**: Long-running lifecycle management powered by the `temporalio` Python SDK.
- **Event-Driven Wake/Sleep Cycle**: The AI does not run in an expensive polling loop. It sleeps using Temporal timers and only wakes on:
  1. **Workflow Start** (Initialization)
  2. **Incoming Signals/Events** (via a lightweight Classifier Policy)
  3. **Scheduled Wake-up Timers**
- **Two-Tier Event Classifier**: Evaluates incoming signals (`payment_failed`, `shipment_delayed`, `customer_message_received`, etc.) and determines whether immediate agent inference is required or if the workflow should remain asleep.
- **5 Business Tool Actions**:
  - `message_fulfillment_team`
  - `message_payments_team`
  - `message_logistics_team`
  - `message_customer`
  - `create_internal_note`
- **Context Compaction & Rolling Memory**: Synthesizes cumulative order history into a compact rolling summary to prevent context bloat.
- **Mid-Flight Operator Steering**: Inject dynamic instructions (e.g. _"Prioritize speed over cost"_) into active workflows via Temporal signals.
- **Interactive Event Simulator**: One-click simulation of order events and carrier delays from the web dashboard.
- **Post-Mortem & Completion**: Generates final executive summaries, key learnings, and feedback recommendations upon terminal completion (`delivered`, `cancelled`, or `terminated`).

---

## 🏗️ Repository Architecture

```text
order-supervisor/
│
├── apps/
│   ├── web/                              # Next.js 14 App Router + Tailwind CSS UI
│   │   ├── app/
│   │   │   ├── page.tsx                  # Live Dashboard
│   │   │   ├── runs/                     # Runs catalog & detailed control rooms
│   │   │   └── supervisors/              # Supervisor template manager
│   │   ├── components/runs/              # Timeline, ActivityLog, Memory, EventInjector, Controls
│   │   └── lib/                          # API client, TypeScript types, utils
│   │
│   └── api/                              # FastAPI Backend & Control Plane
│       └── app/
│           ├── main.py                   # App entrypoint, CORS, lifespan
│           ├── api/routes/               # supervisors, runs, events, instructions
│           ├── models/                   # SQLAlchemy DB entities
│           ├── schemas/                  # Pydantic request/response schemas
│           ├── services/                 # Temporal client wrapper & run services
│           └── db/                       # Database engine & fallback
│
├── temporal/                             # Temporal Engine
│   ├── workflows/
│   │   ├── order_supervisor.py           # Long-running OrderSupervisorWorkflow
│   │   ├── state.py                      # Deterministic workflow state
│   │   └── signals.py                    # Temporal signals & payloads
│   ├── activities/
│   │   ├── wake_policy.py                # Classifier activity (wake vs sleep)
│   │   ├── agent.py                      # Cognitive decision activity & tool selector
│   │   ├── memory.py                     # Memory compaction activity
│   │   └── persistence.py                # Activity & state DB sync
│   ├── tools/                            # 5 Business Action activities
│   │   ├── fulfillment.py
│   │   ├── payments.py
│   │   ├── logistics.py
│   │   ├── customer.py
│   │   └── internal_note.py
│   ├── worker.py                         # Temporal worker process
│   └── client.py                         # Temporal client connection
│
├── domain/                               # Shared Domain Enums & Schemas
│   ├── enums.py                          # OrderStatus, EventType, ActivityType, WakeReason
│   ├── models.py                         # OrderContext, OrderItem
│   └── memory.py                         # OrderCompactMemory
│
├── database/
│   ├── migrations/001_initial.sql        # PostgreSQL schema
│   └── seed.py                           # Seed default supervisors and sample orders
│
├── tests/
│   ├── api/                              # REST API and Schemathesis fuzzing tests
│   ├── unit/                             # Unit tests for wake policy, memory, and tools
│   └── workflows/                        # Temporal workflow integration tests
│
├── scripts/
│   ├── simulate-events.py                # CLI Event Injector
│   └── reset-db.py                       # Clean Database Reset script
│
├── docs/
│   ├── architecture.md                   # Detailed architecture note
│   └── demo-script.md                    # Walkthrough video presentation script
│
├── docker-compose.yml                    # PostgreSQL + Temporal Dev Server + Web UI
└── Makefile                              # Convenient developer targets
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Docker & Docker Compose

### 2. Start Infrastructure (PostgreSQL + Temporal)

```bash
# Start PostgreSQL (port 5432) and Temporal Dev Server (gRPC: 7233, Web UI: 8233)
docker-compose up -d
```

> _Temporal Web UI is accessible at [http://localhost:8233](http://localhost:8233)_

### 3. Initialize Python Environment & Seed Database

```bash
# In project root:
python -m venv .venv
.\.venv\Scripts\activate       # Windows PowerShell
# or source .venv/bin/activate # macOS/Linux

pip install -r requirements.txt

# Seed default supervisor templates and demo runs
python database/seed.py
```

### 4. Start the Temporal Worker

```bash
python -m temporal.worker
```

### 5. Start the FastAPI Backend

```bash
uvicorn apps.api.app.main:app --reload --port 8000
```

> _Interactive API documentation (Swagger UI) is available at [http://localhost:8000/docs](http://localhost:8000/docs)_

### 6. Start the Next.js Frontend

```bash
cd apps/web
npm install
npm run dev
```

> _Access the Web Application at [http://localhost:3000](http://localhost:3000)_

---

## 🧪 Running Automated Tests

```bash
pytest -v tests/unit
```

All unit tests verify:

- Priority event wake classifications and sensitivity modes.
- Context compaction and sliding memory rollups.
- Execution and structured outputs of all 5 business tools.

---

## 🎬 CLI Event Simulator

You can inject real-time signals into running workflows either from the **UI Simulator Panel** or using the CLI:

```bash
# Interactive CLI signal selector:
python scripts/simulate-events.py

# Or target a specific run with an event:
python scripts/simulate-events.py --run-id run_demo_1001 --event shipment_delayed

# Inject a dynamic live operator instruction:
python scripts/simulate-events.py --run-id run_demo_1001 --instruction "Prioritize speed over cost for this client."
```

---

## 📊 REST API Reference

| Method | Endpoint                          | Description                                     |
| :----- | :-------------------------------- | :---------------------------------------------- |
| `GET`  | `/api/supervisors`                | List all supervisor templates                   |
| `POST` | `/api/supervisors`                | Create a new supervisor configuration           |
| `GET`  | `/api/runs`                       | List all active and completed runs              |
| `POST` | `/api/runs`                       | Launch a new Order Supervisor Temporal workflow |
| `GET`  | `/api/runs/{run_id}`              | Get full run state, memory, and timeline        |
| `POST` | `/api/runs/{run_id}/events`       | Inject an event signal into the workflow        |
| `POST` | `/api/runs/{run_id}/instructions` | Inject dynamic live guidance                    |
| `POST` | `/api/runs/{run_id}/interrupt`    | Pause / sleep a running workflow                |
| `POST` | `/api/runs/{run_id}/resume`       | Resume a paused workflow                        |
| `POST` | `/api/runs/{run_id}/terminate`    | Terminate workflow and generate post-mortem     |
