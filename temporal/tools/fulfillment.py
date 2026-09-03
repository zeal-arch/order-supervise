import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("temporal.tools.fulfillment")


async def execute_message_fulfillment_team(order_id: str, message: str, priority: str = "normal") -> dict[str, Any]:
    """Simulates sending a priority message/ticket to the warehouse/fulfillment operations team."""
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(f"[TOOL: message_fulfillment_team] Order: {order_id} | Priority: {priority} | Message: {message}")

    return {
        "tool": "message_fulfillment_team",
        "order_id": order_id,
        "recipient": "warehouse-operations@sagapilot.internal",
        "priority": priority,
        "message": message,
        "ticket_id": f"FULFILL-TICK-{order_id[-4:]}-01",
        "status": "SENT",
        "timestamp": timestamp,
    }
