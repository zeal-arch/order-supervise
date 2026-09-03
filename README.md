# Order Supervisor

A long-running order supervision system built with Temporal, FastAPI, and Next.js. Each order runs as an isolated Temporal workflow that reacts to external events (payment confirmations, carrier tracking, delays), executes business actions through tool activities, maintains state memory, and sleeps when inactive.

---

## Interface & Workflow Run

### Order Run View & Event Simulator
Tracks live order milestones, tool execution logs, and incoming event stream with interactive event simulation.

![Order Control Room](.github/public/order-run-dashboard.png)

### Agent Memory & Operator Directives
Sliding-window memory summary, milestone history, and manual instruction injection to adjust agent behavior mid-flight.

![AI Memory and Live Operator Guidance](.github/public/live-activity-and-memory.png)

### Supervisor Configuration
Configurable supervisor profiles with customizable wake sensitivity, sleep intervals, model selection, and tool permissions.

![Supervisor Configuration Profiles](.github/public/supervisor-config-templates.png)

### Temporal Workflow Execution
Long-running workflow execution showing timer-based sleep cycles, signal triggers, and activity dispatches.

![Temporal Workflow Timeline](.github/public/temporal-workflow-timeline.png)

---

## Demo Order (ORD-1001)

The database seed includes a sample order to test out of the box:

- **Order ID**: `ORD-1001`
- **Customer**: Sarah Connor (`sarah@cyberdyne.io`)
- **Item**: Ergonomic Split Mechanical Keyboard ($499.00)
- **Profile**: `VIP & High-Value Order Supervisor`
- **Active Directive**: "For this order, prioritize speed over cost."
- **Status**: `SLEEPING` (awaiting carrier tracking scan after payment verification)

To view it after starting the stack, open `http://localhost:3000/runs/run_demo_1001`.

---

## Core Mechanics

- **One Workflow per Order**: Orders are modeled as long-running Temporal workflows that persist until delivery, cancellation, or manual termination.
- **Event-Driven Wake/Sleep**: The workflow sleeps via Temporal timers (`wait_condition`). It only wakes when:
  1. The workflow first initializes
  2. An incoming signal is received (filtered through a wake policy classifier)
  3. A scheduled timer fires
- **Wake Policy Classifier**: A lightweight activity evaluates event priority against the supervisor's sensitivity setting (Conservative, Balanced, Aggressive) to decide whether to trigger immediate agent evaluation or remain asleep.
- **Business Tools**:
  - `message_fulfillment_team`: Warehouse packing and dispatch alerts.
  - `message_payments_team`: Billing alerts, payment failures, and refunds.
  - `message_logistics_team`: Courier inquiries and carrier tickets.
  - `message_customer`: Customer transactional emails and delay updates.
  - `create_internal_note`: Audit notes and human review flags.
- **Dynamic Directives**: Operators can signal runtime instructions (e.g., "Do not contact customer without human review") that modulate tool behavior.
- **Terminal Post-Mortem**: When an order reaches completion (`delivered` or `refund_requested`), the agent outputs a summary, actions taken, key learnings, and operational recommendations.

---

## Project Structure

```text
order-supervisor/
├── apps/
│   ├── web/                    # Next.js 14 frontend (App Router, Tailwind CSS)
│   │   ├── app/                # Pages: dashboard, runs, supervisor profiles
│   │   └── components/runs/    # Feed, timeline, controls, simulator
│   └── api/                    # FastAPI backend
│       ├── app/api/routes/     # REST endpoints for runs and supervisors
│       ├── app/models/         # SQLAlchemy models (runs, events, activities)
│       └── app/services/       # Temporal client wrapper and orchestration logic
├── temporal/
│   ├── workflows/              # OrderSupervisorWorkflow implementation & state
│   ├── activities/             # Agent evaluation, wake classifier, memory compaction
│   └── tools/                  # Business action tool activities
├── domain/                     # Shared models, enums, and schemas
├── database/                   # Seed script and initial SQL migrations
├── tests/
│   ├── unit/                   # Wake policy, memory compaction, and tool tests
│   ├── workflows/              # End-to-end Temporal workflow integration tests
│   └── api/                    # REST API tests and Schemathesis property fuzzing
└── scripts/                    # Event injection CLI and local launch helpers
```

---

## Setup & Running Locally

### Requirements
- Python 3.11+
- Node.js 18+ and npm
- Docker and Docker Compose

### 1. Start Infrastructure
Start PostgreSQL and the Temporal development server:
```bash
docker-compose up -d
```
The Temporal Web UI is accessible at `http://localhost:8233`.

### 2. Backend & Worker Setup
Install Python dependencies and seed supervisor profiles and demo data:
```bash
python -m venv .venv
.\.venv\Scripts\activate       # On Windows PowerShell
# source .venv/bin/activate    # On Linux/macOS

pip install -r requirements.txt
python database/seed.py
```

Start the Temporal worker:
```bash
python -m temporal.worker
```

In a separate terminal, start the FastAPI server:
```bash
uvicorn apps.api.app.main:app --reload --port 8000
```
Swagger API docs are available at `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## Testing

Run the full test suite (unit tests, workflow tests, and API fuzzing):
```bash
pytest tests
```

To run a specific test suite:
```bash
pytest tests/unit/test_assignment_compliance.py -v   # Event, tool, and instruction verification
pytest tests/workflows/test_order_supervisor.py -v     # Temporal workflow tests
pytest tests/api/test_schemathesis.py -v              # API fuzz testing
```

---

## Event Simulation CLI

Events can be injected through the web UI or via the CLI script:
```bash
# Interactive mode:
python scripts/simulate-events.py

# Send specific event to an order run:
python scripts/simulate-events.py --run-id run_demo_1001 --event shipment_delayed

# Inject an operator directive:
python scripts/simulate-events.py --run-id run_demo_1001 --instruction "Prioritize speed over cost."
```

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/supervisors` | List supervisor templates |
| `POST` | `/api/supervisors` | Create a supervisor profile |
| `GET` | `/api/runs` | List order runs |
| `POST` | `/api/runs` | Start a new order supervisor workflow |
| `GET` | `/api/runs/{run_id}` | Get run state, timeline, and memory |
| `POST` | `/api/runs/{run_id}/events` | Send an event signal to the workflow |
| `POST` | `/api/runs/{run_id}/instructions` | Send an operator directive signal |
| `POST` | `/api/runs/{run_id}/interrupt` | Pause workflow execution |
| `POST` | `/api/runs/{run_id}/resume` | Resume paused workflow |
| `POST` | `/api/runs/{run_id}/terminate` | Terminate workflow and generate post-mortem |
