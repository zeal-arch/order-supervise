import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import logging

from sqlalchemy.future import select

from apps.api.app.db.database import (
    AsyncSessionLocal,
    create_db_tables,
    init_db_engines,
)
from apps.api.app.models.activity import ActivityModel
from apps.api.app.models.event import EventModel
from apps.api.app.models.run import RunModel
from apps.api.app.models.supervisor import SupervisorModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database.seed")

DEFAULT_SUPERVISORS = [
    {
        "id": "sup_standard_retail",
        "name": "Standard E-Commerce Supervisor",
        "description": "Monitors retail order progress, handles fulfillment dispatch, and updates customers on routine milestones.",
        "base_instruction": "You are a dependable order operations agent. Ensure timely fulfillment, notify customers on delays, and coordinate with couriers.",
        "available_tools": [
            "message_fulfillment_team",
            "message_payments_team",
            "message_logistics_team",
            "message_customer",
            "create_internal_note",
        ],
        "default_wake_delay_seconds": 3600,
        "wake_sensitivity": "balanced",
        "model_name": "gpt-4o-mini",
        "is_active": True,
    },
    {
        "id": "sup_vip_expedited",
        "name": "VIP & High-Value Order Supervisor",
        "description": "High-urgency supervisor for orders over $500. Reacts aggressively to any shipping bottleneck.",
        "base_instruction": "You oversee high-value VIP orders. Immediately escalate any delay directly to senior logistics dispatchers and maintain constant customer communication.",
        "available_tools": [
            "message_fulfillment_team",
            "message_payments_team",
            "message_logistics_team",
            "message_customer",
            "create_internal_note",
        ],
        "default_wake_delay_seconds": 1800,
        "wake_sensitivity": "aggressive",
        "model_name": "gpt-4o",
        "is_active": True,
    },
    {
        "id": "sup_fraud_returns",
        "name": "Returns & Disputed Orders Supervisor",
        "description": "Specialized supervisor handling refund requests, payment disputes, and carrier exceptions.",
        "base_instruction": "Manage return requests, verify billing discrepancies with payments team, and log all communication.",
        "available_tools": [
            "message_payments_team",
            "message_customer",
            "create_internal_note",
        ],
        "default_wake_delay_seconds": 7200,
        "wake_sensitivity": "balanced",
        "model_name": "gpt-4o-mini",
        "is_active": True,
    },
]


async def seed_data():
    logger.info("Initializing database tables...")
    init_db_engines()
    await create_db_tables()

    async with AsyncSessionLocal() as db:
        logger.info("Seeding supervisor templates...")
        for sup_data in DEFAULT_SUPERVISORS:
            existing = await db.execute(select(SupervisorModel).where(SupervisorModel.id == sup_data["id"]))
            if not existing.scalar_one_or_none():
                sup = SupervisorModel(**sup_data)
                db.add(sup)
                logger.info(f"Added supervisor template: {sup_data['name']}")

        # Seed Test Subject Run (ORD-1001) for immediate local showcase
        test_run_id = "run_demo_1001"
        existing_run = await db.execute(select(RunModel).where(RunModel.id == test_run_id))
        if not existing_run.scalar_one_or_none():
            logger.info("Seeding showcase test subject order (ORD-1001)...")
            demo_run = RunModel(
                id=test_run_id,
                order_id="ORD-1001",
                supervisor_id="sup_vip_expedited",
                workflow_id="order-supervisor-ORD-1001",
                status="SLEEPING",
                order_context={
                    "order_id": "ORD-1001",
                    "customer_name": "Sarah Connor",
                    "customer_email": "sarah@cyberdyne.io",
                    "total_amount": 499.00,
                    "currency": "USD",
                    "items": [
                        {
                            "sku": "SKU-ERG-KEY",
                            "title": "Ergonomic Split Mechanical Keyboard",
                            "quantity": 1,
                            "price": 499.00,
                        }
                    ],
                },
                current_memory={
                    "current_status": "PROCESSING",
                    "summary": "VIP order ORD-1001 initialized. Payment confirmed and warehouse dispatched. In scheduled sleep awaiting carrier scan.",
                    "milestones": {
                        "order_created": True,
                        "payment_confirmed": True,
                        "warehouse_notified": True,
                    },
                    "actions_taken": [
                        "Logged initial audit note",
                        "Dispatched warehouse fulfillment pack request [RUSH PRIORITY]",
                        "Sent payment confirmation receipt to customer",
                    ],
                },
                additional_instructions=[
                    {
                        "instruction": "For this order, prioritize speed over cost.",
                        "added_at": "2026-09-03T10:00:00Z",
                    }
                ],
                last_wake_reason="EVENT_SIGNAL",
            )
            db.add(demo_run)

            # Seed demo timeline events
            db.add(
                EventModel(
                    id="evt_demo_01",
                    run_id=test_run_id,
                    event_type="order_created",
                    payload={"amount": 499.00, "customer": "Sarah Connor"},
                    source="checkout",
                    requires_wake=True,
                )
            )
            db.add(
                EventModel(
                    id="evt_demo_02",
                    run_id=test_run_id,
                    event_type="payment_confirmed",
                    payload={"transaction_id": "tx_998811", "amount": 499.00},
                    source="stripe",
                    requires_wake=True,
                )
            )

            # Seed demo activity log
            db.add(
                ActivityModel(
                    id="act_demo_01",
                    run_id=test_run_id,
                    activity_type="execute_agent_step_activity",
                    reasoning="Payment verified for Sarah Connor ($499.00). Applied operator directive 'prioritize speed over cost'. Dispatched rush packing alert to warehouse.",
                    payload={"wake_reason": "payment_confirmed"},
                    result={
                        "actions_executed": [
                            {"tool": "message_fulfillment_team", "summary": "Notified warehouse team [RUSH PRIORITY]"},
                            {"tool": "message_customer", "summary": "Sent payment confirmation email"},
                        ]
                    },
                    status="SUCCESS",
                )
            )
            logger.info("Added test subject run: ORD-1001 (Sarah Connor)")

        await db.commit()
        logger.info("Database ready with supervisor templates and test subject order.")


if __name__ == "__main__":
    asyncio.run(seed_data())

