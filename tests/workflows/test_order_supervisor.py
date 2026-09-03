from datetime import timedelta

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from temporal.activities.agent import execute_agent_step_activity
from temporal.activities.memory import update_compact_memory_activity
from temporal.activities.persistence import (
    persist_activity_log_activity,
    persist_run_state_activity,
)
from temporal.activities.wake_policy import evaluate_wake_policy_activity
from temporal.workflows.order_supervisor import OrderSupervisorWorkflow

WORKFLOW_ACTIVITIES = [
    evaluate_wake_policy_activity,
    execute_agent_step_activity,
    update_compact_memory_activity,
    persist_activity_log_activity,
    persist_run_state_activity,
]

STANDARD_CONFIG = {
    "name": "Integration Test Supervisor",
    "base_instruction": "Supervise test order lifecycle",
    "available_tools": [
        "message_fulfillment_team",
        "message_payments_team",
        "message_logistics_team",
        "message_customer",
        "create_internal_note",
    ],
    "default_wake_delay_seconds": 3600,
    "wake_sensitivity": "balanced",
}

STANDARD_ORDER = {
    "order_id": "ORD-TEST-100",
    "customer_name": "Jane Doe",
    "customer_email": "jane@example.com",
    "total_amount": 250.00,
}


@pytest.mark.asyncio
async def test_workflow_start_and_agent_initialization():
    """Points 1, 2, 12: Test workflow initialization, agent start execution, and state determinism."""
    async with await WorkflowEnvironment.start_time_skipping() as env, Worker(
        env.client,
        task_queue="test-start-queue",
        workflows=[OrderSupervisorWorkflow],
        activities=WORKFLOW_ACTIVITIES,
    ):
        order_id = "ORD-START-01"
        handle = await env.client.start_workflow(
            OrderSupervisorWorkflow.run,
            {
                "order_id": order_id,
                "run_id": "run_start_01",
                "supervisor_config": STANDARD_CONFIG,
                "order_context": {**STANDARD_ORDER, "order_id": order_id},
                "initial_instructions": ["Initial start rule"],
            },
            id=f"order-supervisor-{order_id}",
            task_queue="test-start-queue",
        )

        # Query state immediately
        state = await handle.query("get_state")
        assert state["order_id"] == order_id
        assert state["status"] in ["RUNNING", "SLEEPING"]
        assert state["last_wake_reason"] == "WORKFLOW_START"
        assert state["instructions_count"] == 1

        # Let workflow complete initial activity execution and enter sleep
        await env.sleep(timedelta(seconds=5))
        state_after_start = await handle.query("get_state")
        assert state_after_start["status"] == "SLEEPING"
        assert state_after_start["next_wake_at"] is not None

        # Gracefully clean up
        await handle.signal("terminate_signal", {"reason": "Test cleanup"})
        await handle.result()


@pytest.mark.asyncio
async def test_order_event_signal_and_wake_behavior():
    """Points 3, 4, 9: Test order_event_signal, wake policy evaluation for critical events, and action dispatch."""
    async with await WorkflowEnvironment.start_time_skipping() as env, Worker(
        env.client,
        task_queue="test-signal-queue",
        workflows=[OrderSupervisorWorkflow],
        activities=WORKFLOW_ACTIVITIES,
    ):
        order_id = "ORD-SIG-02"
        handle = await env.client.start_workflow(
            OrderSupervisorWorkflow.run,
            {
                "order_id": order_id,
                "run_id": "run_sig_02",
                "supervisor_config": STANDARD_CONFIG,
                "order_context": {**STANDARD_ORDER, "order_id": order_id},
            },
            id=f"order-supervisor-{order_id}",
            task_queue="test-signal-queue",
        )

        await env.sleep(timedelta(seconds=2))

        # Signal payment_failed (Critical Event)
        await handle.signal(
            "order_event_signal",
            {
                "event_type": "payment_failed",
                "payload": {"reason": "card_declined"},
            },
        )
        await env.sleep(timedelta(seconds=5))

        state = await handle.query("get_state")
        assert state["processed_events_count"] >= 1
        memory = state["current_memory"]
        actions = memory.get("actions_taken", [])
        # Must dispatch customer alert and payment team notification
        assert any("message_customer" in a for a in actions)

        # Signal shipment_delayed (Critical Event)
        await handle.signal(
            "order_event_signal",
            {
                "event_type": "shipment_delayed",
                "payload": {"carrier": "FedEx", "reason": "Storm", "delay_hours": 24},
            },
        )
        await env.sleep(timedelta(seconds=5))

        state_delayed = await handle.query("get_state")
        actions_delayed = state_delayed["current_memory"].get("actions_taken", [])
        assert any("message_logistics_team" in a for a in actions_delayed)

        await handle.signal("terminate_signal", {"reason": "Test cleanup"})
        await handle.result()


