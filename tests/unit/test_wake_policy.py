import pytest

from temporal.activities.wake_policy import evaluate_wake_policy_activity


@pytest.mark.asyncio
async def test_critical_events_always_wake():
    critical_events = [
        "payment_failed",
        "shipment_delayed",
        "refund_requested",
        "customer_message_received",
        "manual_instruction",
    ]
    for event in critical_events:
        res = await evaluate_wake_policy_activity({"event_type": event, "sensitivity": "balanced"})
        assert res["should_wake"] is True, f"Event {event} should wake the agent"


@pytest.mark.asyncio
async def test_sensitivity_modes():
    # Conservative mode should not wake for shipment_created
    res_conservative = await evaluate_wake_policy_activity(
        {"event_type": "shipment_created", "sensitivity": "conservative"}
    )
    assert res_conservative["should_wake"] is False

    # Aggressive mode should wake for shipment_created
    res_aggressive = await evaluate_wake_policy_activity(
        {"event_type": "shipment_created", "sensitivity": "aggressive"}
    )
    assert res_aggressive["should_wake"] is True
