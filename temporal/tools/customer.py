import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("temporal.tools.customer")


async def execute_message_customer(
    order_id: str,
    customer_email: str,
    subject: str,
    body: str,
    channel: str = "email",
) -> dict[str, Any]:
    """Simulates sending a proactive update or notification to the customer."""
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(
        f"✉️ [TOOL: message_customer] Order: {order_id} | To: {customer_email} | Subject: {subject} | Body: {body}"
    )

    return {
        "tool": "message_customer",
        "order_id": order_id,
        "recipient": customer_email,
        "channel": channel,
        "subject": subject,
        "body": body,
        "delivery_status": "DELIVERED",
        "timestamp": timestamp,
    }
