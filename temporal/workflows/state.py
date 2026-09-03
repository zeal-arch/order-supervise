from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowOrderState:
    order_id: str
    run_id: str
    status: str = "INITIALIZING"
    supervisor_config: dict[str, Any] = field(default_factory=dict)
    order_context: dict[str, Any] = field(default_factory=dict)
    current_memory: dict[str, Any] = field(default_factory=dict)

    # Event queues & history
    pending_events: list[dict[str, Any]] = field(default_factory=list)
    processed_events: list[dict[str, Any]] = field(default_factory=list)
    additional_instructions: list[dict[str, Any]] = field(default_factory=list)

    # Scheduling & control
    is_paused: bool = False
    is_terminated: bool = False
    next_wake_at: str | None = None
    last_wake_reason: str = "WORKFLOW_START"

    # Post-mortem output
    final_output: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "run_id": self.run_id,
            "status": self.status,
            "is_paused": self.is_paused,
            "is_terminated": self.is_terminated,
            "next_wake_at": self.next_wake_at,
            "last_wake_reason": self.last_wake_reason,
            "pending_events_count": len(self.pending_events),
            "processed_events_count": len(self.processed_events),
            "instructions_count": len(self.additional_instructions),
            "additional_instructions": self.additional_instructions,
            "current_memory": self.current_memory,
            "final_output": self.final_output,
        }
