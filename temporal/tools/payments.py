import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("temporal.tools.payments")


async def execute_message_payments_team(order_id: str, message: str, action_required: str = "review_charge") -> dict[str, Any]:
    """Simulates sending a payment dispute or reconciliation request to finance/payments."""
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(f"[TOOL: message_payments_team] Order: {order_id} | Action: {action_required} | Message: {message}")

    return {
        "tool": "message_payments_team",
        "order_id": order_id,
        "recipient": "payments-reconciliation@sagapilot.internal",
        "action_required": action_required,
        "message": message,
        "ticket_id": f"PAY-REQ-{order_id[-4:]}-88",
        "status": "SENT",
        "timestamp": timestamp,
    }
