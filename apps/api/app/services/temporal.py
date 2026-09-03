import logging
from typing import Any

from apps.api.app.config import settings
from temporal.client import get_temporal_client
from temporal.workflows.signals import (
    ControlSignalPayload,
    InstructionSignalPayload,
    OrderEventSignalPayload,
)

logger = logging.getLogger(__name__)


class TemporalService:
    @staticmethod
    async def start_order_workflow(
        order_id: str,
        run_id: str,
        supervisor_config: dict[str, Any],
        order_context: dict[str, Any],
        initial_instructions: list[str],
    ) -> str:
        """Starts a long-running OrderSupervisorWorkflow instance for the given order."""
        client = await get_temporal_client()
        workflow_id = f"order-supervisor-{order_id}"

        input_data = {
            "run_id": run_id,
            "order_id": order_id,
            "supervisor_config": supervisor_config,
            "order_context": order_context,
            "initial_instructions": initial_instructions,
        }

        logger.info(f"Starting Temporal workflow ID={workflow_id} on task queue={settings.TEMPORAL_TASK_QUEUE}")
        handle = await client.start_workflow(
            "OrderSupervisorWorkflow",
            input_data,
            id=workflow_id,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
        )
        return handle.id

    @staticmethod
    async def send_event_signal(workflow_id: str, event_data: dict[str, Any]) -> None:
        """Sends an incoming event signal to the running workflow."""
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        payload = OrderEventSignalPayload(
            event_id=event_data.get("event_id", ""),
            event_type=event_data.get("event_type", ""),
            payload=event_data.get("payload", {}),
            source=event_data.get("source", "simulator"),
            timestamp=event_data.get("timestamp"),
        )
        await handle.signal("order_event_signal", payload)
        logger.info(f"Sent order_event_signal to workflow {workflow_id}")

    @staticmethod
    async def send_instruction_signal(workflow_id: str, instruction_data: dict[str, Any]) -> None:
        """Sends a runtime instruction signal to the running workflow."""
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        payload = InstructionSignalPayload(
            instruction=instruction_data.get("instruction", ""),
            author=instruction_data.get("author", "operator"),
            timestamp=instruction_data.get("timestamp"),
        )
        await handle.signal("instruction_signal", payload)
        logger.info(f"Sent instruction_signal to workflow {workflow_id}")

    @staticmethod
    async def send_pause_signal(workflow_id: str) -> None:
        """Sends a pause/interrupt signal to the running workflow."""
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("pause_signal", ControlSignalPayload(action="pause"))
        logger.info(f"Sent pause_signal to workflow {workflow_id}")

    @staticmethod
    async def send_resume_signal(workflow_id: str) -> None:
        """Sends a resume signal to the paused workflow."""
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("resume_signal", ControlSignalPayload(action="resume"))
        logger.info(f"Sent resume_signal to workflow {workflow_id}")

    @staticmethod
    async def terminate_workflow(workflow_id: str, reason: str = "User terminated") -> None:
        """Signals the workflow to gracefully shut down and produce end-of-run outputs, or force-terminates."""
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        try:
            await handle.signal("terminate_signal", ControlSignalPayload(action="terminate", reason=reason))
            logger.info(f"Sent terminate_signal to workflow {workflow_id}")
        except Exception as e:
            logger.warning(f"Could not signal terminate, calling client.terminate: {e}")
            await handle.terminate(reason=reason)


