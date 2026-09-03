import logging
from datetime import datetime, timezone
from typing import Any

from temporalio import activity

from domain.memory import OrderCompactMemory

logger = logging.getLogger("temporal.activities.memory")


@activity.defn
async def update_compact_memory_activity(input_data: dict[str, Any]) -> dict[str, Any]:
    """Updates and compacts order memory context using the OrderCompactMemory domain model.

    Processes incoming events to derive lifecycle status transitions (payment_status,
    shipment_status, current_status, tracking_number), merges new agent actions into
    the deduplicated action set, and synthesizes a fresh rolling summary.
    """
    previous_memory: dict[str, Any] = input_data.get("previous_memory", {})
    recent_events: list[dict[str, Any]] = input_data.get("recent_events", [])
    actions_taken: list[dict[str, Any]] = input_data.get("actions_taken", [])
    reasoning: str = input_data.get("reasoning", "")
    order_context: dict[str, Any] = input_data.get("order_context", {})

    # --- Deserialize previous memory into the typed domain model ---
    # Provide safe fallbacks for any fields not yet present in the raw dict
    if not previous_memory.get("order_id"):
        previous_memory["order_id"] = order_context.get("order_id", "UNKNOWN")
    if not previous_memory.get("current_status"):
        previous_memory["current_status"] = "CREATED"

    memory = OrderCompactMemory.from_dict(previous_memory)

    # Backfill any static fields from order_context that may be missing
    if not memory.customer_name:
        memory.customer_name = order_context.get("customer_name")
    if not memory.customer_email:
        memory.customer_email = order_context.get("customer_email")
    if not memory.items_summary and order_context.get("items"):
        items = order_context["items"]
        memory.items_summary = f"{len(items)} items (${order_context.get('total_amount', 0):.2f})"
    if not memory.total_amount and order_context.get("total_amount"):
        memory.total_amount = order_context["total_amount"]

    # --- Apply event-driven state transitions ---
    if recent_events:
        memory.update_from_events(recent_events)

    # --- Merge new agent actions (deduplicated) ---
    memory.merge_actions(actions_taken)

    # --- Rebuild rolling summary from current state ---
    memory.rolling_summary = memory.build_rolling_summary(reasoning)

    # --- Store last agent reasoning verbatim ---
    if reasoning:
        memory.last_agent_reasoning = reasoning

    # --- Stamp update time ---
    memory.last_updated_at = datetime.now(timezone.utc)

    updated_memory = memory.model_dump(mode="json")

    print(
        f"  🧠 [MEMORY UPDATE] Order: {memory.order_id} | "
        f"Status: {memory.current_status} | "
        f"Payment: {memory.payment_status} | "
        f"Shipment: {memory.shipment_status} | "
        f"Actions: {len(memory.actions_taken)} | "
        f"Key Events: {len(memory.key_events_summary)}"
    )

    return updated_memory
