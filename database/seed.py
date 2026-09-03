import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import asyncio
import logging
from datetime import datetime, timedelta, timezone

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

DEMO_ORDERS = [
    {
        "id": "run_demo_1001",
        "order_id": "ORD-1001",
        "supervisor_id": "sup_vip_expedited",
        "workflow_id": "order-supervisor-ORD-1001",
        "status": "SLEEPING",
        "customer_name": "Sarah Connor",
        "customer_email": "sarah@cyberdyne.io",
        "total_amount": 499.00,
        "item_title": "Ergonomic Split Mechanical Keyboard",
        "item_sku": "SKU-ERG-KEY",
        "summary": "VIP order initialized. Payment confirmed and warehouse dispatched. Dormant in scheduled sleep awaiting carrier tracking update.",
        "instructions": [{"instruction": "For this order, prioritize speed over cost.", "added_at": "2026-09-03T10:00:00Z"}],
        "last_wake_reason": "EVENT_SIGNAL",
        "events": [
            {"type": "order_created", "payload": {"amount": 499.00, "customer": "Sarah Connor"}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998811", "amount": 499.00}, "source": "stripe"},
        ],
        "activities": [
            {
                "reasoning": "Payment verified ($499.00). Applied operator directive 'prioritize speed over cost'. Dispatched rush packing alert to warehouse.",
                "tools": [
                    {"tool": "message_fulfillment_team", "summary": "Notified warehouse team [RUSH PRIORITY]"},
                    {"tool": "message_customer", "summary": "Sent payment confirmation receipt"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1002",
        "order_id": "ORD-1002",
        "supervisor_id": "sup_vip_expedited",
        "workflow_id": "order-supervisor-ORD-1002",
        "status": "SLEEPING",
        "customer_name": "Marcus Vance",
        "customer_email": "marcus.vance@techcorp.com",
        "total_amount": 1199.00,
        "item_title": "Ultrawide 49-inch Curved OLED Monitor",
        "item_sku": "SKU-MON-49",
        "summary": "Order dispatched via FedEx Priority Overnight (FX-99881122). Sleeping until next carrier waypoint check.",
        "instructions": [{"instruction": "Ensure white-glove courier delivery.", "added_at": "2026-09-03T09:15:00Z"}],
        "last_wake_reason": "EVENT_SIGNAL",
        "events": [
            {"type": "order_created", "payload": {"amount": 1199.00}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998812"}, "source": "stripe"},
            {"type": "shipment_created", "payload": {"carrier": "FedEx", "tracking_number": "FX-99881122"}, "source": "warehouse"},
        ],
        "activities": [
            {
                "reasoning": "Shipment handed over to FedEx. Dispatched tracking portal link to buyer.",
                "tools": [
                    {"tool": "message_customer", "summary": "Dispatched shipping confirmation and tracking link"},
                    {"tool": "create_internal_note", "summary": "Logged tracking number FX-99881122"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1003",
        "order_id": "ORD-1003",
        "supervisor_id": "sup_standard_retail",
        "workflow_id": "order-supervisor-ORD-1003",
        "status": "SLEEPING",
        "customer_name": "Elena Rostova",
        "customer_email": "elena.rostova@designlab.net",
        "total_amount": 349.50,
        "item_title": "Studio Wireless Active Noise Cancelling Headphones",
        "item_sku": "SKU-AUD-ANC",
        "summary": "Carrier delay alert received (48h winter blizzard). Proactive email sent to customer and carrier escalation ticket opened.",
        "instructions": [{"instruction": "If shipment is delayed, notify customer immediately.", "added_at": "2026-09-03T08:00:00Z"}],
        "last_wake_reason": "EVENT_SIGNAL",
        "events": [
            {"type": "order_created", "payload": {"amount": 349.50}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998813"}, "source": "stripe"},
            {"type": "shipment_created", "payload": {"carrier": "FedEx", "tracking_number": "FX-77665511"}, "source": "warehouse"},
            {"type": "shipment_delayed", "payload": {"carrier": "FedEx", "delay_hours": 48, "reason": "Severe blizzard"}, "source": "fedex_webhook"},
        ],
        "activities": [
            {
                "reasoning": "Blizzard delay at Chicago hub. Dispatched polite delay notice to customer and opened FedEx inquiry.",
                "tools": [
                    {"tool": "message_logistics_team", "summary": "Opened carrier escalation ticket with FedEx"},
                    {"tool": "message_customer", "summary": "Sent weather delay notification and revised ETA"},
                    {"tool": "create_internal_note", "summary": "Flagged order for 24h follow-up"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1004",
        "order_id": "ORD-1004",
        "supervisor_id": "sup_standard_retail",
        "workflow_id": "order-supervisor-ORD-1004",
        "status": "SLEEPING",
        "customer_name": "David Kim",
        "customer_email": "dkim@startup.io",
        "total_amount": 129.00,
        "item_title": "Custom Double-Shot PBT Keycap Set",
        "item_sku": "SKU-KEY-PBT",
        "summary": "Customer inquiry received regarding tracking status. Automated response sent with current courier ETA.",
        "instructions": [],
        "last_wake_reason": "EVENT_SIGNAL",
        "events": [
            {"type": "order_created", "payload": {"amount": 129.00}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998814"}, "source": "stripe"},
            {"type": "shipment_created", "payload": {"carrier": "DHL Express", "tracking_number": "DHL-442211"}, "source": "warehouse"},
            {"type": "customer_message_received", "payload": {"message": "When is my order expected to arrive?"}, "source": "customer_inbound"},
        ],
        "activities": [
            {
                "reasoning": "Customer inquired about delivery timeline. Generated status reply referencing DHL tracking DHL-442211.",
                "tools": [
                    {"tool": "message_customer", "summary": "Answered customer tracking inquiry with estimated Friday delivery"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1005",
        "order_id": "ORD-1005",
        "supervisor_id": "sup_standard_retail",
        "workflow_id": "order-supervisor-ORD-1005",
        "status": "SLEEPING",
        "customer_name": "Amara Okafor",
        "customer_email": "amara.okafor@biotech.org",
        "total_amount": 299.00,
        "item_title": "Titanium Biometric Smart Health Ring (Size 9)",
        "item_sku": "SKU-RNG-09",
        "summary": "1st delivery attempt failed (customer not home). Requested 24h hold at local FedEx depot and sent rescheduling link.",
        "instructions": [],
        "last_wake_reason": "EVENT_SIGNAL",
        "events": [
            {"type": "order_created", "payload": {"amount": 299.00}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998815"}, "source": "stripe"},
            {"type": "shipment_created", "payload": {"carrier": "FedEx", "tracking_number": "FX-332211"}, "source": "warehouse"},
            {"type": "delivery_attempt_failed", "payload": {"reason": "Customer not available", "carrier": "FedEx"}, "source": "fedex_webhook"},
        ],
        "activities": [
            {
                "reasoning": "Delivery attempt 1 unsuccessful. Promptly alerted customer with 3 delivery reschedule slots.",
                "tools": [
                    {"tool": "message_customer", "summary": "Sent delivery rescheduling options and local depot pickup address"},
                    {"tool": "message_logistics_team", "summary": "Requested 24-hour depot hold"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1006",
        "order_id": "ORD-1006",
        "supervisor_id": "sup_fraud_returns",
        "workflow_id": "order-supervisor-ORD-1006",
        "status": "SLEEPING",
        "customer_name": "Lucas Silva",
        "customer_email": "lucas.silva@musicworks.br",
        "total_amount": 189.97,
        "item_title": "Hi-Res USB-C Audio DAC & Amplifier",
        "item_sku": "SKU-AUD-DAC",
        "summary": "Refund requested by customer. Fulfillment halted and forwarded to payments review queue.",
        "instructions": [{"instruction": "Hold fulfillment and verify refund authorization.", "added_at": "2026-09-03T07:30:00Z"}],
        "last_wake_reason": "EVENT_SIGNAL",
        "events": [
            {"type": "order_created", "payload": {"amount": 189.97}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998816"}, "source": "stripe"},
            {"type": "refund_requested", "payload": {"reason": "Customer ordered incorrect model"}, "source": "customer_portal"},
        ],
        "activities": [
            {
                "reasoning": "Customer initiated cancellation before warehouse dispatch. Forwarded to payments team for refund processing.",
                "tools": [
                    {"tool": "message_payments_team", "summary": "Initiated refund review ticket for $189.97"},
                    {"tool": "message_customer", "summary": "Sent refund confirmation and instructions"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1007",
        "order_id": "ORD-1007",
        "supervisor_id": "sup_standard_retail",
        "workflow_id": "order-supervisor-ORD-1007",
        "status": "COMPLETED",
        "customer_name": "Chloe Bennett",
        "customer_email": "chloe.b@creativehub.co",
        "total_amount": 89.99,
        "item_title": "Wireless Ergonomic Vertical Mouse",
        "item_sku": "SKU-MOU-VRT",
        "summary": "Order delivered to Front Porch. Workflow completed cleanly with terminal AI post-mortem report.",
        "instructions": [],
        "last_wake_reason": "EVENT_SIGNAL",
        "final_output": {
            "final_summary": "Order ORD-1007 successfully completed with on-time delivery.",
            "important_actions_taken": [
                "Captured payment authorization",
                "Dispatched standard shipping label",
                "Sent delivery confirmation notice",
            ],
            "key_learnings": [
                "Seamless fulfillment completed within 28 hours.",
                "Zero customer support touches required.",
            ],
            "feedback_and_recommendations": [
                "Standard retail workflow operated with 100% autonomous accuracy.",
            ],
            "completed_at": "2026-09-03T12:30:00Z",
        },
        "events": [
            {"type": "order_created", "payload": {"amount": 89.99}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998817"}, "source": "stripe"},
            {"type": "shipment_created", "payload": {"carrier": "USPS", "tracking_number": "940011189922"}, "source": "warehouse"},
            {"type": "delivered", "payload": {"signature": "C. Bennett", "location": "Front Porch"}, "source": "usps_webhook"},
        ],
        "activities": [
            {
                "reasoning": "USPS confirmed package delivery. Emitted delivery receipt and generated terminal summary.",
                "tools": [
                    {"tool": "message_customer", "summary": "Sent delivery confirmation email and feedback survey"},
                    {"tool": "create_internal_note", "summary": "Order lifecycle concluded successfully"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1008",
        "order_id": "ORD-1008",
        "supervisor_id": "sup_vip_expedited",
        "workflow_id": "order-supervisor-ORD-1008",
        "status": "COMPLETED",
        "customer_name": "Liam Gallagher",
        "customer_email": "liam.g@oasisrecords.co.uk",
        "total_amount": 799.00,
        "item_title": "4K 144Hz Professional Color-Calibrated Creator Display",
        "item_sku": "SKU-DSP-4K",
        "summary": "VIP order delivered with recipient signature. Zero bottlenecks encountered.",
        "instructions": [{"instruction": "High-priority VIP client. Monitor shipping continuously.", "added_at": "2026-09-03T06:00:00Z"}],
        "last_wake_reason": "EVENT_SIGNAL",
        "final_output": {
            "final_summary": "VIP Order ORD-1008 fulfilled and delivered with signature confirmation.",
            "important_actions_taken": [
                "Dispatched priority fulfillment packing",
                "Monitored hourly carrier telemetry",
                "Confirmed signature delivery with client",
            ],
            "key_learnings": [
                "White-glove SLA achieved under 24 hours.",
            ],
            "feedback_and_recommendations": [
                "VIP courier protocol executed flawlessly.",
            ],
            "completed_at": "2026-09-03T11:45:00Z",
        },
        "events": [
            {"type": "order_created", "payload": {"amount": 799.00}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998818"}, "source": "stripe"},
            {"type": "shipment_created", "payload": {"carrier": "FedEx", "tracking_number": "FX-88990011"}, "source": "warehouse"},
            {"type": "delivered", "payload": {"signature": "Liam Gallagher", "location": "Reception"}, "source": "fedex_webhook"},
        ],
        "activities": [
            {
                "reasoning": "VIP parcel delivered safely to Liam Gallagher with direct signature.",
                "tools": [
                    {"tool": "message_customer", "summary": "Sent VIP delivery confirmation and support contact"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1009",
        "order_id": "ORD-1009",
        "supervisor_id": "sup_fraud_returns",
        "workflow_id": "order-supervisor-ORD-1009",
        "status": "TERMINATED",
        "customer_name": "Sophia Martinez",
        "customer_email": "sophia.m@archstudio.es",
        "total_amount": 119.00,
        "item_title": "Carbon Fiber Adjustable Laptop Riser",
        "item_sku": "SKU-ACC-RISER",
        "summary": "Order cancelled prior to shipment upon customer request. Full refund issued.",
        "instructions": [],
        "last_wake_reason": "EVENT_SIGNAL",
        "final_output": {
            "final_summary": "Order ORD-1009 terminated following customer cancellation request.",
            "important_actions_taken": [
                "Halted warehouse packing",
                "Processed payment refund of $119.00",
                "Sent cancellation receipt",
            ],
            "key_learnings": [
                "Cancellation handled in under 2 minutes, preventing unnecessary courier fees.",
            ],
            "feedback_and_recommendations": [
                "Inventory immediately restocked to available catalog.",
            ],
            "completed_at": "2026-09-03T08:15:00Z",
        },
        "events": [
            {"type": "order_created", "payload": {"amount": 119.00}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998819"}, "source": "stripe"},
            {"type": "refund_requested", "payload": {"reason": "Customer cancelled order"}, "source": "customer_portal"},
        ],
        "activities": [
            {
                "reasoning": "Processed immediate cancellation and issued refund to original payment method.",
                "tools": [
                    {"tool": "message_payments_team", "summary": "Processed $119.00 refund via Stripe"},
                    {"tool": "message_customer", "summary": "Sent cancellation and refund confirmation"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1010",
        "order_id": "ORD-1010",
        "supervisor_id": "sup_standard_retail",
        "workflow_id": "order-supervisor-ORD-1010",
        "status": "SLEEPING",
        "customer_name": "Noah Jensen",
        "customer_email": "noah.jensen@nordicsoft.dk",
        "total_amount": 249.00,
        "item_title": "Thunderbolt 4 Quad-Display Docking Station",
        "item_sku": "SKU-DOCK-TB4",
        "summary": "Payment verified. Warehouse currently packing parcel. Scheduled wake timer set for tracking registration.",
        "instructions": [],
        "last_wake_reason": "EVENT_SIGNAL",
        "events": [
            {"type": "order_created", "payload": {"amount": 249.00}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998820"}, "source": "stripe"},
        ],
        "activities": [
            {
                "reasoning": "Payment captured. Dispatched order packing ticket to central warehouse depot.",
                "tools": [
                    {"tool": "message_fulfillment_team", "summary": "Issued packing ticket #DOCK-9920"},
                    {"tool": "message_customer", "summary": "Sent order receipt and preparation update"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1011",
        "order_id": "ORD-1011",
        "supervisor_id": "sup_standard_retail",
        "workflow_id": "order-supervisor-ORD-1011",
        "status": "SLEEPING",
        "customer_name": "Zoe Chen",
        "customer_email": "zoe.chen@gamestudio.cn",
        "total_amount": 68.50,
        "item_title": "Hydrophobic Extended Desk Mat & Gel Wrist Rest",
        "item_sku": "SKU-ACC-MAT",
        "summary": "Order placed. Awaiting initial payment confirmation signal from billing gateway.",
        "instructions": [],
        "last_wake_reason": "WORKFLOW_START",
        "events": [
            {"type": "order_created", "payload": {"amount": 68.50}, "source": "checkout"},
        ],
        "activities": [
            {
                "reasoning": "Workflow initiated on checkout submission. Set 15-minute watchdog timer for payment confirmation.",
                "tools": [
                    {"tool": "create_internal_note", "summary": "Watchdog timer armed for payment authorization"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1012",
        "order_id": "ORD-1012",
        "supervisor_id": "sup_vip_expedited",
        "workflow_id": "order-supervisor-ORD-1012",
        "status": "PAUSED",
        "customer_name": "James Wilson",
        "customer_email": "jwilson@deepcompute.ai",
        "total_amount": 1450.00,
        "item_title": "Enterprise Dual GPU External Compute Enclosure",
        "item_sku": "SKU-SRV-GPU",
        "summary": "Paused by operator for manual address verification and export compliance review.",
        "instructions": [{"instruction": "Hold dispatch until enterprise compliance verifies VAT ID.", "added_at": "2026-09-03T09:00:00Z"}],
        "last_wake_reason": "MANUAL_INSTRUCTION",
        "events": [
            {"type": "order_created", "payload": {"amount": 1450.00}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998822"}, "source": "stripe"},
        ],
        "activities": [
            {
                "reasoning": "High-value enterprise order flagged for VAT compliance. Workflow safely paused.",
                "tools": [
                    {"tool": "create_internal_note", "summary": "Compliance review initiated by operator"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1013",
        "order_id": "ORD-1013",
        "supervisor_id": "sup_vip_expedited",
        "workflow_id": "order-supervisor-ORD-1013",
        "status": "COMPLETED",
        "customer_name": "Maya Patel",
        "customer_email": "maya.patel@healthtech.org",
        "total_amount": 580.00,
        "item_title": "Ergonomic Lumbar Executive Task Chair",
        "item_sku": "SKU-CHR-EXEC",
        "summary": "Delivered successfully with zero issues. Autonomous supervisor concluded workflow.",
        "instructions": [],
        "last_wake_reason": "EVENT_SIGNAL",
        "final_output": {
            "final_summary": "Order ORD-1013 completed on schedule.",
            "important_actions_taken": [
                "Coordinated freight dispatch",
                "Provided delivery tracking to customer",
            ],
            "key_learnings": [
                "Freight courier delivery completed within target window.",
            ],
            "feedback_and_recommendations": [
                "Recommended carrier for future heavy-freight items.",
            ],
            "completed_at": "2026-09-03T10:15:00Z",
        },
        "events": [
            {"type": "order_created", "payload": {"amount": 580.00}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998823"}, "source": "stripe"},
            {"type": "shipment_created", "payload": {"carrier": "FedEx Freight", "tracking_number": "FX-55443322"}, "source": "warehouse"},
            {"type": "delivered", "payload": {"signature": "Maya Patel", "location": "Front Door"}, "source": "fedex_webhook"},
        ],
        "activities": [
            {
                "reasoning": "Freight courier confirmed successful delivery.",
                "tools": [
                    {"tool": "message_customer", "summary": "Sent delivery notification and assembly instructions"},
                ],
            }
        ],
    },
    {
        "id": "run_demo_1014",
        "order_id": "ORD-1014",
        "supervisor_id": "sup_standard_retail",
        "workflow_id": "order-supervisor-ORD-1014",
        "status": "SLEEPING",
        "customer_name": "Oliver Wright",
        "customer_email": "oliver.w@soundstage.uk",
        "total_amount": 54.00,
        "item_title": "Acoustic Studio Monitor Isolation Pads (Pair)",
        "item_sku": "SKU-AUD-PADS",
        "summary": "No courier tracking updates for 24h. Raised automated status inquiry ticket with logistics carrier.",
        "instructions": [],
        "last_wake_reason": "EVENT_SIGNAL",
        "events": [
            {"type": "order_created", "payload": {"amount": 54.00}, "source": "checkout"},
            {"type": "payment_confirmed", "payload": {"transaction_id": "tx_998824"}, "source": "stripe"},
            {"type": "shipment_created", "payload": {"carrier": "Royal Mail", "tracking_number": "RM-99112233"}, "source": "warehouse"},
            {"type": "no_update_for_n_hours", "payload": {"hours": 24, "last_location": "Heathrow Sorting Facility"}, "source": "telemetry"},
        ],
        "activities": [
            {
                "reasoning": "Tracking has been silent for 24h at Heathrow hub. Triggered proactive carrier ping.",
                "tools": [
                    {"tool": "message_logistics_team", "summary": "Inquired with Royal Mail regarding tracking status"},
                    {"tool": "create_internal_note", "summary": "Tracer opened on RM-99112233"},
                ],
            }
        ],
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

        logger.info(f"Seeding {len(DEMO_ORDERS)} demo orders...")
        base_time = datetime.now(timezone.utc) - timedelta(hours=6)

        for idx, order_data in enumerate(DEMO_ORDERS):
            existing_run = await db.execute(select(RunModel).where(RunModel.id == order_data["id"]))
            if not existing_run.scalar_one_or_none():
                order_time = base_time + timedelta(minutes=idx * 25)
                demo_run = RunModel(
                    id=order_data["id"],
                    order_id=order_data["order_id"],
                    supervisor_id=order_data["supervisor_id"],
                    workflow_id=order_data["workflow_id"],
                    status=order_data["status"],
                    order_context={
                        "order_id": order_data["order_id"],
                        "customer_name": order_data["customer_name"],
                        "customer_email": order_data["customer_email"],
                        "total_amount": order_data["total_amount"],
                        "currency": "USD",
                        "items": [
                            {
                                "sku": order_data["item_sku"],
                                "title": order_data["item_title"],
                                "quantity": 1,
                                "price": order_data["total_amount"],
                            }
                        ],
                    },
                    current_memory={
                        "current_status": order_data["status"],
                        "summary": order_data["summary"],
                        "actions_taken": [a["summary"] for act in order_data.get("activities", []) for a in act.get("tools", [])],
                    },
                    additional_instructions=order_data.get("instructions", []),
                    last_wake_reason=order_data.get("last_wake_reason", "WORKFLOW_START"),
                    final_output=order_data.get("final_output"),
                    started_at=order_time,
                    updated_at=order_time + timedelta(minutes=15),
                )
                db.add(demo_run)

                # Seed Timeline Events
                for e_idx, evt in enumerate(order_data.get("events", [])):
                    evt_time = order_time + timedelta(minutes=e_idx * 5)
                    db.add(
                        EventModel(
                            id=f"evt_{order_data['id']}_{e_idx+1}",
                            run_id=order_data["id"],
                            event_type=evt["type"],
                            payload=evt["payload"],
                            source=evt.get("source", "simulator"),
                            requires_wake=True,
                            created_at=evt_time,
                        )
                    )

                # Seed Agent Activity History
                for a_idx, act in enumerate(order_data.get("activities", [])):
                    act_time = order_time + timedelta(minutes=a_idx * 7)
                    db.add(
                        ActivityModel(
                            id=f"act_{order_data['id']}_{a_idx+1}",
                            run_id=order_data["id"],
                            activity_type="execute_agent_step_activity",
                            reasoning=act["reasoning"],
                            payload={"wake_reason": order_data.get("last_wake_reason")},
                            result={"actions_executed": act["tools"]},
                            status="SUCCESS",
                            created_at=act_time,
                        )
                    )

                logger.info(f"Added demo order: {order_data['order_id']} ({order_data['customer_name']}) - Status: {order_data['status']}")

        await db.commit()
        logger.info(f"Database successfully populated with supervisor templates and {len(DEMO_ORDERS)} realistic demo orders.")


if __name__ == "__main__":
    asyncio.run(seed_data())
