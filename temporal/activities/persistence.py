import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.future import select
from temporalio import activity

import apps.api.app.db.database as db_module
from apps.api.app.models.activity import ActivityModel
from apps.api.app.models.run import RunModel

logger = logging.getLogger("temporal.activities.persistence")


async def execute_with_db_retry(func):
    """Executes a DB operation, falling back to SQLite if primary DB (e.g. Postgres) authentication fails."""
    try:
        async with db_module.AsyncSessionLocal() as db:
            return await func(db)
    except Exception as e:
        logger.warning(f"Primary database connection failed in worker ({e}). Switching to SQLite fallback...")
        db_module.set_sqlite_fallback()
        async with db_module.AsyncSessionLocal() as db:
            return await func(db)


@activity.defn
async def persist_activity_log_activity(input_data: dict[str, Any]) -> dict[str, Any]:
    """Persists an executed agent tool activity into the database."""
    run_id = input_data.get("run_id")
    activity_type = input_data.get("activity_type", "unknown")
    reasoning = input_data.get("reasoning", "")
    payload = input_data.get("payload", {})
    result = input_data.get("result", {})
    status = input_data.get("status", "SUCCESS")

    act_id = f"act_{uuid.uuid4().hex[:8]}"

    async def _operation(db):
        res = await db.execute(select(RunModel).where((RunModel.id == run_id) | (RunModel.workflow_id == run_id)))
        run = res.scalar_one_or_none()
        if run:
            db_activity = ActivityModel(
                id=act_id,
                run_id=run.id,
                activity_type=activity_type,
                reasoning=reasoning,
                payload=payload,
                result=result,
                status=status,
                created_at=datetime.now(timezone.utc),
            )
            db.add(db_activity)
            await db.commit()
            logger.info(f"💾 [PERSIST_ACTIVITY] Saved {activity_type} for run {run.id}")

    try:
        await execute_with_db_retry(_operation)
    except Exception as e:
        logger.error(f"Failed to persist activity log even after fallback: {e}")

    return {"status": "persisted", "activity_id": act_id}


@activity.defn
async def persist_run_state_activity(input_data: dict[str, Any]) -> dict[str, Any]:
    """Updates the run's current memory, status, next wake timestamp, and post-mortem output in the database."""
    run_id = input_data.get("run_id")
    status = input_data.get("status")
    memory = input_data.get("memory")
    next_wake_at_iso = input_data.get("next_wake_at")
    last_wake_reason = input_data.get("last_wake_reason")
    final_output = input_data.get("final_output")

    async def _operation(db):
        res = await db.execute(select(RunModel).where((RunModel.id == run_id) | (RunModel.workflow_id == run_id)))
        run = res.scalar_one_or_none()
        if run:
            if status:
                run.status = status
            if memory:
                run.current_memory = memory
            if next_wake_at_iso:
                try:
                    run.next_wake_at = datetime.fromisoformat(next_wake_at_iso)
                except Exception:
                    pass
            if last_wake_reason:
                run.last_wake_reason = last_wake_reason
            if final_output:
                run.final_output = final_output
                run.completed_at = datetime.now(timezone.utc)

            run.updated_at = datetime.now(timezone.utc)
            db.add(run)
            await db.commit()
            logger.info(f"💾 [PERSIST_STATE] Updated state for run {run.id} (Status: {status})")

    try:
        await execute_with_db_retry(_operation)
    except Exception as e:
        logger.error(f"Failed to persist run state even after fallback: {e}")

    return {"status": "updated"}
