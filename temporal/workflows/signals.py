from dataclasses import dataclass, field
from typing import Any


@dataclass
class OrderEventSignalPayload:
    event_type: str = ""
    event_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "simulator"
    timestamp: str | None = None


@dataclass
class InstructionSignalPayload:
    instruction: str = ""
    author: str = "operator"
    timestamp: str | None = None


@dataclass
class ControlSignalPayload:
    action: str = ""  # "pause", "resume", "terminate"
    reason: str | None = None