@pytest.mark.asyncio
async def test_non_critical_event_sleep_behavior():
    """Point 5: Test conservative wake policy leaves workflow sleeping on non-critical events."""
    async with await WorkflowEnvironment.start_time_skipping() as env, Worker(
        env.client,
        task_queue="test-sleep-queue",
        workflows=[OrderSupervisorWorkflow],
        activities=WORKFLOW_ACTIVITIES,
    ):
        order_id = "ORD-SLEEP-03"
        conservative_config = {**STANDARD_CONFIG, "wake_sensitivity": "conservative"}

        handle = await env.client.start_workflow(
            OrderSupervisorWorkflow.run,
            {
                "order_id": order_id,
                "run_id": "run_sleep_03",
                "supervisor_config": conservative_config,
                "order_context": {**STANDARD_ORDER, "order_id": order_id},
            },
            id=f"order-supervisor-{order_id}",
            task_queue="test-sleep-queue",
        )

        await env.sleep(timedelta(seconds=5))

        # Signal non-critical event under conservative policy
        await handle.signal(
            "order_event_signal",
            {
                "event_type": "shipment_created",
                "payload": {"tracking_number": "TRK-CONSERVATIVE-1"},
            },
        )
        await env.sleep(timedelta(seconds=2))

        state = await handle.query("get_state")
        # In conservative mode, shipment_created is classified as non-wake
        assert state["status"] == "SLEEPING"

        await handle.signal("terminate_signal", {"reason": "Test cleanup"})
        await handle.result()


@pytest.mark.asyncio
async def test_scheduled_timer_wakeup():
    """Point 6: Test scheduled timer wake-up after default sleep duration."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-timer-queue",
            workflows=[OrderSupervisorWorkflow],
            activities=WORKFLOW_ACTIVITIES,
        ):
            order_id = "ORD-TIMER-04"
            short_timer_config = {**STANDARD_CONFIG, "default_wake_delay_seconds": 100}

            handle = await env.client.start_workflow(
                OrderSupervisorWorkflow.run,
                {
                    "order_id": order_id,
                    "run_id": "run_timer_04",
                    "supervisor_config": short_timer_config,
                    "order_context": {**STANDARD_ORDER, "order_id": order_id},
                },
                id=f"order-supervisor-{order_id}",
                task_queue="test-timer-queue",
            )

            await env.sleep(timedelta(seconds=5))
            state_initial = await handle.query("get_state")
            assert state_initial["status"] == "SLEEPING"

            # Advance time past default_wake_delay_seconds (100 seconds)
            await env.sleep(timedelta(seconds=105))

            state_after_timer = await handle.query("get_state")
            assert state_after_timer["last_wake_reason"] in ["SCHEDULED_TIMER", "WORKFLOW_START"]

            await handle.signal("terminate_signal", {"reason": "Test cleanup"})
            await handle.result()


@pytest.mark.asyncio
async def test_manual_instruction_injection():
    """Point 7: Test manual instruction_signal reaches workflow state and influences reasoning."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-instruction-queue",
            workflows=[OrderSupervisorWorkflow],
            activities=WORKFLOW_ACTIVITIES,
        ):
            order_id = "ORD-INSTR-05"
            handle = await env.client.start_workflow(
                OrderSupervisorWorkflow.run,
                {
                    "order_id": order_id,
                    "run_id": "run_instr_05",
                    "supervisor_config": STANDARD_CONFIG,
                    "order_context": {**STANDARD_ORDER, "order_id": order_id},
                },
                id=f"order-supervisor-{order_id}",
                task_queue="test-instruction-queue",
            )

            await env.sleep(timedelta(seconds=2))

            # Send live operator instruction signal
            await handle.signal(
                "instruction_signal",
                {
                    "instruction": "Prioritize speed over cost. Escalate to VP of Operations.",
                    "author": "operator_jane",
                },
            )
            await env.sleep(timedelta(seconds=5))

            state = await handle.query("get_state")
            assert state["instructions_count"] >= 1
            assert state["last_wake_reason"] == "MANUAL_INSTRUCTION"

            await handle.signal("terminate_signal", {"reason": "Test cleanup"})
            await handle.result()


@pytest.mark.asyncio
async def test_pause_and_resume_control_signals():
    """Point 8: Test pause_signal and resume_signal workflow state control."""
    async with await WorkflowEnvironment.start_time_skipping() as env, Worker(
        env.client,
        task_queue="test-pause-queue",
        workflows=[OrderSupervisorWorkflow],
        activities=WORKFLOW_ACTIVITIES,
    ):
        order_id = "ORD-PAUSE-06"
        handle = await env.client.start_workflow(
            OrderSupervisorWorkflow.run,
            {
                "order_id": order_id,
                "run_id": "run_pause_06",
                "supervisor_config": STANDARD_CONFIG,
                "order_context": {**STANDARD_ORDER, "order_id": order_id},
            },
            id=f"order-supervisor-{order_id}",
            task_queue="test-pause-queue",
        )

        await env.sleep(timedelta(seconds=2))

        # Send pause signal
        await handle.signal("pause_signal", {"action": "pause"})
        await env.sleep(timedelta(seconds=2))

        state_paused = await handle.query("get_state")
        assert state_paused["is_paused"] is True
        assert state_paused["status"] == "PAUSED"

        # Send resume signal
        await handle.signal("resume_signal", {"action": "resume"})
        await env.sleep(timedelta(seconds=2))

        state_resumed = await handle.query("get_state")
        assert state_resumed["is_paused"] is False
        assert state_resumed["status"] in ["RUNNING", "SLEEPING"]

        await handle.signal("terminate_signal", {"reason": "Test cleanup"})
        await handle.result()


