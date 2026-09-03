from temporal.tools.customer import execute_message_customer
from temporal.tools.fulfillment import execute_message_fulfillment_team
from temporal.tools.internal_note import execute_create_internal_note
from temporal.tools.logistics import execute_message_logistics_team
from temporal.tools.payments import execute_message_payments_team

AVAILABLE_TOOLS = {
    "message_fulfillment_team": execute_message_fulfillment_team,
    "message_payments_team": execute_message_payments_team,
    "message_logistics_team": execute_message_logistics_team,
    "message_customer": execute_message_customer,
    "create_internal_note": execute_create_internal_note,
}

__all__ = [
    "AVAILABLE_TOOLS",
    "execute_create_internal_note",
    "execute_message_customer",
    "execute_message_fulfillment_team",
    "execute_message_logistics_team",
    "execute_message_payments_team",
]
