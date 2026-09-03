import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from apps.api.app.models.event import EventModel
from apps.api.app.models.run import RunModel
from apps.api.app.models.supervisor import SupervisorModel
from apps.api.app.schemas.event import EventCreate
from apps.api.app.schemas.instruction import InstructionCreate
from apps.api.app.schemas.run import RunCreate
from apps.api.app.services.temporal import TemporalService
from domain.enums import OrderStatus, RunStatus
from domain.models import OrderContext, OrderItem


class RunService:
    @staticmethod
    async def create_run(db: AsyncSession, data: RunCreate) -> RunModel:
        workflow_id = f"order-supervisor-{data.order_id}"

        # Check if an existing run already exists for this order
        res_existing = await db.execute(select(RunModel).where((RunModel.order_id == data.order_id) | (RunModel.workflow_id == workflow_id)))
        if res_existing.scalar_one_or_none():
            raise ValueError(f"An order supervisor run for order '{data.order_id}' already exists.")

        run_id = f"run_{uuid.uuid4().hex[:8]}"

        # Fetch supervisor config
        supervisor_dict = {}
        if data.supervisor_id:
            res = await db.execute(select(SupervisorModel).where(SupervisorModel.id == data.supervisor_id))
            sup = res.scalar_one_or_none()
            if sup:
                supervisor_dict = {
                    "id": sup.id,
                    "name": sup.name,
                    "base_instruction": sup.base_instruction,
                    "available_tools": sup.available_tools,
                    "default_wake_delay_seconds": sup.default_wake_delay_seconds,
                    "wake_sensitivity": sup.wake_sensitivity,
                    "model_name": sup.model_name,
                }

        # If order_context not provided, build a clean default
        if not data.order_context:
            order_context = OrderContext(
                order_id=data.order_id,
                customer_name="Alex Johnson",
                customer_email="alex.j@example.com",
                customer_phone="+1-555-0199",
                shipping_address="742 Evergreen Terrace, Springfield, OR 97477",
                items=[
                    OrderItem(sku="SKU-TECH-01", name="Wireless Noise-Canceling Headphones", quantity=1, unit_price=149.99),
                    OrderItem(sku="SKU-ACC-02", name="Braided USB-C Fast Charger Cable", quantity=2, unit_price=19.99),
                ],
                total_amount=189.97,
                status=OrderStatus.CREATED,
            ).model_dump(mode="json")
        else:
            order_context = data.order_context.model_dump(mode="json")

        initial_instructions_list = []
        if data.initial_instructions:
            for instr in data.initial_instructions:
                initial_instructions_list.append({
                    "instruction": instr,
                    "author": "system_init",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        initial_memory = {
            "order_id": data.order_id,
            "current_status": "CREATED",
            "customer_name": order_context.get("customer_name"),
            "customer_email": order_context.get("customer_email"),
            "items_summary": f"{len(order_context.get('items', []))} items ($ {order_context.get('total_amount')})",
            "payment_status": "pending",
            "shipment_status": "not_shipped",
            "key_events_summary": ["Order initialized"],
            "actions_taken": [],
            "pending_concerns": [],
            "active_instructions": [i["instruction"] for i in initial_instructions_list],
            "rolling_summary": f"Order {data.order_id} created for {order_context.get('customer_name')}. Awaiting payment confirmation.",
        }

        run = RunModel(
            id=run_id,
            order_id=data.order_id,
            supervisor_id=data.supervisor_id,
            workflow_id=workflow_id,
            status=RunStatus.INITIALIZING.value,
            order_context=order_context,
            current_memory=initial_memory,
            additional_instructions=initial_instructions_list,
            started_at=datetime.now(timezone.utc),
        )
        db.add(run)

        # Record initial event
        initial_event = EventModel(
            id=f"evt_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            event_type="order_created",
            payload=order_context,
            source="system",
            requires_wake=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(initial_event)

        await db.commit()
        await db.refresh(run)

        # Trigger Temporal workflow
        try:
            await TemporalService.start_order_workflow(
                order_id=data.order_id,
                run_id=run_id,
                supervisor_config=supervisor_dict,
                order_context=order_context,
                initial_instructions=[i["instruction"] for i in initial_instructions_list],
            )
        except Exception as e:
            # If Temporal is offline in standalone testing, don't crash the API creation
            print(f"Warning: Temporal workflow start deferred/failed: {e}")

        return run

    @staticmethod
    async def get_all_runs(db: AsyncSession) -> list[RunModel]:
        result = await db.execute(select(RunModel).order_by(RunModel.started_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_run_by_id(db: AsyncSession, run_id: str) -> RunModel | None:
        result = await db.execute(
            select(RunModel)
            .options(
                selectinload(RunModel.events),
                selectinload(RunModel.activities),
            )
            .where((RunModel.id == run_id) | (RunModel.workflow_id == run_id) | (RunModel.order_id == run_id))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def add_event(db: AsyncSession, run_id: str, event_in: EventCreate) -> EventModel:
        run = await RunService.get_run_by_id(db, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        event = EventModel(
            id=event_id,
            run_id=run.id,
            event_type=event_in.event_type.value,
            payload=event_in.payload,
            source=event_in.source,
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

        # Send signal to Temporal workflow
        try:
            await TemporalService.send_event_signal(
                workflow_id=run.workflow_id,
                event_data={
                    "event_id": event.id,
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "source": event.source,
                    "timestamp": event.created_at.isoformat(),
                },
                run_model=run,
            )
        except Exception as e:
            print(f"Warning: Temporal signal sending failed: {e}")

        return event

    @staticmethod
    async def add_instruction(db: AsyncSession, run_id: str, instr_in: InstructionCreate) -> dict[str, Any]:
        run = await RunService.get_run_by_id(db, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        instruction_payload = {
            "instruction": instr_in.instruction,
            "author": instr_in.author or "operator",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        instructions_list = list(run.additional_instructions or [])
        instructions_list.append(instruction_payload)
        run.additional_instructions = instructions_list
        db.add(run)
        await db.commit()

        # Send instruction signal to Temporal workflow
        try:
            await TemporalService.send_instruction_signal(
                workflow_id=run.workflow_id,
                instruction_data=instruction_payload,
                run_model=run,
            )
        except Exception as e:
            print(f"Warning: Temporal instruction signal failed: {e}")

        return instruction_payload

    @staticmethod
    async def pause_run(db: AsyncSession, run_id: str) -> RunModel:
        run = await RunService.get_run_by_id(db, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        run.status = RunStatus.PAUSED.value
        db.add(run)
        await db.commit()
        try:
            await TemporalService.send_pause_signal(run.workflow_id)
        except Exception as e:
            print(f"Temporal pause error: {e}")
        return run

    @staticmethod
    async def resume_run(db: AsyncSession, run_id: str) -> RunModel:
        run = await RunService.get_run_by_id(db, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        run.status = RunStatus.RUNNING.value
        db.add(run)
        await db.commit()
        try:
            await TemporalService.send_resume_signal(run.workflow_id)
        except Exception as e:
            print(f"Temporal resume error: {e}")
        return run

    @staticmethod
    async def terminate_run(db: AsyncSession, run_id: str) -> RunModel:
        run = await RunService.get_run_by_id(db, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        run.status = RunStatus.TERMINATED.value
        run.completed_at = datetime.now(timezone.utc)
        db.add(run)
        await db.commit()
        try:
            await TemporalService.terminate_workflow(run.workflow_id, reason="User terminated from API/UI")
        except Exception as e:
            print(f"Temporal terminate error: {e}")
        return run
