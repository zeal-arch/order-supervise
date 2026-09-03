from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from temporal.activities.agent import execute_agent_step_activity
    from temporal.activities.memory import update_compact_memory_activity
    from temporal.activities.persistence import (
        persist_activity_log_activity,
        persist_run_state_activity,
    )
    from temporal.activities.wake_policy import evaluate_wake_policy_activity
    from temporal.workflows.state import WorkflowOrderState


@workflow.defn
class OrderSupervisorWorkflow:
    def __init__(self) -> None:
        self._state: WorkflowOrderState | None = None
        self._new_event_or_instruction_received = False
        self._trigger_wake = False

    @workflow.signal(name="order_event_signal")
    def receive_order_event(self, event_data: Any) -> None:
        """Signal handler for incoming order domain events."""
        if self._state:
            event_id = getattr(event_data, "event_id", None) or (event_data.get("event_id") if isinstance(event_data, dict) else "")
            event_type = getattr(event_data, "event_type", None) or (event_data.get("event_type") if isinstance(event_data, dict) else "")
            payload = getattr(event_data, "payload", None) if not isinstance(event_data, dict) else event_data.get("payload", {})
            source = getattr(event_data, "source", None) or (event_data.get("source") if isinstance(event_data, dict) else "simulator")
            timestamp = getattr(event_data, "timestamp", None) or (event_data.get("timestamp") if isinstance(event_data, dict) else None)

            self._state.pending_events.append({
                "event_id": event_id or f"evt_{len(self._state.pending_events)+1}",
                "event_type": event_type,
                "payload": payload or {},
                "source": source or "simulator",
                "timestamp": timestamp,
            })
            self._new_event_or_instruction_received = True

    @workflow.signal(name="instruction_signal")
    def receive_instruction(self, instruction_data: Any) -> None:
        """Signal handler for dynamic operator instructions."""
        if self._state:
            instruction = getattr(instruction_data, "instruction", None) or (instruction_data.get("instruction") if isinstance(instruction_data, dict) else "")
            author = getattr(instruction_data, "author", None) or (instruction_data.get("author") if isinstance(instruction_data, dict) else "operator")
            timestamp = getattr(instruction_data, "timestamp", None) or (instruction_data.get("timestamp") if isinstance(instruction_data, dict) else None)

            self._state.additional_instructions.append({
                "instruction": instruction,
                "author": author or "operator",
                "timestamp": timestamp,
            })
            self._new_event_or_instruction_received = True
            self._trigger_wake = True

    @workflow.signal(name="pause_signal")
    def pause_workflow(self, data: Any = None) -> None:
        """Signal handler to pause the supervisor."""
        if self._state:
            self._state.is_paused = True
            self._state.status = "PAUSED"

    @workflow.signal(name="resume_signal")
    def resume_workflow(self, data: Any = None) -> None:
        """Signal handler to resume the supervisor."""
        if self._state:
            self._state.is_paused = False
            self._state.status = "RUNNING"
            self._trigger_wake = True

    @workflow.signal(name="terminate_signal")
    def terminate_workflow(self, data: Any = None) -> None:
        """Signal handler to terminate the workflow immediately."""
        if self._state:
            self._state.is_terminated = True
            self._state.status = "TERMINATED"
            self._trigger_wake = True

    @workflow.query(name="get_state")
    def get_state(self) -> dict[str, Any]:
        """Query handler for fetching the live in-memory state."""
        return self._state.to_dict() if self._state else {}

    @workflow.run
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Long-running workflow execution managing the complete order supervisor lifecycle."""
        order_id = input_data["order_id"]
        run_id = input_data.get("run_id", f"run_{order_id}")
        supervisor_config = input_data.get("supervisor_config", {})
        order_context = input_data.get("order_context", {})
        initial_instructions = input_data.get("initial_instructions", [])

        initial_memory = input_data.get("initial_memory")

        # Initialize workflow deterministic state
        self._state = WorkflowOrderState(
            order_id=order_id,
            run_id=run_id,
            status="RUNNING",
            supervisor_config=supervisor_config,
            order_context=order_context,
            current_memory=initial_memory or {
                "order_id": order_id,
                "current_status": "CREATED",
                "customer_name": order_context.get("customer_name"),
                "rolling_summary": f"Workflow initialized for order {order_id}.",
                "actions_taken": [],
                "key_events_summary": ["Workflow start"],
            },
            additional_instructions=[{"instruction": i} for i in initial_instructions],
            last_wake_reason="WORKFLOW_START" if not initial_memory else "CONTINUE_AS_NEW",
        )

        activity_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )

        # Initial wake step
        current_wake_reason = "WORKFLOW_START"
        sleep_seconds = supervisor_config.get("default_wake_delay_seconds", 3600)

        while not self._state.is_terminated:
            # Check pause state
            if self._state.is_paused:
                self._state.status = "PAUSED"
                await workflow.execute_activity(
                    persist_run_state_activity,
                    {
                        "run_id": self._state.run_id,
                        "status": "PAUSED",
                        "memory": self._state.current_memory,
                        "last_wake_reason": current_wake_reason,
                    },
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=activity_retry_policy,
                )
                await workflow.wait_condition(lambda: not self._state.is_paused or self._state.is_terminated)
                if self._state.is_terminated:
                    break
                self._state.status = "RUNNING"
                current_wake_reason = "RESUMED"

            # Check if there are pending events to classify
            should_run_agent = False
            events_to_process = list(self._state.pending_events)
            self._state.pending_events.clear()
            self._new_event_or_instruction_received = False
            self._trigger_wake = False

            if current_wake_reason in ["WORKFLOW_START", "SCHEDULED_TIMER", "MANUAL_INSTRUCTION", "RESUMED"]:
                should_run_agent = True
            elif events_to_process:
                # Evaluate ALL pending events through the wake classifier.
                # Wake if ANY event requires it — this prevents a critical event
                # (e.g. shipment_delayed) from being missed when a non-critical
                # event (e.g. payment_confirmed) arrives last in the queue.
                for candidate_event in events_to_process:
                    wake_decision = await workflow.execute_activity(
                        evaluate_wake_policy_activity,
                        {
                            "event_type": candidate_event.get("event_type"),
                            "payload": candidate_event.get("payload", {}),
                            "sensitivity": supervisor_config.get("wake_sensitivity", "balanced"),
                        },
                        start_to_close_timeout=timedelta(seconds=10),
                        retry_policy=activity_retry_policy,
                    )
                    if wake_decision.get("should_wake", False):
                        should_run_agent = True
                        current_wake_reason = "EVENT_SIGNAL"
                        workflow.logger.info(
                            f"Event '{candidate_event.get('event_type')}' triggered wake "
                            f"(batch size: {len(events_to_process)})."
                        )
                        break  # One critical event is sufficient; no need to check the rest

                if not should_run_agent:
                    workflow.logger.info(
                        f"All {len(events_to_process)} queued event(s) classified as non-wake. Remaining asleep."
                    )

            if should_run_agent:
                self._state.status = "RUNNING"

                # Execute agent reasoning & action selection step
                agent_result = await workflow.execute_activity(
                    execute_agent_step_activity,
                    {
                        "order_context": self._state.order_context,
                        "current_memory": self._state.current_memory,
                        "recent_events": events_to_process,
                        "additional_instructions": self._state.additional_instructions,
                        "supervisor_config": self._state.supervisor_config,
                        "wake_reason": current_wake_reason,
                    },
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=activity_retry_policy,
                )

                # Persist tool execution records
                for act in agent_result.get("actions_executed", []):
                    await workflow.execute_activity(
                        persist_activity_log_activity,
                        {
                            "run_id": self._state.run_id,
                            "activity_type": act.get("tool"),
                            "reasoning": agent_result.get("reasoning"),
                            "payload": act.get("args", {}),
                            "result": act.get("result", {}),
                            "status": "SUCCESS",
                        },
                        start_to_close_timeout=timedelta(seconds=10),
                        retry_policy=activity_retry_policy,
                    )

                # Update & compact memory context
                updated_memory = await workflow.execute_activity(
                    update_compact_memory_activity,
                    {
                        "previous_memory": self._state.current_memory,
                        "recent_events": events_to_process,
                        "actions_taken": agent_result.get("actions_executed", []),
                        "reasoning": agent_result.get("reasoning", ""),
                        "order_context": self._state.order_context,
                    },
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=activity_retry_policy,
                )
                self._state.current_memory = updated_memory

                # Move events to processed history
                self._state.processed_events.extend(events_to_process)

                # Update sleep timing
                sleep_seconds = agent_result.get("next_sleep_seconds", 3600)

                # Check for terminal completion
                if agent_result.get("is_terminal", False):
                    self._state.is_terminated = True
                    self._state.status = "COMPLETED"
                    self._state.final_output = agent_result.get("final_output")
                    break

            # Calculate next wake timestamp string (workflow-safe deterministic time)
            next_wake_time = workflow.now() + timedelta(seconds=sleep_seconds)
            self._state.next_wake_at = next_wake_time.isoformat()
            self._state.status = "SLEEPING"
            self._state.last_wake_reason = current_wake_reason

            # Persist state to DB
            await workflow.execute_activity(
                persist_run_state_activity,
                {
                    "run_id": self._state.run_id,
                    "status": "SLEEPING",
                    "memory": self._state.current_memory,
                    "next_wake_at": self._state.next_wake_at,
                    "last_wake_reason": current_wake_reason,
                    "final_output": self._state.final_output,
                },
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=activity_retry_policy,
            )

            # Check if continue_as_new is recommended to truncate long history logs
            if (workflow.info().is_continue_as_new_suggested() or len(self._state.processed_events) >= 100) and not self._state.is_terminated:
                workflow.logger.info(f"History threshold reached. Continuing as new for order {order_id}...")
                workflow.continue_as_new(
                    {
                        "order_id": self._state.order_id,
                        "run_id": self._state.run_id,
                        "supervisor_config": self._state.supervisor_config,
                        "order_context": self._state.order_context,
                        "initial_instructions": [i.get("instruction") for i in self._state.additional_instructions if isinstance(i, dict)],
                        "initial_memory": self._state.current_memory,
                    }
                )

            # Wait for either incoming signal OR sleep timer expiration (non-polling!)
            wake_on_signal = False
            try:
                await workflow.wait_condition(
                    lambda: self._new_event_or_instruction_received or self._trigger_wake or self._state.is_terminated,
                    timeout=timedelta(seconds=sleep_seconds),
                )
                wake_on_signal = True
            except TimeoutError:
                # Timer fired naturally
                wake_on_signal = False

            if wake_on_signal:
                if self._state.is_terminated:
                    break
                current_wake_reason = "EVENT_SIGNAL" if self._state.pending_events else "MANUAL_INSTRUCTION"
            else:
                current_wake_reason = "SCHEDULED_TIMER"

        # Final Post-Mortem Step upon completion or manual termination
        terminal_status = self._state.status if self._state.status in ["COMPLETED", "TERMINATED"] else "COMPLETED"
        if not self._state.final_output:
            self._state.final_output = {
                "final_summary": f"Order {order_id} workflow concluded with status {terminal_status}.",
                "important_actions_taken": self._state.current_memory.get("actions_taken", []),
                "key_learnings": [
                    "Workflow executed with deterministic signal-driven sleep/wake cycle.",
                    "All activities and memory snapshots synced cleanly to persistence.",
                ],
                "feedback_and_recommendations": [
                    "System successfully demonstrated autonomous supervision end-to-end.",
                ],
                "completed_at": workflow.now().isoformat(),
            }

        await workflow.execute_activity(
            persist_run_state_activity,
            {
                "run_id": self._state.run_id,
                "status": terminal_status,
                "memory": self._state.current_memory,
                "next_wake_at": None,
                "last_wake_reason": "TERMINAL_EVENT",
                "final_output": self._state.final_output,
            },
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=activity_retry_policy,
        )

        return self._state.to_dict()
