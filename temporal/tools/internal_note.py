import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("temporal.tools.internal_note")


async def execute_create_internal_note(
    order_id: str,
    note: str,
    category: str = "general",
    flag_for_human: bool = False,
) -> dict[str, Any]:
    """Simulates creating an internal operational note on the order record."""
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(f"📝 [TOOL: create_internal_note] Order: {order_id} | Category: {category} | Flag: {flag_for_human} | Note: {note}")

    return {
        "tool": "create_internal_note",
        "order_id": order_id,
        "category": category,
        "note": note,
        "flag_for_human": flag_for_human,
        "note_id": f"NOTE-{order_id[-4:]}-{int(datetime.now(timezone.utc).timestamp())}",
        "timestamp": timestamp,
    }