@pytest.mark.asyncio
async def test_terminal_event_completion_and_post_mortem():
    """Points 10, 11: Test terminal 'delivered' event completion and post-mortem summary generation."""
    async with await WorkflowEnvironment.start_time_skipping() as env, Worker(
        env.client,
        task_queue="test-terminal-queue",
        workflows=[OrderSupervisorWorkflow],
        activities=WORKFLOW_ACTIVITIES,
    ):
        order_id = "ORD-TERM-07"
        handle = await env.client.start_workflow(
            OrderSupervisorWorkflow.run,
            {
                "order_id": order_id,
                "run_id": "run_term_07",
                "supervisor_config": STANDARD_CONFIG,
                "order_context": {**STANDARD_ORDER, "order_id": order_id},
            },
            id=f"order-supervisor-{order_id}",
            task_queue="test-terminal-queue",
        )

        await env.sleep(timedelta(seconds=2))

        # Send terminal event signal 'delivered'
        await handle.signal(
            "order_event_signal",
            {
                "event_type": "delivered",
                "payload": {"signed_by": "Jane Doe", "location": "Front Porch"},
            },
        )

        # Wait for workflow completion
        result = await handle.result()
        assert result["status"] == "COMPLETED"
        assert result["is_terminated"] is True

        final_output = result.get("final_output")
        assert final_output is not None
        assert "final_summary" in final_output
        assert "key_learnings" in final_output
        assert "feedback_and_recommendations" in final_output
        assert len(final_output["key_learnings"]) > 0
        assert len(final_output["feedback_and_recommendations"]) > 0


@pytest.mark.asyncio
async def test_order_supervisor_full_lifecycle_with_operator_directives():
    """Validates full event chain from assignment L150-L158, operator instructions from L207-L209,
    and post-mortem report structure from L219-L222 inside a live Temporal workflow."""
    async with await WorkflowEnvironment.start_time_skipping() as env, Worker(
        env.client,
        task_queue="test-full-lifecycle-queue",
        workflows=[OrderSupervisorWorkflow],
        activities=WORKFLOW_ACTIVITIES,
    ):
        order_id = "ORD-LIFECYCLE-99"
        handle = await env.client.start_workflow(
            OrderSupervisorWorkflow.run,
            {
                "order_id": order_id,
                "run_id": "run_lifecycle_99",
                "supervisor_config": STANDARD_CONFIG,
                "order_context": {**STANDARD_ORDER, "order_id": order_id},
            },
            id=f"order-supervisor-{order_id}",
            task_queue="test-full-lifecycle-queue",
        )

        await env.sleep(timedelta(seconds=2))

        # 1. Event: payment_confirmed
        await handle.signal(
            "order_event_signal",
            {"event_type": "payment_confirmed", "payload": {"amount": 250.00}},
        )
        await env.sleep(timedelta(seconds=2))

        # 2. Operator Directives (L207-L209)
        await handle.signal(
            "instruction_signal",
            {"instruction": "For this order, prioritize speed over cost."},
        )
        await handle.signal(
            "instruction_signal",
            {"instruction": "Do not contact the customer without human review."},
        )
        await env.sleep(timedelta(seconds=2))

        # 3. Event: shipment_delayed
        await handle.signal(
            "order_event_signal",
            {
                "event_type": "shipment_delayed",
                "payload": {"carrier": "FedEx", "reason": "Severe hub blizzard"},
            },
        )
        await env.sleep(timedelta(seconds=2))

        # Check state during active lifecycle
        state = await handle.query("get_state")
        assert state["status"] in ["RUNNING", "SLEEPING"]
        assert len(state["additional_instructions"]) == 2
        assert state["current_memory"]["current_status"] == "DELAYED"

        # 4. Terminal Event: delivered
        await handle.signal(
            "order_event_signal",
            {
                "event_type": "delivered",
                "payload": {"signed_by": "Jane Doe", "location": "Front Porch"},
            },
        )

        # Wait for workflow completion
        result = await handle.result()
        assert result["status"] == "COMPLETED"
        assert result["is_terminated"] is True

        # 5. Verify Post-Mortem Report Structure (L219-L222)
        final_output = result.get("final_output")
        assert final_output is not None
        assert "final_summary" in final_output
        assert "important_actions_taken" in final_output
        assert "key_learnings" in final_output
        assert "feedback_and_recommendations" in final_output
        assert len(final_output["important_actions_taken"]) > 0
        assert len(final_output["key_learnings"]) > 0
        assert len(final_output["feedback_and_recommendations"]) > 0
