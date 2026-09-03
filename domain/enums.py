from enum import Enum


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELAYED = "DELAYED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    UNDER_REVIEW = "UNDER_REVIEW"


class RunStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    SLEEPING = "SLEEPING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    FAILED = "FAILED"


class EventType(str, Enum):
    ORDER_CREATED = "order_created"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PAYMENT_FAILED = "payment_failed"
    SHIPMENT_CREATED = "shipment_created"
    SHIPMENT_DELAYED = "shipment_delayed"
    DELIVERY_ATTEMPT_FAILED = "delivery_attempt_failed"
    CUSTOMER_NOT_HOME = "customer_not_home"
    DELIVERED = "delivered"
    REFUND_REQUESTED = "refund_requested"
    CUSTOMER_MESSAGE_RECEIVED = "customer_message_received"
    NO_UPDATE_FOR_N_HOURS = "no_update_for_n_hours"
    MANUAL_INSTRUCTION = "manual_instruction"
    CUSTOM_EVENT = "custom_event"

