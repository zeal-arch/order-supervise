import logging
from typing import Any

from temporalio import activity

logger = logging.getLogger("temporal.activities.wake_policy")


@activity.defn
async def evaluate_wake_policy_activity(input_data: dict[str, Any]) -> dict[str, Any]:
    """Lightweight classifier activity that determines whether an incoming event requires waking the main agent."""
    event_type = input_data.get("event_type", "")
    sensitivity = input_data.get("sensitivity", "balanced")

    CRITICAL_EVENTS = {
        "payment_failed",
        "shipment_delayed",
        "refund_requested",
        "customer_message_received",
        "no_update_for_n_hours",
        "delivery_attempt_failed",
        "customer_not_home",
        "manual_instruction",
    }

    INFORMATIONAL_EVENTS = {
        "order_created",
        "payment_confirmed",
        "shipment_created",
        "delivered",
    }

    should_wake = False
    reason = ""

    if event_type in CRITICAL_EVENTS:
        should_wake = True
        reason = f"Critical priority exception '{event_type}' requires immediate supervisor intervention."
    elif event_type in INFORMATIONAL_EVENTS:
        if sensitivity == "aggressive":
            should_wake = True
            reason = f"Aggressive mode: processing informational milestone '{event_type}' immediately."
        elif sensitivity == "conservative":
            should_wake = (event_type in ["order_created", "delivered"])
            reason = f"Conservative mode: {'waking for boundary milestone' if should_wake else 'deferring to scheduled wake'}"
        else: # balanced
            should_wake = True
            reason = f"Balanced mode: processing order lifecycle event '{event_type}'."
    else:
        should_wake = True
        reason = f"Custom domain event '{event_type}' received."

    print("\n" + "-" * 76)
    print(f"  [WAKE POLICY CLASSIFIER] Event: {event_type}")
    print(f"  Priority:   {'CRITICAL' if event_type in CRITICAL_EVENTS else 'INFORMATIONAL'}")
    print(f"  Decision:   {'>>> WAKE AGENT IMMEDIATELY' if should_wake else '--- STAY ASLEEP'}")
    print(f"  Reason:     {reason}")
    print("-" * 76)

    return {
        "should_wake": should_wake,
        "reason": reason,
        "event_type": event_type,
    }
