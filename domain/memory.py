from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

# Event type → order lifecycle status mapping
_STATUS_FROM_EVENT: dict[str, str] = {
    "order_created": "CREATED",
    "payment_confirmed": "PROCESSING",
    "payment_failed": "PAYMENT_FAILED",
    "shipment_created": "SHIPPED",
    "shipment_delayed": "DELAYED",
    "delivered": "DELIVERED",
    "refund_requested": "REFUNDED",
}


class OrderCompactMemory(BaseModel):
    order_id: str
    current_status: str = "CREATED"
    customer_name: str | None = None
    customer_email: str | None = None
    items_summary: str | None = None
    total_amount: float | None = None
    payment_status: str | None = "pending"
    shipment_status: str | None = "not_shipped"
    tracking_number: str | None = None
    courier: str | None = None

    # Key historical highlights
    key_events_summary: list[str] = Field(default_factory=list)
    actions_taken: list[str] = Field(default_factory=list)
    pending_concerns: list[str] = Field(default_factory=list)
    active_instructions: list[str] = Field(default_factory=list)

    # Rolling natural language synthesis
    rolling_summary: str = "Order workflow initiated."
    last_agent_reasoning: str | None = None

    last_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrderCompactMemory":
        """Tolerant deserialization: silently ignores unknown keys.
        Safe to call even when the raw dict has extra ad-hoc fields added
        by the agent activity.
        """
        known_fields = set(cls.model_fields.keys())
        return cls(**{k: v for k, v in data.items() if k in known_fields})

    def update_from_events(self, events: list[dict[str, Any]]) -> None:
        """Derives status transitions and shipment metadata from a list of domain events.

        Processes events in chronological order so the LAST terminal event wins
        the status update (e.g. payment_failed → PAYMENT_FAILED if it's the latest).
        Also maintains the key_events_summary sliding window.
        """
        for event in events:
            event_type = event.get("event_type", "")
            payload = event.get("payload", {})
            timestamp = str(event.get("timestamp", "recent"))[:16]

            # --- Lifecycle status ---
            new_status = _STATUS_FROM_EVENT.get(event_type)
            if new_status:
                self.current_status = new_status

            # --- Payment sub-status ---
            if event_type == "payment_confirmed":
                self.payment_status = "confirmed"
            elif event_type == "payment_failed":
                self.payment_status = "failed"
            elif event_type == "refund_requested":
                self.payment_status = "refund_pending"

            # --- Shipment sub-status ---
            if event_type == "shipment_created":
                self.shipment_status = "in_transit"
                self.tracking_number = payload.get("tracking_number") or self.tracking_number
                self.courier = payload.get("carrier") or self.courier
            elif event_type == "shipment_delayed":
                self.shipment_status = "delayed"
                self.tracking_number = payload.get("tracking_number") or self.tracking_number
                self.courier = payload.get("carrier") or self.courier
            elif event_type == "delivered":
                self.shipment_status = "delivered"
            elif event_type == "customer_not_home":
                self.shipment_status = "delivery_attempted"

            # --- Key events timeline (deduplicated) ---
            evt_str = f"[{event_type}] at {timestamp}"
            if evt_str not in self.key_events_summary:
                self.key_events_summary.append(evt_str)

        # Maintain sliding window (max 10 recent key events)
        if len(self.key_events_summary) > 10:
            self.key_events_summary = self.key_events_summary[-10:]

    def merge_actions(self, new_actions: list[dict[str, Any]]) -> None:
        """Appends unique action summaries from a list of agent-executed tool results."""
        for act in new_actions:
            summary = f"{act.get('tool')}: {act.get('summary', 'executed')}"
            if summary not in self.actions_taken:
                self.actions_taken.append(summary)

    def build_rolling_summary(self, reasoning: str = "") -> str:
        """Synthesizes a self-contained natural language summary of current order state."""
        parts = [f"Order {self.order_id}"]
        if self.customer_name:
            parts[0] += f" for {self.customer_name}"
        parts.append(f"Status: {self.current_status}.")
        if self.payment_status:
            parts.append(f"Payment: {self.payment_status}.")
        if self.shipment_status:
            parts.append(f"Shipment: {self.shipment_status}.")
        if self.tracking_number:
            parts.append(f"Tracking: {self.tracking_number}.")
        parts.append(f"Total actions taken: {len(self.actions_taken)}.")
        if reasoning:
            parts.append(reasoning[:200])
        return " ".join(parts)
