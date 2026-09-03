from datetime import datetime, timezone

from pydantic import BaseModel, Field

from domain.enums import OrderStatus


class OrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price: float


class OrderContext(BaseModel):
    order_id: str
    customer_name: str
    customer_email: str
    customer_phone: str | None = None
    shipping_address: str
    items: list[OrderItem] = Field(default_factory=list)
    total_amount: float
    currency: str = "USD"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: OrderStatus = OrderStatus.CREATED
