export type RunStatus =
  | "INITIALIZING"
  | "RUNNING"
  | "SLEEPING"
  | "PAUSED"
  | "COMPLETED"
  | "TERMINATED"
  | "FAILED";

export type EventType =
  | "order_created"
  | "payment_confirmed"
  | "payment_failed"
  | "shipment_created"
  | "shipment_delayed"
  | "delivered"
  | "refund_requested"
  | "customer_message_received"
  | "manual_instruction"
  | "custom_event";

export interface Supervisor {
  id: string;
  name: string;
  description?: string;
  base_instruction: string;
  available_tools: string[];
  default_wake_delay_seconds: number;
  wake_sensitivity: "aggressive" | "balanced" | "conservative";
  model_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  sku: string;
  name: string;
  quantity: number;
  unit_price: number;
}

export interface OrderContext {
  order_id: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  shipping_address: string;
  items: OrderItem[];
  total_amount: number;
  currency: string;
}

export interface CompactMemory {
  order_id: string;
  current_status: string;
  customer_name?: string;
  customer_email?: string;
  items_summary?: string;
  total_amount?: number;
  payment_status?: string;
  shipment_status?: string;
  tracking_number?: string;
  courier?: string;
  key_events_summary?: string[];
  actions_taken?: string[];
  pending_concerns?: string[];
  active_instructions?: string[];
  rolling_summary: string;
  last_agent_reasoning?: string;
  last_updated_at?: string;
}

export interface DomainEvent {
  id: string;
  run_id: string;
  event_type: EventType | string;
  payload: Record<string, any>;
  source: string;
  requires_wake?: boolean;
  created_at: string;
}

export interface AgentActivity {
  id: string;
  run_id: string;
  activity_type: string;
  reasoning?: string;
  payload: Record<string, any>;
  result: Record<string, any>;
  status: string;
  created_at: string;
}

export interface Instruction {
  instruction: string;
  author: string;
  timestamp: string;
}

export interface FinalOutput {
  final_summary: string;
  important_actions_taken: string[];
  key_learnings: string[];
  feedback_and_recommendations: string[];
  completed_at: string;
}

export interface Run {
  id: string;
  order_id: string;
  supervisor_id?: string;
  workflow_id: string;
  run_id?: string;
  status: RunStatus;
  order_context: OrderContext;
  current_memory: CompactMemory;
  additional_instructions: Instruction[];
  next_wake_at?: string;
  last_wake_reason?: string;
  started_at: string;
  updated_at: string;
  completed_at?: string;
  final_output?: FinalOutput;
  events?: DomainEvent[];
  activities?: AgentActivity[];
}
