# Order Supervisor: Technical Architecture & System Design

## 1. System Overview & Durable Execution Model

Order Supervisor is an autonomous operations agent designed to oversee the lifecycle of an e-commerce order from creation to terminal completion.

Traditional systems either rely on high-frequency cron polling or process events in stateless webhook handlers. In contrast, this platform models every order as a persistent, long-running Temporal workflow execution (`order-supervisor-{order_id}`).

Key architectural properties:

- **Durable Lifecycle State**: The workflow execution survives server restarts, process crashes, and network partitions without losing variables, timers, or history.
- **Zero-CPU Dormancy**: Between events, the agent remains completely dormant using Temporal timers (`workflow.wait_condition`), consuming 0 tokens and 0% CPU.
- **Event-Driven Reactivity**: Incoming domain signals immediately wake the workflow to evaluate operational risk and take corrective actions.

```
+-------------------------------------------------------------------------+
|                               Next.js 14 UI                             |
|          Operator Cockpit, Event Simulator, Profile Configuration       |
+-------------------------------------------------------------------------+
                                    |
                                    | HTTP REST
                                    v
+-------------------------------------------------------------------------+
|                              FastAPI Backend                            |
|             API Gateway, Signal Dispatcher, Run State Service           |
+-------------------------------------------------------------------------+
                                    |
                                    | gRPC
                                    v
+-------------------------------------------------------------------------+
|                        Temporal Workflow Engine                         |
|                                                                         |
|  OrderSupervisorWorkflow (workflows/order_supervisor.py)                |
|  - Deterministic state machine                                          |
|  - Signal handlers: order_event, instruction, pause, resume, terminate  |
|  - Sleep management: workflow.wait_condition                            |
|  - History truncation: workflow.continue_as_new                         |
+-------------------------------------------------------------------------+
          |                                            |
          | Schedules                                  | Persists
          v                                            v
+-------------------------------------+   +-------------------------------+
|            Worker Process           |   |       Database Storage        |
|                                     |   |     (PostgreSQL / SQLite)     |
| 1. Evaluate Wake Policy Activity    |   |                               |
| 2. Execute Agent Step Activity      |-->| - runs (state, memory, report)|
| 3. Business Tools (5 modules)       |   | - events (raw signal log)     |
| 4. Update Compact Memory Activity   |   | - activities (tool audit log) |
| 5. Persist State Activity           |   | - supervisors (config presets)|
+-------------------------------------+   +-------------------------------+
```

---

## 2. Temporal Workflow Lifecycle & The 3 Wake Triggers

The core execution loop in `temporal/workflows/order_supervisor.py` handles three distinct triggers:

1. **Workflow Start (`WORKFLOW_START`)**:
   - Fires immediately upon order initialization.
   - Evaluates initial order context, logs the genesis audit note, initializes rolling memory, and schedules the first sleep cycle.

2. **Incoming Signals (`EVENT_SIGNAL` / `MANUAL_INSTRUCTION`)**:
   - External events
     (`payment_failed`, `shipment_delayed`, `customer_message_received`)
     are delivered via
     `@workflow.signal(name="order_event_signal")`.
   - The wait condition unblocks immediately and executes triage.

3. **Scheduled Wake-up (`SCHEDULED_TIMER`)**:
   - When the sleep timer expires without incoming signals, the workflow wakes for a routine health inspection and staleness check.

---

## 3. Two-Tier Event Classification & Triage Policy

To prevent unnecessary LLM token consumption on routine informational pings, incoming events pass through a lightweight classifier (`temporal/activities/wake_policy.py`) before invoking the cognitive agent:

| Event Type                  | Priority Tier | Reaction in Balanced Mode    | Reaction in Conservative Mode |
| :-------------------------- | :------------ | :--------------------------- | :---------------------------- |
| `payment_failed`            | Critical      | Wake immediately             | Wake immediately              |
| `shipment_delayed`          | Critical      | Wake immediately             | Wake immediately              |
| `refund_requested`          | Critical      | Wake immediately             | Wake immediately              |
| `customer_message_received` | Critical      | Wake immediately             | Wake immediately              |
| `delivery_attempt_failed`   | Critical      | Wake immediately             | Wake immediately              |
| `no_update_for_n_hours`     | Critical      | Wake immediately             | Wake immediately              |
| `manual_instruction`        | Critical      | Wake immediately             | Wake immediately              |
| `payment_confirmed`         | Informational | Wake (advances to packing)   | Defer to scheduled wake       |
| `shipment_created`          | Informational | Wake (records tracking)      | Defer to scheduled wake       |
| `delivered`                 | Boundary      | Wake immediately (completes) | Wake immediately (completes)  |

---

## 4. Agent Runtime & Business Action Tools

When the workflow determines that agent inference is required, it schedules `execute_agent_step_activity`. The agent reasons over current status, active instructions, and event history, and dispatches appropriate tools:

1. **`message_fulfillment_team`** (`temporal/tools/fulfillment.py`):
   - Dispatches warehouse packing, hold, or expedited handling instructions.
2. **`message_payments_team`** (`temporal/tools/payments.py`):
   - Flags billing discrepancies, decline codes, and authorizes return refunds.
3. **`message_logistics_team`** (`temporal/tools/logistics.py`):
   - Opens carrier escalation tickets with FedEx, UPS, or DHL for transit bottlenecks and NDR holds.
4. **`message_customer`** (`temporal/tools/customer.py`):
   - Sends proactive email and SMS notifications directly to the customer.
5. **`create_internal_note`** (`temporal/tools/internal_note.py`):
   - Records structured operational audit entries (`logistics_incident`, `workflow_init`, `staleness_check`).

---

## 5. Memory Architecture & Rolling Compaction

To ensure long-running workflows do not exceed context limits or database constraints over weeks of execution, the platform implements structured compaction (`temporal/activities/memory.py`):

- **Order Header**: Preserves immutable identity (Order ID, customer name, total amount, currency).
- **Key Milestones Summary**: Retains a clean chronological array of lifecycle transitions (`[payment_confirmed]`, `[shipment_delayed]`, `[delivered]`).
- **Rolling Natural Language Narrative**: Synthesizes the cumulative state into a self-contained summary paragraph used as active context in subsequent LLM prompts.
- **Action Set**: De-duplicates and stores the unique set of business actions taken.

---

## 6. Control Plane, Signals & History Management

The platform supports operator control signals and long-history management:

- **Pause / Resume / Terminate**: FastAPI sends control signals (`pause_signal`, `resume_signal`, `terminate_signal`) directly to the running workflow. When paused, the workflow updates status to `PAUSED` and waits for resume without terminating.
- **Dynamic Operator Steering**: Operators inject directives (e.g. _"Prioritize speed over cost"_, _"Offer 15% refund credit"_) via `instruction_signal`. The instruction is merged into the agent's active memory context.
- **History Truncation (`continue_as_new`)**: When an order lifecycle exceeds 100 events or Temporal suggests compaction (`workflow.info().is_continue_as_new_suggested()`), the workflow calls `workflow.continue_as_new()`, carrying forward the compacted memory while resetting the event ledger.

---

## 7. End-of-Run Post-Mortem & Strategic Output

When an order reaches a terminal state (`delivered` or `refund_requested`), the agent generates a structured completion report persisted in `runs.final_output`:

- **Final Summary**: Narrative of the entire order lifecycle from creation to resolution.
- **Important Actions Taken**: Complete audit list of tool actions dispatched.
- **Key Learnings**: Operational takeaways (e.g., proactive courier tickets reducing customer support inquiries).
- **Feedback & Recommendations**: Actionable suggestions for supply chain and fulfillment improvements.
