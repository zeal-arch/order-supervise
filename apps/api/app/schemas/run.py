from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.schemas.event import EventResponse
from domain.models import OrderContext


class ActivityResponse(BaseModel):
    id: str
    run_id: str
    activity_type: str
    reasoning: str | None
    payload: dict[str, Any]
    result: dict[str, Any]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RunCreate(BaseModel):
    order_id: str = Field(..., examples=["ORD-9021"])
    supervisor_id: str | None = Field(None, examples=["sup_default_standard"])
    order_context: OrderContext | None = None
    initial_instructions: list[str] | None = Field(default_factory=list)


class RunResponse(BaseModel):
    id: str
    order_id: str
    supervisor_id: str | None
    workflow_id: str
    run_id: str | None
    status: str
    order_context: dict[str, Any]
    current_memory: dict[str, Any]
    additional_instructions: list[dict[str, Any]]
    next_wake_at: datetime | None
    last_wake_reason: str | None
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    final_output: dict[str, Any] | None

    model_config = ConfigDict(from_attributes=True)


class RunDetailResponse(RunResponse):
    events: list[EventResponse] = Field(default_factory=list)
    activities: list[ActivityResponse] = Field(default_factory=list)
