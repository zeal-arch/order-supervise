from datetime import datetime

from pydantic import BaseModel, Field


class InstructionCreate(BaseModel):
    instruction: str = Field(
        ...,
        examples=["For this order, prioritize speed over cost. If shipment is delayed, escalate immediately."],
    )
    author: str | None = Field(default="operations_user")


class InstructionResponse(BaseModel):
    instruction: str
    author: str
    timestamp: datetime
