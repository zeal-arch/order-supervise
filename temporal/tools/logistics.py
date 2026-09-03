import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("temporal.tools.logistics")


async def execute_message_logistics_team(
    order_id: str,
    carrier: str,
    tracking_number: str,
    issue_description: str,
    urgency: str = "high",
) -> dict[str, Any]:
    """Simulates raising an expedited inquiry with third-party logistics/couriers (e.g. DHL, FedEx, UPS)."""
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(
        f"[TOOL: message_logistics_team] Order: {order_id} | Carrier: {carrier} | Tracking: {tracking_number} | Issue: {issue_description}"
    )

    return {
        "tool": "message_logistics_team",
        "order_id": order_id,
        "carrier": carrier or "FedEx Logistics",
        "tracking_number": tracking_number or "TRK-98127391",
        "urgency": urgency,
        "issue_description": issue_description,
        "carrier_case_number": f"CASE-LOG-{order_id[-4:]}-77",
        "status": "DISPATCHED",
        "timestamp": timestamp,
    }
