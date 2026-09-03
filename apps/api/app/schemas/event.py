from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import EventType


class EventCreate(BaseModel):
    event_type: EventType = Field(..., examples=[EventType.SHIPMENT_DELAYED])
    payload: dict[str, Any] = Field(
        default_factory=dict,
        examples=[{"delay_hours": 48, "reason": "Severe weather conditions at regional sorting hub"}],
    )
    source: str = Field(default="simulator", examples=["logistics_carrier"])


class EventResponse(BaseModel):
    id: str
    run_id: str
    event_type: str
    payload: dict[str, Any]
    source: str
    requires_wake: bool | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
