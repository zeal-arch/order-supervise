import asyncio
import logging

from temporalio.worker import Worker

from apps.api.app.config import settings
from temporal.activities.agent import execute_agent_step_activity
from temporal.activities.memory import update_compact_memory_activity
from temporal.activities.persistence import (
    persist_activity_log_activity,
    persist_run_state_activity,
)
from temporal.activities.wake_policy import evaluate_wake_policy_activity
from temporal.client import get_temporal_client

# Import workflow and activities
from temporal.workflows.order_supervisor import OrderSupervisorWorkflow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("temporal.worker")


async def run_worker():
    print("\n" + "=" * 76)
    print("  ORDER SUPERVISOR - TEMPORAL WORKER ENGINE")
    print("=" * 76)
    logger.info("Connecting to Temporal Server at localhost:7233...")
    client = await get_temporal_client()
    logger.info("Connected successfully to Temporal.")

    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[OrderSupervisorWorkflow],
        activities=[
            evaluate_wake_policy_activity,
            execute_agent_step_activity,
            update_compact_memory_activity,
            persist_activity_log_activity,
            persist_run_state_activity,
        ],
    )

    print("-" * 76)
    print(f"  Task Queue:   {settings.TEMPORAL_TASK_QUEUE}")
    print(f"  Namespace:    {settings.TEMPORAL_NAMESPACE}")
    print("  Workflow:     OrderSupervisorWorkflow")
    print("  Status:       ACTIVE & LISTENING FOR SIGNALS")
    print("=" * 76 + "\n")

    try:
        await worker.run()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n" + "=" * 76)
        print("  Temporal Worker stopped cleanly.")
        print("=" * 76 + "\n")
