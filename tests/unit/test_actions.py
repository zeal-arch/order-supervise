import pytest

from temporal.tools import (
    execute_create_internal_note,
    execute_message_customer,
    execute_message_fulfillment_team,
    execute_message_logistics_team,
    execute_message_payments_team,
)


@pytest.mark.asyncio
async def test_business_actions_simulation():
    order_id = "ORD-TEST-100"

    # 1. Fulfillment
    res_ful = await execute_message_fulfillment_team(order_id=order_id, message="Pack immediately")
    assert res_ful["status"] == "SENT"
    assert "ticket_id" in res_ful

    # 2. Payments
    res_pay = await execute_message_payments_team(order_id=order_id, message="Check decline code")
    assert res_pay["status"] == "SENT"

    # 3. Logistics
    res_log = await execute_message_logistics_team(
        order_id=order_id, carrier="FedEx", tracking_number="12345", issue_description="Delayed"
    )
    assert res_log["status"] == "DISPATCHED"

    # 4. Customer
    res_cust = await execute_message_customer(
        order_id=order_id, customer_email="user@test.com", subject="Update", body="Your order is delayed"
    )
    assert res_cust["delivery_status"] == "DELIVERED"

    # 5. Internal note
    res_note = await execute_create_internal_note(order_id=order_id, note="Supervisor audit complete")
    assert "note_id" in res_note
