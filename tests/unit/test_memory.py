import pytest

from temporal.activities.memory import update_compact_memory_activity


@pytest.mark.asyncio
async def test_memory_compaction():
    initial_memory = {
        "order_id": "ORD-TEST-99",
        "current_status": "PROCESSING",
        "key_events_summary": ["[order_created] at 10:00"],
        "actions_taken": ["message_fulfillment_team: Dispatched"],
    }
    recent_events = [
        {"event_type": "shipment_delayed", "timestamp": "2026-09-02T12:00:00Z"},
    ]
    actions_taken = [
        {"tool": "message_logistics_team", "summary": "Raised urgent carrier ticket"},
    ]
    reasoning = "Carrier delayed package. Escalated to logistics."

    updated = await update_compact_memory_activity({
        "previous_memory": initial_memory,
        "recent_events": recent_events,
        "actions_taken": actions_taken,
        "reasoning": reasoning,
    })

    assert len(updated["actions_taken"]) == 2
    assert "message_logistics_team: Raised urgent carrier ticket" in updated["actions_taken"]
    assert "ORD-TEST-99" in updated["rolling_summary"]
    assert len(updated["key_events_summary"]) == 2
