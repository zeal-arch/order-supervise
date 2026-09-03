import pytest

from temporal.activities.agent import execute_agent_step_activity

STANDARD_ORDER = {
    "order_id": "ORD-COMPLIANCE-01",
    "customer_name": "Jane Smith",
    "customer_email": "jane.smith@example.com",
    "total_amount": 249.99,
}

SUPERVISOR_CONFIG = {
    "id": "sup_standard",
    "name": "Standard Supervisor",
    "default_wake_delay_seconds": 3600,
    "available_tools": [
        "message_fulfillment_team",
        "message_payments_team",
        "message_logistics_team",
        "message_customer",
        "create_internal_note",
    ],
}


@pytest.mark.asyncio
async def test_all_assignment_events_and_tool_invocations():
    """Validates that all events from assignment L150-L158 invoke the appropriate tools from L131-L138."""

    # 1. order_created
    res = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "order_created", "payload": {}}],
        "wake_reason": "order_created",
    })
    tools_called = [a["tool"] for a in res["actions_executed"]]
    assert "create_internal_note" in tools_called
    assert res["next_sleep_seconds"] > 0
    assert not res["is_terminal"]

    # 2. payment_confirmed
    res = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "payment_confirmed", "payload": {"amount": 249.99}}],
        "wake_reason": "payment_confirmed",
    })
    tools_called = [a["tool"] for a in res["actions_executed"]]
    assert "message_fulfillment_team" in tools_called
    assert "message_customer" in tools_called

    # 3. payment_failed
    res = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "payment_failed", "payload": {"reason": "insufficient_funds"}}],
        "wake_reason": "payment_failed",
    })
    tools_called = [a["tool"] for a in res["actions_executed"]]
    assert "message_customer" in tools_called
    assert "message_payments_team" in tools_called

    # 4. shipment_created
    res = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "shipment_created", "payload": {"carrier": "FedEx", "tracking_number": "TRK-1001"}}],
        "wake_reason": "shipment_created",
    })
    tools_called = [a["tool"] for a in res["actions_executed"]]
    assert "message_customer" in tools_called

    # 5. shipment_delayed
    res = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "shipment_delayed", "payload": {"carrier": "FedEx", "reason": "Snowstorm hub delay"}}],
        "wake_reason": "shipment_delayed",
    })
    tools_called = [a["tool"] for a in res["actions_executed"]]
    assert "message_logistics_team" in tools_called
    assert "message_customer" in tools_called
    assert "create_internal_note" in tools_called

    # 6. customer_message_received
    res = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "customer_message_received", "payload": {"message": "Can I change address?"}}],
        "wake_reason": "customer_message_received",
    })
    tools_called = [a["tool"] for a in res["actions_executed"]]
    assert "message_customer" in tools_called

    # 7. no_update_for_n_hours
    res = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "no_update_for_n_hours", "payload": {"hours": 48, "carrier": "FedEx"}}],
        "wake_reason": "no_update_for_n_hours",
    })
    tools_called = [a["tool"] for a in res["actions_executed"]]
    assert "message_logistics_team" in tools_called
    assert "create_internal_note" in tools_called

    # 8. refund_requested (Terminal)
    res = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "refund_requested", "payload": {"reason": "Cancelled by buyer"}}],
        "wake_reason": "refund_requested",
    })
    tools_called = [a["tool"] for a in res["actions_executed"]]
    assert "message_payments_team" in tools_called
    assert "message_customer" in tools_called
    assert res["is_terminal"] is True
    assert res["final_output"] is not None

    # 9. delivered (Terminal & Post-Mortem)
    res = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "delivered", "payload": {"signed_by": "Jane Smith"}}],
        "wake_reason": "delivered",
    })
    tools_called = [a["tool"] for a in res["actions_executed"]]
    assert "message_customer" in tools_called
    assert res["is_terminal"] is True


@pytest.mark.asyncio
async def test_operator_instructions_modulation():
    """Validates that instructions from assignment L207-L209 correctly modulate agent behavior."""

    # Instruction A: “For this order, prioritize speed over cost.”
    res_speed = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "payment_confirmed", "payload": {}}],
        "additional_instructions": [{"instruction": "For this order, prioritize speed over cost."}],
    })
    fulfillment_action = next(a for a in res_speed["actions_executed"] if a["tool"] == "message_fulfillment_team")
    assert fulfillment_action["args"]["priority"] == "rush"

    # Instruction B: “If shipment is delayed, escalate immediately.”
    res_escalate = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "shipment_delayed", "payload": {"reason": "Mechanical failure"}}],
        "additional_instructions": [{"instruction": "If shipment is delayed, escalate immediately."}],
    })
    logistics_action = next(a for a in res_escalate["actions_executed"] if a["tool"] == "message_logistics_team")
    assert logistics_action["args"]["urgency"] == "critical"

    # Instruction C: “Do not contact the customer without human review.”
    res_no_contact = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "payment_confirmed", "payload": {}}],
        "additional_instructions": [{"instruction": "Do not contact the customer without human review."}],
    })
    tools_called = [a["tool"] for a in res_no_contact["actions_executed"]]
    # message_customer MUST NOT be called directly!
    assert "message_customer" not in tools_called
    # A human review note MUST be created instead!
    human_note_action = next(a for a in res_no_contact["actions_executed"] if a["tool"] == "create_internal_note")
    assert human_note_action["args"]["flag_for_human"] is True
    assert "HELD FOR HUMAN REVIEW" in human_note_action["args"]["note"]


@pytest.mark.asyncio
async def test_terminal_post_mortem_report_structure():
    """Validates that terminal completion outputs all 4 required fields from assignment L219-L222:
    - final summary
    - important actions taken
    - key learnings
    - feedback or recommendations
    """
    res = await execute_agent_step_activity({
        "order_context": STANDARD_ORDER,
        "supervisor_config": SUPERVISOR_CONFIG,
        "recent_events": [{"event_type": "delivered", "payload": {"signed_by": "Jane Smith"}}],
    })
    assert res["is_terminal"] is True
    report = res["final_output"]
    assert report is not None

    # Verify all 4 required sections from L219-L222
    assert "final_summary" in report and len(report["final_summary"]) > 0
    assert "important_actions_taken" in report and isinstance(report["important_actions_taken"], list)
    assert "key_learnings" in report and len(report["key_learnings"]) > 0
    assert "feedback_and_recommendations" in report and len(report["feedback_and_recommendations"]) > 0
    assert "completed_at" in report
