from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SupervisorCreate(BaseModel):
    name: str = Field(..., examples=["E-commerce Tier 1 Supervisor"])
    description: str | None = Field(None, examples=["Handles standard customer orders and proactively manages shipping delays"])
    base_instruction: str = Field(
        ...,
        examples=["You are an autonomous AI Order Supervisor. Monitor order progress, resolve logistics hiccups by contacting logistics or alerting the customer, and maintain a concise memory state."],
    )
    available_tools: list[str] = Field(
        default_factory=lambda: [
            "message_fulfillment_team",
            "message_payments_team",
            "message_logistics_team",
            "message_customer",
            "create_internal_note",
        ]
    )
    default_wake_delay_seconds: int = Field(default=3600, ge=10, le=2592000)
    wake_sensitivity: str = Field(default="balanced")  # "aggressive", "balanced", "conservative"
    model_name: str | None = Field(default="gpt-4o-mini")
    is_active: bool = True


class SupervisorResponse(BaseModel):
    id: str
    name: str
    description: str | None
    base_instruction: str
    available_tools: list[str]
    default_wake_delay_seconds: int
    wake_sensitivity: str
    model_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
